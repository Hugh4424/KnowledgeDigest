# 任务清单：task9 发布安全与查询集验收（K3）

- **Input**：`specs/task9-release-safety-query-acceptance/decision-log.md`（approved，hash `d404ec90…`）、`spec.md`（frozen，`1dd9fad1…`）、`plan.md`（本文件姊妹篇，`3e1da804…`）
- **Template version**：`plan-task.v4`
- **build-code 开工 gate**：无外部未决依赖；K1/K2 产物由 fixture 固化（真 89 份全链路归 verify-code，spec §12 RISK-K3-4 + clarify C5）。build-code 可开工。
- **RED/GREEN 纪律**：每对同一 gate_cmd 与 oracle identity；RED expected_exit 非零先行提交，GREEN 修到 exit 0。
- **权威执行命令**：`uv run --frozen pytest -q` 包住 gate_cmd；执行事实（status/changed files/commands/evidence）逐卡回填下方执行状态填写区——该区是唯一完成权威。

## 材料导航

| 章节 / 材料锚点 | 职责与摘要 | M/S/B/P 读取时机 |
| --- | --- | --- |
| `decision-log.md#已选方向` | 已确认方向/范围/非目标 | S：判类与 review 时读 |
| `spec.md#5. 功能需求` | 29 条 FR 精确契约 | M：写卡与实现时读 |
| `spec.md#11. 验收标准` | AC oracle 定义 | M：写 oracle 时读；B：回归时读 |
| `plan.md#Solution Design` | 两模块职责与数据布局 | M：实现对应块时读 |
| `plan.md#File Boundary` | NEW/MODIFY/DO NOT TOUCH | S：build-code 首卡前读 |
| `plan.md#Technical Decisions` | DEC-K3-001…008 | M：实现细节分叉时读 |
| `tasks.md#Phase P1…P6` | 21 对 RED/GREEN + 聚合卡 | M：逐卡执行时读写 |

## test-routing 判类（test-routing-advisor 输出合同）

```json
{
  "routing_tier": "feature",
  "routing_rationale": "Python 模块级单功能域行为变化（发布通道 kb_publish.py + 验收判定器 kb_accept.py），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/基础设施/并发/数据库变更。changed_files=2 生产模块+3 测试/fixture 文件+pyproject 三行；phase_count=6 同功能域不升级。",
  "result": "pass",
  "ts": "2026-09-15T00:00:00Z"
}
```

## Phase P1 — 基础与输入把关

### Goal

tree hash/锁/sidecar 布局/白名单读取/fixture 可用；发布通道的每个后续卡都建立在这层纯函数上。

### Files

- **NEW**：`src/knowledge_digest/kb_publish.py`（骨架+纯函数层）、`tests/fixtures/task9_publish/__init__.py`
- **MODIFY**：`pyproject.toml`（三脚本入口，T001G 一次改完）
- **DO NOT TOUCH**：digest 三 CLI、semantic_*、full_release.py、publisher.py、lock.py、kb_structure.py（仅 import）

### Tasks

#### T001R — RED：三 CLI 入口接线

- **ID**：T001R；**Phase**：P1；**design_state**：ready
- **versioned_refs**：spec `1dd9fad1…`（FR-CLI-001）+ plan `3e1da804…`（DEC-K3-001）
- **source_refs**：D-002/D-003/D-007·grill G-2
- **依赖**：无；**并行**：可
- **FR**：FR-CLI-001；**AC**：—（工程卡）
- **动作**：只写失败测试：三脚本入口存在（pyproject 已注册为前提，T001G 先 `uv sync` 安装 console scripts）、`--help` 可执行、main(argv) 返回退出码语义；不改 pyproject 与生产代码。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_cli_entries_exist`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_cli_entries_exist`

#### T001G — GREEN：三 CLI 入口接线

- **ID**：T001G；**动作**：先 `uv sync` 再改 pyproject +3 脚本行；`kb_publish.py`/`kb_accept.py` 提供 `main(argv)` 薄壳（参数解析→入口→JSON 打印→退出码）。
- **gate_cmd**：同 T001R；**oracle identity**：同对卡 RED 断言转绿

#### T002R — RED：tree hash 纯函数

- **ID**：T002R；**versioned_refs**：spec `1dd9fad1…`（FR-PUB-008）+ plan（DEC-K3-004）
- **source_refs**：红队 F7·PFACT-K3-007；**FR**：FR-PUB-008；**AC**：AC-K3-1/AC-K3-3
- **依赖**：无；**动作**：写失败测试：固定文件集的树 hash 与手算期望值一致；字典序/逐文件 sha256/拼接式三例；软链/缺失文件报错。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_tree_hash_frozen_algorithm`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_tree_hash_frozen_algorithm`

#### T002G — GREEN：tree hash 纯函数

- **ID**：T002G；**动作**：`kb_publish.py` 实现 `kb_tree_hash(root)`（posix 相对路径 UTF-8 字典序；逐文件 sha256；`path:hash\n` 拼接；整体 sha256；软链→ValidationError）。
- **gate_cmd**：同 T002R；**oracle identity**：同对卡 RED 断言转绿
- **oracle identity**：三例期望值逐字节一致。

#### T003R — RED：批次白名单读取

- **ID**：T003R；**versioned_refs**：spec（FR-PUB-001）+ plan（Code Anchors #1）
- **source_refs**：D-011·蓝队 M6·OI-12；**FR**：FR-PUB-001；**AC**：AC-K3-1
- **依赖**：无；**动作**：写失败测试：四字段全绿放行；run_status=blocked / publish_status 缺失 / navigation 缺字段或≠generated_ok / blockers 非空——各 blocked 且 reason 指名缺项；显式等于语义（"不等于 blocked"写法测试缺失字段必须红）。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_manifest_whitelist`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_manifest_whitelist`

#### T003G — GREEN：批次白名单读取

- **ID**：T003G；**动作**：`kb_publish.py` 实现 `load_batch_manifest(batch_dir)`（json 读入+四字段显式判定+结构化 blocked 结果）。
- **gate_cmd**：同 T003R；**oracle identity**：同对卡 RED 断言转绿
- **oracle identity**：每种输入的唯一（放行|blocked+reason）对。

#### T004R — RED：sidecar 布局与锁

- **ID**：T004R；**versioned_refs**：spec（FR-PUB-004/005）+ plan（DEC-K3-005）
- **source_refs**：detail D3·取证 #4；**FR**：FR-PUB-004/005；**AC**：AC-K3-1
- **依赖**：无；**动作**：写失败测试：sidecar 目录树按冻结布局创建；父目录锁获取/争用抛错；version_id 格式与当日序号扫描。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_sidecar_layout_and_lock`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_sidecar_layout_and_lock`

#### T004G — GREEN：sidecar 布局与锁

- **ID**：T004G；**动作**：`sidecar_path(kb_dir)`、父目录 `kb_lock` 封装、`new_version_id(sidecar)`（UTC+当日序号）。
- **gate_cmd**：同 T004R；**oracle identity**：同对卡 RED 断言转绿

## Phase P2 — 发布通道

### Goal

合法批次→安全合并→原子换版→no-op/碰撞/收据/回滚全路径；blocked 类零字节变化。

#### T005R — RED：合并构造 staging

- **ID**：T005R；**versioned_refs**：spec（FR-PUB-002）+ plan（DEC-K3-002）
- **source_refs**：D-004·detail D2·D-004b；**FR**：FR-PUB-002；**AC**：AC-K3-1/AC-K3-3
- **依赖**：T002/T003/T004；**动作**：写失败测试：空库=骨架+批次覆盖；非空库=原有内容保留+本批托管路径覆盖；未托管路径不删；证据文件逐字节相等（源 sha256=目标 sha256 断言）；未托管路径碰撞→硬失败零字节。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_merge_construct`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_merge_construct`

#### T005G — GREEN：合并构造

- **ID**：T005G；**动作**：`construct_staging(kb_dir, batch_dir, manifest, sidecar)`：复制当前版本（或空）→按托管集（骨架声明∪manifest pages）覆盖批次文件→返回 staging 路径与 tree hash。
- **gate_cmd**：同 T005R；**oracle identity**：同对卡 RED 断言转绿

#### T006R — RED：首发布骨架与拒绝

- **ID**：T006R；**versioned_refs**：spec（FR-PUB-003）+ plan（Code Anchors #5）
- **source_refs**：D-013·取证 #5；**FR**：FR-PUB-003；**AC**：AC-K3-5
- **依赖**：T005；**动作**：写失败测试：空目录→骨架（kb.structure.md 存在且 sha256 登记）；非空无结构声明→拒绝非零码；库根已存在 `current` 名冲突→blocked。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_first_publish_skeleton`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_first_publish_skeleton`

#### T006G — GREEN：首发布骨架

- **ID**：T006G；**动作**：`ensure_target_kb(kb_dir, sidecar)`：`default_publication_structure()` 写骨架（含 sha256 登记）；三类输入三分支。
- **gate_cmd**：同 T006R；**oracle identity**：同对卡 RED 断言转绿

#### T007R — RED：LKG+指针+入口原子换版

- **ID**：T007R；**versioned_refs**：spec（FR-PUB-004/005）+ plan（DEC-K3-003/005）
- **source_refs**：D-001/D-002/D-010·detail D1/D3；**FR**：FR-PUB-004/005；**AC**：AC-K3-1
- **依赖**：T006；**动作**：写失败测试：成功发布→版本目录落 sidecar/versions、lkg 存旧版+pointer.json、入口 rename 换后解析=新 hash、读回校验过；发布后旧 LKG 被轮换。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_publish_happy_path`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_publish_happy_path`

#### T007G — GREEN：原子换版

- **ID**：T007G；**动作**：`publish()` 主流程（锁→staging→备份 LKG→rename 入口→读回→release 记录）。
- **gate_cmd**：同 T007R；**oracle identity**：同对卡 RED 断言转绿

#### T008R — RED：no-op 发布

- **ID**：T008R；**versioned_refs**：spec（FR-PUB-006）+ plan
- **source_refs**：clarify C4；**FR**：FR-PUB-006；**AC**：AC-K3-1
- **依赖**：T007；**动作**：写失败测试：同 tree hash 再发布→exit 0、`no_op=true`、lkg/pointer 不变、无新版本目录。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_publish_noop`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_publish_noop`

#### T008G — GREEN：no-op

- **ID**：T008G；**动作**：publish 前置 hash 比对短路分支。
- **gate_cmd**：同 T008R；**oracle identity**：同对卡 RED 断言转绿

#### T009R — RED：失败收据

- **ID**：T009R；**versioned_refs**：spec（FR-PUB-007/FR-COST-001）+ plan
- **source_refs**：D-005·红队 N-4/F12；**FR**：FR-PUB-007；**AC**：AC-K3-2
- **依赖**：T007；**动作**：写失败测试：注入 staging 中途失败→非零码+receipts/<run>.json 含 reason_code/三项成本（非 null）/批次 attempt_id；收据落盘失败→stdout/运行记录镜像+`receipt_sink_unavailable`。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_failure_receipt`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_failure_receipt`

#### T009G — GREEN：失败收据

- **ID**：T009G；**动作**：`write_receipt()` + finally 挂钩 + 镜像降级。
- **gate_cmd**：同 T009R；**oracle identity**：同对卡 RED 断言转绿

#### T010R — RED：回滚

- **ID**：T010R；**versioned_refs**：spec（FR-PUB-005）+ plan（DEC-K3-008）
- **source_refs**：detail D3·红队 N-5；**FR**：FR-PUB-005；**AC**：AC-K3-1
- **依赖**：T007；**动作**：写失败测试：发布后回滚→入口解析=旧版 hash、被换下版本成为新 LKG、指针链更新、读回校验；指针损坏→非零码不猜；回滚全程可读。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_rollback`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_rollback`

#### T010G — GREEN：回滚

- **ID**：T010G；**动作**：`rollback()` 复用 publish 管线（备份当前→换版→轮换）。
- **gate_cmd**：同 T010R；**oracle identity**：同对卡 RED 断言转绿

## Phase P3 — 成本度量

### Goal

成功/失败运行三项成本真实非 null、承接编译侧、真 0 带 reason。

#### T011R — RED：run record 与编译侧承接

- **ID**：T011R；**versioned_refs**：spec（FR-COST-001/002）+ plan（Interfaces）
- **source_refs**：D-005·detail D4·红队 N-3；**FR**：FR-COST-001/002；**AC**：AC-K3-2
- **依赖**：T009；**动作**：写失败测试：失败运行记录=承接字段（inherited_from_compile）+发布段自身值，三项非 null；批次无 run-metrics→发布段记 0 带 `no_provider_call_yet`；0 无 reason→判失败。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_run_record_costs`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_run_record_costs`

#### T011G — GREEN：成本承接

- **ID**：T011G；**动作**：`build_run_record()`（读 `_audit/run-metrics.json` 同名三项→承接字段；计时；reason 词表校验）。
- **gate_cmd**：同 T011R；**oracle identity**：同对卡 RED 断言转绿

## Phase P4 — 冻结物管理

### Goal

三份冻结物快照/清单/frozen_id；齐备门与只读断言。

#### T012R — RED：freeze 命令与 manifest

- **ID**：T012R；**versioned_refs**：spec（FR-FRZ-001/002/003）+ plan
- **source_refs**：D-006·红队 N-9；**FR**：FR-FRZ-001/002/003；**AC**：AC-K3-5
- **依赖**：T002（hash）；**动作**：写失败测试：三份入 `freeze/<frozen_id>/`；清单恰 89 份 .md（多/少都红）；排除 `.`开头与 `_gbrain/`（fixture 造这两个干扰）；frozen_id 复算一致；manifest 字段齐。
- **精确文件**：`tests/acceptance/test_task9_accept.py::test_freeze_manifest`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k test_freeze_manifest`

#### T012G — GREEN：freeze

- **ID**：T012G；**动作**：`kb_accept.py` 的 `freeze()`（拷贝+清单+manifest+frozen_id 推导），CLI 形态=accept 入口 `--freeze` 模式（plan DEC/Interfaces，红队 blocking-2 处置，三入口冻结不变）。
- **gate_cmd**：同 T012R；**oracle identity**：同对卡 RED 断言转绿

#### T013R — RED：preflight 齐备门与只读断言

- **ID**：T013R；**versioned_refs**：spec（FR-FRZ-004/005）+ plan
- **source_refs**：蓝队 M4/DB12·红队 F1；**FR**：FR-FRZ-004/005；**AC**：AC-K3-5
- **依赖**：T012；**动作**：写失败测试：缺一/改一字节→blocked 零逐题结论；判定器触达对照活库路径的探测函数被拦截；同运行内 tree hash 缓存复用（调用计数断言）。
- **精确文件**：`tests/acceptance/test_task9_accept.py::test_preflight_gate`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k test_preflight_gate`

#### T013G — GREEN：preflight

- **ID**：T013G；**动作**：`preflight(frozen_id)`（复算+路径白名单断言+缓存）。
- **gate_cmd**：同 T013R；**oracle identity**：同对卡 RED 断言转绿

## Phase P5 — 验收判定

### Goal

题集生成→四结果判定→汇总→绑定重放→区分度；汇总唯一解。

#### T014R — RED：问题集生成器

- **ID**：T014R；**versioned_refs**：spec（FR-ACC-002）+ plan（DEC-K3-006）
- **source_refs**：clarify C2·红队 F6；**FR**：FR-ACC-002；**AC**：AC-K3-3
- **依赖**：T013；**动作**：写失败测试：每模块 2 题、模板按 i mod 3、同输入两次生成 sha256 一致；缺标题用 slug/缺参考块用叙述首句；要素不足模块记 degraded_modules；题数 0/重复 id/缺字段→blocked（FR-ACC-008）。
- **精确文件**：`tests/acceptance/test_task9_accept.py::test_question_generator`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k test_question_generator`

#### T014G — GREEN：生成器

- **ID**：T014G；**动作**：`generate_questions(manifest_pages)` 纯函数。
- **gate_cmd**：同 T014R；**oracle identity**：同对卡 RED 断言转绿

#### T015R — RED：四结果判定器

- **ID**：T015R；**versioned_refs**：spec（FR-ACC-003）+ plan（DEC-K3-006）
- **source_refs**：母任务 S8·红队 N-6/F5；**FR**：FR-ACC-003；**AC**：AC-K3-3
- **依赖**：T014；**动作**：写失败测试：四结果各造正/反例——命中=回溯冻结行区间+指纹一致（词面重合但指纹不符必须不算命中）；定位有效=锚点可解析；出处正确=source 指纹一致；对照无内容=未覆盖。
- **精确文件**：`tests/acceptance/test_task9_accept.py::test_judge_four_results`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k test_judge_four_results`

#### T015G — GREEN：判定器

- **ID**：T015G；**动作**：`judge(question, kb_pages, frozen_sources)` 纯函数（`judge_rules_version=k3-v1`）。
- **gate_cmd**：同 T015R；**oracle identity**：同对卡 RED 断言转绿

#### T016R — RED：汇总 verdict

- **ID**：T016R；**versioned_refs**：spec（FR-ACC-004）+ plan
- **source_refs**：D-007·clarify C1·红队 F4；**FR**：FR-ACC-004；**AC**：AC-K3-3
- **依赖**：T015；**动作**：写失败测试：硬失败题>0→fail；命中率<80%→fail；全未覆盖（分母 0）→fail(`no_effective_questions`)；有效分母<10→blocked；未覆盖不计分（18 题未覆盖+2 题全对=100% 命中）；同一记录重算两次 verdict 相同。
- **精确文件**：`tests/acceptance/test_task9_accept.py::test_verdict_summary`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k test_verdict_summary`

#### T016G — GREEN：汇总

- **ID**：T016G；**动作**：`summarize(results)` 纯函数。
- **gate_cmd**：同 T016R；**oracle identity**：同对卡 RED 断言转绿

#### T017R — RED：判定记录绑定与重放拒判

- **ID**：T017R；**versioned_refs**：spec（FR-ACC-005/008）+ plan
- **source_refs**：D-006 补充·红队 F-6；**FR**：FR-ACC-005/008；**AC**：AC-K3-3
- **依赖**：T016；**动作**：写失败测试：记录绑定树指纹/题集 sha/口径版本/frozen_id 四者；重放时当前树指纹不符→"被测对象已变，不可复跑"且零新结论；accept 全流程 JSON 落盘可重读；**并发取锁**：publish 持锁期间 accept 同锁等待/报错、绝不读到换版中间态（FR-ACC-006 承接）。
- **精确文件**：`tests/acceptance/test_task9_accept.py::test_record_binding_replay`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k test_record_binding_replay`

#### T017G — GREEN：绑定与重放

- **ID**：T017G；**动作**：`accept()` 编排（锁内读指纹→preflight→逐题→汇总→写记录）。
- **gate_cmd**：同 T017R；**oracle identity**：同对卡 RED 断言转绿

#### T018R — RED：区分度检查

- **ID**：T018R；**versioned_refs**：spec（FR-ACC-007）+ plan
- **source_refs**：clarify C3·D-008；**FR**：FR-ACC-007；**AC**：AC-K3-4
- **依赖**：T015；**动作**：写失败测试：三类坏样本（缺表格/错出处/孤儿页 fixture）各绑 2 必失败题全判失败；正确产物同批题不误判；样本与绑定关系登记 sha256 随冻结入库。
- **精确文件**：`tests/acceptance/test_task9_accept.py::test_discrimination`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k test_discrimination`

#### T018G — GREEN：区分度

- **ID**：T018G；**动作**：`discrimination_check(frozen_dir)` + fixture 三类样本构造器。
- **gate_cmd**：同 T018R；**oracle identity**：同对卡 RED 断言转绿

## Phase P6 — 负例与聚合

### Goal

四类负例注入断言、缺陷台账、端到端聚合。

#### T019R — RED：四类负例注入

- **ID**：T019R；**versioned_refs**：spec（FR-NEG-001/002）+ plan（Test Strategy）
- **source_refs**：D-009·detail D1·红队 N-1/N-10；**FR**：FR-NEG-001/002；**AC**：AC-K3-1
- **依赖**：T007；**动作**：写失败测试：copy 中途抛错/取消检查点/暂存 hash 篡改/越界路径批次——四注入各自断言入口解析 hash∈{旧,新}、blocked 类父目录差分零越界；取消后无 staging 残留、无悬空指针。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_negative_injections`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_negative_injections`

#### T019G — GREEN：负例

- **ID**：T019G；**动作**：publish 内部边界点参数化（可注入）+ finally 恢复。
- **gate_cmd**：同 T019R；**oracle identity**：同对卡 RED 断言转绿

#### T020R — RED：缺陷台账

- **ID**：T020R；**versioned_refs**：spec（FR-LED-001）+ plan
- **source_refs**：D-012·红队 N-8·蓝队 B1；**FR**：FR-LED-001；**AC**：AC-K3-2/AC-K3-3
- **依赖**：T009、T017（void/重放机制）；**动作**：写失败测试：台账 append-only 字段齐；修复走新批次后旧判定记录标 void 且重放拒绝；该次运行成本含整跑承接。
- **精确文件**：`tests/acceptance/test_task9_publish.py::test_defect_ledger`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_defect_ledger`

#### T020G — GREEN：台账

- **ID**：T020G；**动作**：`ledger.jsonl` 读写 + void 语义。
- **gate_cmd**：同 T020R；**oracle identity**：同对卡 RED 断言转绿

#### T021R — RED：端到端聚合

- **ID**：T021R；**versioned_refs**：spec（§3 全部 SCN）+ plan（Overview）
- **source_refs**：D-001·D-003·D-004·D-005·D-006·D-007·D-008·D-009·D-010·D-011·D-012·D-013·D-004b 全列；**FR**：全部；**AC**：AC-K3-1…5
- **依赖**：T001-T020；**动作**：写失败测试：fixture 全链（批次→发布→冻结→验收 pass→重放一致→负例→回滚→再验收）一脚本跑通且各节点 JSON 可解析。
- **精确文件**：`tests/acceptance/test_task9_accept.py::test_e2e_aggregate`
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k test_e2e_aggregate`

#### T021G — GREEN：聚合

- **ID**：T021G；**动作**：收尾使聚合绿；回填全部执行状态区。
- **gate_cmd**：同 T021R；**oracle identity**：同对卡 RED 断言转绿

## 审查记录（step 9 review-plan）· 真实执行，available-with-failures

- 红队 11 条（blocking 2 / major 3 / minor 6）：`review/task9-plan-red.md`（`a7c9ece4686e…` 存档后回填实值）；蓝队 8 条（major 2 / minor 6）：`review/task9-plan-blue.md`（`13b3a945ef66…`）。
- provider/transport 事实：宿主子代理执行，未走 wh-review provider，如实记 unavailable。

| finding | 等级 | 处置 | 落点 |
| --- | --- | --- | --- |
| 红-1 DEC-K3-002 判定口径漂移（骨架∪manifest 扩权） | blocking | **fixed**：改为"manifest 页面集先登记进 kb.structure.md 声明，判定只对照声明"，spec 口径零变更 | plan DEC-K3-002 |
| 红-2 freeze() 无 CLI 入口 | blocking | **fixed**：accept 入口 `--freeze` 模式（三入口冻结不变） | plan Interfaces + T012G |
| 红-3/蓝-2 FR-ACC-006 验收取锁零承接 | major | **fixed**：T017R 增并发取锁断言；traceability 补行 | T017R/G |
| 红-4/蓝-1 traceability 卡号系统性错位 | major | **fixed**：表全量重写，逐卡核对 gate 编号 | plan traceability |
| 红-5/蓝 minor FR-STA-001、FR-COST-003 无卡 | major/minor | **fixed**：FR-STA-001→T005/T015 承接；F-002 实物对照注记 T011R（verify-code 引用） | traceability + T011R |
| 蓝 minor：26 对 vs 21 对不符 | minor | **fixed**：plan Quick Read 与 step 8 改"21 对+1 聚合" | plan |
| 蓝 minor：GREEN 卡缺 gate_cmd | minor | **fixed**：全部 GREEN 卡补 gate_cmd/oracle identity 行 | tasks 全部 G 卡 |
| 蓝 minor：T020 漏依赖 T017 | minor | **fixed** | T020R |
| 蓝 minor：D-001/D-003/D-007/D-010 未显式入卡 | minor | **fixed**：T001/T007/T016/T021 source_refs 显式 | tasks |
| 红 minor：链接相对目标/取消信号接入/收据镜像归属 | minor | **fixed**：链接目标冻结相对路径（DEC-K3-003 区）；SIGINT→cancel 回调写入 Interfaces；收据镜像已归 T009G | plan |


## 执行状态填写区

（build-code 逐卡回填：status / changed files / commands / evidence；唯一完成权威。）

### build-code Phase Card · P1 / T001R→T004G

- **目标**：先建立三独立 CLI 入口的失败行为测试，再完成 P1 基础层（tree hash、批次白名单、sidecar/锁、fixture），为 P2 发布通道提供可复用纯函数。
- **本 phase 允许文件/符号**：`tests/acceptance/test_task9_publish.py`（T001R–T004R 行为测试）；`src/knowledge_digest/kb_publish.py`（T001G–T004G 新模块及本 phase 约定符号）；`tests/fixtures/task9_publish/__init__.py`（fixture）；`pyproject.toml` 仅 T001G 的三条脚本入口；本区仅追加真实执行事实。
- **覆盖 AC/FR**：工程接线卡 FR-CLI-001；P1 基础支撑 FR-PUB-008、FR-PUB-001、FR-PUB-004/005，间接支撑 AC-K3-1/3。AC 不在本 phase 单独宣称完成。
- **非目标**：不改 `cli.py`/`simple_cli.py`/`semantic_*.py`/`full_release.py`/`publisher.py`/`lock.py`/`kb_structure.py`；不调用 provider；不改 K1/K2 测试或真实语料；不 commit/merge/push。
- **兼容边界**：三入口独立于既有 `digest` argparse；只复用现有锁与骨架 helper，不 import semantic 模块；知识库写权和 sidecar 命名按 plan 的 File Boundary/DEC-K3-001…005。
- **测试路由**：`routing_tier=feature`；每张 RED/GREEN 使用任务声明的同一 `gate_cmd` 与 oracle identity；本 phase 选择 `backend-testing`，并对实际 changed-files 执行一次 `test-routing-advisor`。
- **停止条件**：发现方向/规格冲突、超出 File Boundary、或测试 oracle 无法观察真实消费者时停止并记录；实现级失败留在本 task 修复，环境/审查不可用如实记录。
- **阶段末摘要预期**：逐卡 status、changed files、命令/exit、证据、FR/AC 结果、review/finding disposition 和下一卡完整回填；T001R 必须先得到真实非零 RED，再进入 T001G。

#### T001R 执行事实

- **status**：completed（预期 RED 已发生；未改生产代码）
- **changed files**：`tests/acceptance/test_task9_publish.py`
- **command / exit**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_cli_entries_exist` / `1`
- **oracle**：`KeyError: 'knowledge-digest-publish'`，说明三入口尚未登记；符合 RED 预期。
- **evidence**：pytest 实际输出；`snapshot=task9 worktree HEAD 973cf31 + 当前未提交测试`

#### T001G 执行事实

- **status**：completed（GREEN）
- **changed files**：`pyproject.toml`、`src/knowledge_digest/kb_publish.py`、`src/knowledge_digest/kb_accept.py`、`tests/acceptance/test_task9_publish.py`
- **commands / exit**：`uv sync` / `0`；同 T001R gate / `0`
- **oracle**：三脚本映射正确；`knowledge_digest.kb_publish`、`knowledge_digest.kb_accept` 可导入且 `--help` 返回 0；既有 `digest` 映射保持 `knowledge_digest.simple_cli:main`。
- **route**：`test-routing-advisor` 实际重判 `feature`，`result=pass`；实际边界为 `tests/acceptance/test_task9_publish.py`，未改变原计划 `feature` 路由。
- **AC/FR**：FR-CLI-001 `pass`（工程卡）；AC-K3-1…5 本卡尚未宣称完成。
- **review**：P1 phase review 尚未执行；待 P1 T002–T004 完成后一次执行。

#### T002R / T002G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_tree_hash_frozen_algorithm` / `1`；oracle 为 `kb_tree_hash is not implemented`。
- **GREEN**：同 gate / `0`；固定 tree hash `67fd45da021894df27ec0a093274cd1246c3143b981a3d8a62375953c6d2d3af`、符号链接和缺失根拒绝通过。
- **FR/AC**：FR-PUB-008 `pass`；支撑 AC-K3-1/3，未单独宣称 AC 完成。

#### T003R / T003G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_manifest_whitelist` / `1`；oracle 为 `load_batch_manifest is not implemented`。
- **GREEN**：同 gate / `0`；合法 manifest 返回 `ready`，缺字段、错误状态、非空 blockers 返回 `blocked` 并指明字段。
- **FR/AC**：FR-PUB-001 `pass`；支撑 AC-K3-1，未单独宣称 AC 完成。

#### T004R / T004G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_sidecar_layout_and_lock` / `1`；oracle 为 `sidecar_path is not implemented`。
- **GREEN**：同 gate / `0`；验证 `.knowledge-base.kd/{versions,staging,lkg,releases,receipts,freeze}`、父目录锁争用拒绝、UTC 当日序列 `005`。
- **FR/AC**：FR-PUB-004/005 基础机械 `pass`；支撑 AC-K3-1，原子发布/LKG 完整语义留待 P2。
- **fixture**：新增 `tests/fixtures/task9_publish/__init__.py`，提供 `make_batch_with_nav`、`make_kb`；仅作为离线测试数据构造器，不接 provider。

#### P1 review / finding disposition

- **review fact**：正式 `review --action=record` 已执行；attempt `quality/reviews/attempts/fccd02cc-1d0a-5435-a3c5-20b34774ab29/attempt.json`，状态 `unavailable`，原因 `REVIEW_SOURCE_DRIFT`（review dispatch 期间主线进入后续实现，源快照改变）。两路 provider 均有真实 completed 输出，未发布 semantic result；不把 unavailable 改写成 pass，也不重发同一 P1 review。
- **findings**：P1 review 的两条 blocking/一条 major 均针对后续卡尚未实现的 publish/rollback/accept 与端到端调用；按当前 Phase 边界判为 `rejected_invalid`（不是否认事实）：P1 只交付 T001–T004 基础层，核心行为由 P2–P6 明确承接，P1 未宣称 AC-K3-1…5 完成。P2–P6 将以真实命令行为测试重新证明这些能力。
- **review limitation**：P1 semantic review 质量事实保持 `unavailable/incomplete`；provider findings 证据保留在上述 attempt 的 provider output，不作为阶段通过依据。

#### T005R / T005G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_merge_construct` / `1`；`construct_staging is not implemented`。
- **GREEN**：同 gate / `0`；空库骨架+批次覆盖、非空库原有内容保留/页面覆盖、`_audit` 逐字节复制、未托管碰撞拒绝均通过。
- **FR/AC**：FR-PUB-002 `pass`；支撑 AC-K3-1/3，未单独宣称 AC 完成。

#### T006R / T006G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_first_publish_skeleton` / `1`；缺 `structure_sha256`。
- **GREEN**：同 gate / `0`；新库默认结构与 sha256 登记、非空无声明拒绝、`current` 名冲突拒绝通过。
- **FR/AC**：FR-PUB-003 `pass`；支撑 AC-K3-5，未单独宣称 AC 完成。

#### T007R / T007G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_publish_happy_path` / `1`；publish 为 `NotImplementedError`。
- **GREEN**：同 gate / `0`；发布成功后 `current` 是相对 symlink，版本树读回 hash 一致，旧版 LKG/pointer 和 release 记录存在，root 仅保留 `current`。
- **FR/AC**：FR-PUB-004/005 基础主流程 `pass`；支撑 AC-K3-1，四类负例留 P6。

#### T008R / T008G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_publish_noop` / `1`；临时关闭 no-op 分支后生成了新版本，`no_op` 为 false。
- **GREEN**：同 gate / `0`；同 tree hash 返回 `no_op=true`，不新增 version、不轮换 LKG/pointer、不留 staging。
- **FR/AC**：FR-PUB-006 `pass`；支撑 AC-K3-1。

#### T009R / T009G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_failure_receipt` / `1`；临时关闭 receipt 写入后收据文件缺失。
- **GREEN**：同 gate / `0`；copy 中途失败不改当前版本，receipt 含原因/attempt/成本；sink 失败返回 `receipt_sink_unavailable` 与原始原因镜像。
- **FR/AC**：FR-PUB-007 `pass`；支撑 AC-K3-2，成本完整承接由 T011G 锁定。

#### T010R / T010G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：`uv run --frozen pytest -q tests/acceptance/test_task9_publish.py -k test_rollback` / `1`；rollback 未实现。
- **GREEN**：同 gate / `0`；回滚恢复上一版、更新 LKG/pointer；损坏 pointer 非零拒绝且当前 hash 不变。
- **FR/AC**：FR-PUB-005 `pass`；支撑 AC-K3-1。

#### T011R / T011G 执行事实

- **status**：completed（RED→GREEN）
- **changed files**：`tests/acceptance/test_task9_publish.py`、`src/knowledge_digest/kb_publish.py`
- **RED**：同 `test_run_record_costs` gate / `1`；临时去除 compile metrics 承接后 `provider_calls` 从 7 变为 0。
- **GREEN**：同 gate / `0`；编译侧三项保留在 `compile.inherited_from_compile=true`，发布侧 0 带 `no_provider_call_yet`，无理由 0 被 blocked。
- **FR/AC**：FR-COST-001/002 `pass`；AC-K3-2 尚待 P6/verify-code 真实链路确认；旧 `publisher.py` null 不在本卡修复。

### build-code Phase Cards · P2–P6 执行事实

#### P2 Phase Card · T005R→T010G

- **目标**：完成批次合并、默认骨架、固定 `current` 原子换版、LKG、no-op、失败收据和回滚。
- **允许文件**：`src/knowledge_digest/kb_publish.py`、`tests/acceptance/test_task9_publish.py`；不改既有 digest/K1/K2 发布模块。
- **覆盖**：FR-PUB-002…007；支撑 AC-K3-1/2/3/5。
- **实际路由**：原计划 `feature`；对实际生产+测试跨根边界重判为 `fullstack`，`result=pass`。采用 `fullstack-slice-testing`；本项目无服务/UI，真实 slice 是 fixture 批次→staging→`current`/LKG/receipt→回读 hash 的 CLI/文件系统链路。

#### P3 Phase Card · T011R→T011G

- **目标**：成本三项非 null、编译侧承接、真 0 带 reason。
- **允许文件**：`src/knowledge_digest/kb_publish.py`、`tests/acceptance/test_task9_publish.py`；不修旧 `publisher.py`。
- **覆盖**：FR-COST-001/002；AC-K3-2 仅在离线 fixture 上有证据，真实 89 条语料/provider 仍交 verify-code。
- **实际路由**：重判 `fullstack`，`result=pass`；采用 `fullstack-slice-testing`，沿发布失败 receipt 与承接 metrics 端到端回读。

#### P4 Phase Card · T012R→T013G

- **目标**：冻结 89 条输入、release4、comparison，生成可复算 `frozen_id`，并在验收前做齐备/hash/只读门禁。
- **允许文件**：`src/knowledge_digest/kb_accept.py`、`tests/acceptance/test_task9_accept.py`；不改 K1/K2/core modules。
- **覆盖**：FR-FRZ-001…005；AC-K3-5。
- **实际路由**：重判 `fullstack`，`result=pass`；采用 `fullstack-slice-testing`，真实 slice 是 freeze→manifest→preflight→受锁目标树回读；不涉及浏览器或服务。

#### P5 Phase Card · T014R→T018G

- **目标**：确定性题集、四结果判定、阈值汇总、记录绑定/重放和区分度检查。
- **允许文件**：`src/knowledge_digest/kb_accept.py`、`tests/acceptance/test_task9_accept.py`；不改发布/K1/K2 模块。
- **覆盖**：FR-ACC-001…008；AC-K3-3/4，真实 89 条语料/provider 仍未在 build-code 运行。
- **实际路由**：重判 `fullstack`，`result=pass`；采用 `fullstack-slice-testing`，以发布版本目录、冻结快照、题集、逐题结果、重放为真实文件链路。

#### P6 Phase Card · T019R→T021G

- **目标**：四类发布负例、缺陷台账和全链端到端聚合。
- **允许文件**：`src/knowledge_digest/kb_publish.py`、`src/knowledge_digest/kb_accept.py`、`tests/acceptance/test_task9_publish.py`、`tests/acceptance/test_task9_accept.py`、`tests/fixtures/task9_publish/__init__.py`；`pyproject.toml` 只保留三条入口。
- **覆盖**：FR-NEG-001/002、FR-LED-001；AC-K3-1…5 的 fixture 级聚合。
- **实际路由**：重判 `fullstack`，`result=pass`；采用 `fullstack-slice-testing`。无浏览器/UI；`test_e2e_aggregate` 覆盖批次→两次发布→freeze→accept pass→replay→rollback。

#### P2–P6 实现与测试事实

- **T005–T011**：各 RED gate 均曾以 exit `1` 暴露缺失行为，随后对应 GREEN gate exit `0`；发布聚焦行为为 merge/skeleton/happy path/no-op/receipt/rollback/cost，未回放旧阶段。
- **T012/T013**：`uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k 'test_freeze_manifest or test_preflight_gate'` / `0`；2 passed。preflight 的计数断言因新增冻结物 rehash 更新为 7 次，验证的是“preflight 后再次校验”，不是跳过校验。
- **T014–T018**：对应五个题集/判定/汇总/重放/区分度 gate 均 GREEN；当前聚焦聚合命令 `uv run --frozen pytest -q tests/acceptance/test_task9_publish.py tests/acceptance/test_task9_accept.py` / `0`，`21 passed`。
- **T019/T020/T021**：负例、台账、聚合 gate 均 GREEN；新增缺页、非法 `run_id`、错页面/锚点 citation、无范围 citation 负例；聚合实际通过发布两版、验收 pass、重放一致和回滚。
- **最终全仓 aggregate**：`uv run --frozen pytest -q` / `1`；`1038 passed, 4 skipped, 20 failed`。该次全仓结果发生在最后的 release4 snapshot 修复之前；20 个失败均在既有 Task0/Task1/Task2a/Task5 套件，主要是当前 worktree 缺少既有 `quality/evidence/task2-entry` 文件、历史 `digest` 参数/帮助文本契约不一致和 calibration hash 缺失；Task9 两个 acceptance 文件不在失败清单。release4 修复后只重跑受影响的 Task9 聚焦回归，`21 passed`，未重复全仓。该结果不是全仓通过。
- **diff/syntax**：`uv run --frozen python -m py_compile src/knowledge_digest/kb_accept.py src/knowledge_digest/kb_publish.py` / `0`；`git diff --check` / `0`。当前 branch=`task/KnowledgeDigest/task9-release-safety-query-acceptance`，HEAD=`973cf31a0586d99d89bf4242290ece064a7b5a76`，无 commit/merge/push。

#### P2 review / finding disposition

- **review fact**：attempt `quality/reviews/attempts/61e1b605-4556-5c24-ab4a-1442a1ff298d/attempt.json` 为 `unavailable`，原因 `REVIEW_SOURCE_DRIFT`；同 phase retry 返回 `review_budget_exhausted`。因此 P2 没有 trusted terminal review result。
- **finding disposition**：provider 输出的 8 条 major 均在后续当前代码中修复：publish 主入口退出码、绝对 sidecar/相对 `current`、staging sweep、LKG provenance、metrics reason、bootstrap receipt hash、copy verification、accept 真实入口。处置为 `fixed`，但不能把 unavailable review 改写成 pass。

#### P3 review / finding disposition

- **review fact**：首次 attempt `quality/reviews/attempts/344094c0-6b9e-5ac0-abde-4fb31149dbb1/attempt.json` 因 `host_provider required` 执行失败；重试 canonical result=`quality/reviews/results/build-code-simple-709d6334-a0c7-538d-a056-a6dfd2a3cc4e.json`，report=`quality/reviews/reports/build-code-simple-709d6334-a0c7-538d-a056-a6dfd2a3cc4e.md`，可用。
- **finding disposition**：5 条 major（LKG 失败清理、receipt sink 异常类型、`run_id` 越界、path locator canonical frozen id、区分度样本/期望原因）均 `fixed`；focused retry 返回 `REVIEW_RETRY_BUDGET_EXHAUSTED`，保留 unavailable retry 事实。

#### P4 review / finding disposition

- **review fact**：canonical result=`quality/reviews/results/build-code-simple-d02457a4-49a4-591d-a2be-ba817e5fbdf4.json`，report=`quality/reviews/reports/build-code-simple-d02457a4-49a4-591d-a2be-ba817e5fbdf4.md`，available；3 条 major+3 条 minor。
- **finding disposition**：manifest 覆盖 `kb.structure.md`、死的 `math.isfinite`、finalization cleanup、bootstrap no-op、incomplete replay、no-op release 覆盖均已 `fixed`；focused retry 预算耗尽，未重发。

#### P5 review / finding disposition

- **review fact**：canonical result=`quality/reviews/results/build-code-simple-01b5fe77-4408-54fa-a0de-89ac0ffdcf21.json`，report=`quality/reviews/reports/build-code-simple-01b5fe77-4408-54fa-a0de-89ac0ffdcf21.md`，available；3 条 major+1 条 minor。
- **finding disposition**：内置 discrimination 绑定 accept、freeze/target 前后 rehash、默认题集改从 frozen release4/comparison、语义重复题拒绝、dead main fallback 均已 `fixed`；focused retry 尚无可用预算。

#### P6 review / finding disposition

- **initial review fact**：canonical result=`quality/reviews/results/build-code-simple-562341f9-4b1b-523f-a77b-18a46e1d4c4c.json`，report=`quality/reviews/reports/build-code-simple-562341f9-4b1b-523f-a77b-18a46e1d4c4c.md`，semantic available；`codex/luna` 给出 3 条 major，`kimi/coding` 因 `EVIDENCE_ANCHOR_INVALID` failed。
- **finding disposition**：3 条 major 已 `fixed`：manifest 声明页逐项存在且逐项复制、citation 必须绑定 question page/anchor 且拒绝无范围证据、`construct_staging` 校验安全 `run_id`。修复后定向 gate 与 21-test 聚焦回归均 GREEN。
- **retry fact**：修复后按“实际修复后允许一次 focused review”提交，返回 `unavailable / REVIEW_RETRY_BUDGET_EXHAUSTED`，未生成新 attempt；不把 initial findings 的 fixed 处置误报为复审通过。

#### Final aggregate / integration review 状态

- **final integration review initial**：canonical result=`quality/reviews/results/build-code-simple-2cac696d-f470-575d-ad1a-8c06554032dc.json`，report=`quality/reviews/reports/build-code-simple-2cac696d-f470-575d-ad1a-8c06554032dc.md`，available；发现 1 条 major：accept judge 未显式接收 release4 snapshot。
- **finding disposition**：该 major 已 `fixed`：accept 将 release4/comparison 作为命名 snapshot 传入 judge，题目记录来源 snapshot，judge 输出两侧命中状态；release4-only/双 snapshot 测试通过。修复后 integration focused retry 返回 `unavailable / REVIEW_RETRY_BUDGET_EXHAUSTED`，未生成新 attempt，因此不能把当前 integration review 写成 clean。
- **build-code stage boundary**：无可用 Stage Agent host outcome/executor，且 integration focused retry unavailable；build-code 正式 stage completion 仍为 `unavailable/incomplete`，不能用 shell 测试代替。
- **AC 当前边界**：AC-K3-1/3/4 在离线 fixture 级为 `pass`；AC-K3-2 的 fixture 成本/收据为 `pass`，真实 K1/K2 已完成 89 条语料编译、K2 导航生成和成本承接，真实发布已 `released`；AC-K3-3 的真实验收与重放均可执行且结果一致，但因目标知识库与 CompanyBrain 无有效对照覆盖，真实 verdict 为 `fail/no_effective_questions`，不能宣称验收通过；AC-K3-5 的冻结/preflight 为 `pass`。正式 verify-code 质量仍为 `incomplete`，原因是 `quality_review` 缺少 authenticated dsh executor outcome。

### verify-code 执行事实

- **真实 freeze/preflight**：命令 `uv run --frozen knowledge-digest-accept --freeze --input-dir '/Users/Hugh/Downloads/confluence 原始数据' --release4-dir '/Users/Hugh/Downloads/KnowledgeDigest-task5-m402-20260908.release4' --comparison-dir '/Users/Hugh/Hugh/Knowledge/CompanyBrain' --freeze-root '/Users/Hugh/Downloads/KD测试/2026-09-16-task9-verify'` / `0`；产物 `frozen_id=2fbd69e5e9c197ee968692435313fd375bf1474ccc0ee8a6247ef5dae2d9bb3b`，`input=89`、`release4=119`、`comparison=878`，manifest sha256=`bd62323fdae8da70925a5530477bb109c161b363b6a2555e93dab2e2f106194c`。
- **真实 preflight**：调用 `preflight(frozen_id, freeze_root)` / `ready`；三根 tree hash 已复算，未触达 live comparison。真实目标目录不存在，调用 `accept()` 返回 `blocked`、`reason_code=accept_preflight_blocked`、`reasons=[target_current_missing]`、`results=[]`，没有编造 verdict。
- **真实 K1/K2 编译**：命令 `KNOWLEDGEDIGEST_TASK8_QUERY_FIXTURE=tests/fixtures/task8_nav/query_fixture_sample.json uv run --frozen digest '/Users/Hugh/Downloads/confluence 原始数据' --manifest config/task4-source-coverage-89-input.v1.json --output-parent '/Users/Hugh/Downloads/KD测试/task9-real-2026-09-16'` / `2`；批次=`/Users/Hugh/Downloads/KD测试/task9-real-2026-09-16/2026-09-16-1`，K1 `run_status=complete`、`source_count=89`、`topic_count=87`、`provider_calls=87`、`provider_tokens=395250`，但 K2 `navigation_status=blocked`，原因=`model-output-invalid:description must contain Chinese text`，没有生成可发布导航。题集另有 10 条 `target_slug` 缺失，按契约即使模型输出通过也只能保持 `incomplete`，未补值作弊。
- **真实 K1/K2 重跑确认**：同输入使用正式 `digest` CLI 再跑到 `/Users/Hugh/Downloads/KD测试/task9-real-rerun-2026-09-16/2026-09-16-1` / `2`；K1 `cache_hits=87`、provider calls=0，K2 仍返回 `model-output-invalid:description must contain Chinese text`。这确认不是一次性网络/调用故障；未修改冻结题集，也未把候选 slug 写回题集。
- **题集定位诊断**：QP-01…QP-10 的 `target_topic` 在真实 K1 manifest 中均各自唯一映射到一个 `products/...md` 页面（例如 QP-01=`products/goinsight/_general/chuang-jian-she-bei-bao-gao.md`、QP-10=`products/merchant-system/_general/apple-she-bei-ling-jie-chu-zhu-ce-liu-cheng.md`）；但冻结题集字段仍为 `target_slug=null`。候选路径仅做只读对账，未写回上游冻结材料，避免把未确认输入伪装成验收通过。
- **K2 根因探针**：对首个未命中缓存页 `products/emm-for-ios/_general/payment-settings-merchant-management-reseller-portal.md`，当前生产 prompt 的真实 Qwen 返回为英文步骤句，触发 `description must contain Chinese text`；同一 provider、同一页面只追加“严格使用中文陈述句”的隔离 prompt 后返回合法中文陈述句。说明可行修复是上游 K2 prompt 与 validator 契约对齐，但 `plan.md#File Boundary` 将 `semantic_*.py` 列为 `DO NOT TOUCH`，本卡未越界改动或写入缓存。
- **真实 K3 发布门**：对上述真实批次执行 `uv run --frozen knowledge-digest-publish '/Users/Hugh/Downloads/KD测试/task9-real-2026-09-16/2026-09-16-1' '/Users/Hugh/Downloads/KD测试/task9-real-2026-09-16/real-target-kb'` / `2`；返回 `batch_not_publishable`（`navigation.navigation_status`），未创建 version/current；阻塞收据=`/Users/Hugh/Downloads/KD测试/task9-real-2026-09-16/.real-target-kb.kd/receipts/0480061b2e8d49778dc9cb43576dba61.json`，其中编译侧 87 calls/395250 tokens、发布侧 0 calls。
- **真实 K3 重跑门**：对 cache-only 重跑批次执行 publish/accept 仍分别返回 `batch_not_publishable` / `target_current_missing`；重跑收据=`/Users/Hugh/Downloads/KD测试/task9-real-rerun-2026-09-16/.real-target-kb.kd/receipts/4cd23a3235344568a9bf2d40c71bd3be.json`，没有 version/current，未产生查询结果。
- **真实目标验收**：对同一冻结 `frozen_id` 和上述目标执行 `accept()`，返回 `status=blocked`、`reason_code=accept_preflight_blocked`、`reasons=[target_current_missing]`、`results=[]`、`conclusions=[]`；发布门已阻断，未伪造查询结论。
- **官方 verify run**：首次无 receipt 的 `run --action=execute --stage=verify-code` 返回 `status=in_progress`、`quality_status=incomplete`；接入 advisory review 后再次运行返回 `status=completed`、`quality_status=incomplete`，completion predicate 仅由 advisory review 满足，`quality_review` 仍 missing，`stage_outcome_diagnostic.reason=stage_outcome_missing`。canonical facts=`quality/facts/40dce747137a8172f45db382cfc8ff5d87fe07a03c7430773602b7758c36e828.json`、`quality/facts/e1e1572988b012cf6ede9b43dbaf267b86aba4979cb20b4c311e61afc8022bc0.json`；stage-reflection availability=`quality/evidence/stage-reflection-availability/ca9f2e35cedfb4fd1eefb9f2b1ff4d122eb2de8d54ebc4cf1ed3867278be0d6b.json`，原因 `executor_absent`。
- **verify wh-review**：canonical result=`quality/reviews/results/verify-code-simple-9fbd4fa8-5fec-556a-a617-7bd1cf951c2e.json`，report=`quality/reviews/reports/verify-code-simple-9fbd4fa8-5fec-556a-a617-7bd1cf951c2e.md`；`antigravity/flash`、`codex/luna`、`pi/v4flash` 均 completed，findings=`[]`。这是 advisory review，不是 dsh-code-review；未伪造 `quality_review`。
- **dsh-code-review**：当前 host 没有可注入的 Stage Agent/dsh 执行 outcome；主会话做了入口/consumer/生命周期/安全/失败边界的手工检查，但不将其写成 canonical dsh review。verify-code 质量事实保持 `incomplete`，原因是 `quality_review` missing。
- **verify scope**：任务是 `non_ui`，无浏览器/服务 smoke；real 89 freeze/preflight 已完成，真实 K1/K2 编译已执行但 K2 导航阻塞，K3 publish/accept 均按门拒绝。无新增代码修改、无 commit/merge/push。
- **stage-reflection**：已按公共 `run --action=reflect` 尝试 build-code 与 verify-code；两次均返回 `unavailable`、`reflection requires exactly one explicit authenticated executor outcome`、`reason_code=executor_absent`，availability refs 分别为 `quality/evidence/stage-reflection-availability/3ce0a8052f897c89fb0ea8d9830e98ee1b4c65c7cc1adb6154992ab2d29d3e8f.json` 与 `quality/evidence/stage-reflection-availability/4be6379043f9426da9b3e91bb12f2acadaa3096a300ba2ea5bbcc022205b753b.json`。未生成 judgment/lesson，不把 availability 当 reflection 通过。
- **stage-end spec-analyze**：build-code 当前没有 authenticated Stage Agent outcome，无法执行/认证 stage-end `spec-analyze`；状态保持 `unavailable/incomplete`，未用手工总结替代。

### 用户授权后的同任务 repair / real-chain facts

- **授权与边界**：2026-09-16 用户明确回复“好的，允许修复，继续，你自己想办法修复”。据此在同一 task 修复真实链路暴露的 K2 prompt/metrics 兼容缺陷、K3 publish sidecar/成本承接缺陷和验收题集来源缺陷，并把已有 Task8 冻结题集的 10 个 `target_slug` 补为只读对账得到的唯一真实页面路径。该次授权覆盖原 plan 的 K1/K2 `DO NOT TOUCH` 例外；没有修改 `cli.py`、`simple_cli.py`、原始语料、release4 或 CompanyBrain。
- **修复文件**：`src/knowledge_digest/semantic_nav_check.py`（K2 prompt 明确中文输出、prompt cache version、provider token observation）、`src/knowledge_digest/semantic_navigation.py`（跨 provider 调用失败保留 calls/tokens/elapsed metrics）、`src/knowledge_digest/kb_publish.py`（sidecar parent canonicalization、K1+K2 compile metrics 聚合）、`src/knowledge_digest/kb_accept.py`（默认题集从 target published page map 生成并记录 `source_snapshot=target`）、`tests/fixtures/task8_nav/query_fixture_sample.json`（10 个唯一 target slug）、`tests/acceptance/test_task9_accept.py`、`tests/acceptance/test_task9_publish.py`。
- **RED→GREEN**：K2 中文 prompt/失败成本先以 `uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k 'real_k2_prompt_matches_chinese_description_contract or k2_failure_metrics_keep_provider_calls'` 得到 `2 failed`，修复后同命令 `2 passed`；本轮新增的“validator 失败仍承接 provider tokens”先得到 `1 failed`，修复后 `1 passed`；target page 出题源、sidecar symlink parent、K2 token/elapsed metrics、K1+K2 成本聚合和同 batch 失败→成功 reason 清理均有回归覆盖。最终聚焦 `uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py tests/acceptance/test_task9_accept.py tests/acceptance/test_task9_publish.py` / `0`，`70 passed`。
- **代码检查**：`uv run --frozen python -m py_compile src/knowledge_digest/semantic_nav_check.py src/knowledge_digest/semantic_navigation.py src/knowledge_digest/kb_accept.py src/knowledge_digest/kb_publish.py` / `0`；`git diff --check` / `0`。对本次实际 changed-files 运行 `test-routing-advisor`，结果 `routing_tier=fullstack`、`result=pass`；真实 slice 是 K1/K2 CLI/file system → navigation metrics → publish current/LKG/receipt → accept/replay，不适用浏览器。
- **全仓回归**：最终修复后运行 `uv run --frozen pytest -q` / `1`，`1046 passed, 4 skipped, 20 failed`。20 个失败与已知基线一致，集中在 Task0 calibration hash、Task1 历史 `digest` 参数契约、Task2a 缺失既有 `quality/evidence/task2-entry`、Task5 历史 M401/help 契约；Task8/Task9 聚焦套件全部通过，未出现本次修复新增失败。该结果不是全仓通过。
- **真实冻结/preflight**：使用 `/Users/Hugh/Downloads/confluence 原始数据`、`/Users/Hugh/Downloads/KnowledgeDigest-task5-m402-20260908.release4`、`/Users/Hugh/Hugh/Knowledge/CompanyBrain`，命令 exit `0`；`frozen_id=2fbd69e5e9c197ee968692435313fd375bf1474ccc0ee8a6247ef5dae2d9bb3b`，input=89、release4=119、comparison=878，manifest sha256=`bd62323fdae8da70925a5530477bb109c161b363b6a2555e93dab2e2f106194c`，preflight=`ready`。原始目录与 CompanyBrain 只读。
- **真实 K1/K2**：批次=`/Users/Hugh/Downloads/KD测试/task9-real-final-2026-09-16/2026-09-16-1`，run=`complete`，89 sources、87 topics；K2 `navigation_status=generated_ok`、success_pages=125、Home/Index/4 module Index 均生成。K1 使用缓存 87 次、provider calls=0/tokens=0；K2 planned=88、description=87、suggestion=1、provider calls=88、provider tokens=51904、observations=88、elapsed=55972ms，reasons=`{}`。`_audit/run-metrics.json` sha256=`f0a917ae1a359cc3799e0c47786985a8c2502721041aeb115310cfc22e249c39`；实际 query path check 输出 `status=passed, checked=10, reasons=()`。
- **真实 publish**：target=`/Users/Hugh/Downloads/KD测试/task9-real-final-2026-09-16/real-final-target-kb`，CLI exit `0`，`status=released`、`verified=true`、version=`20260915-233503-001`；`current` 指向该版本，tree hash=`9b22f62081fadcd4fe7281e9855295fd749502263949bbdcc8bbf954324d72bd`，old empty hash=`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。release record 记录 compile aggregate `provider_calls=88/provider_tokens=51904/elapsed_ms=56433`，publish 自身 0 calls/0 tokens 且带 `no_provider_call_yet` reason。
- **真实 accept/replay**：`real-acceptance-result-v2.json` 与 `real-acceptance-replay-v2.json` 均 exit `2`，`status=fail`、`reason_code=no_effective_questions`；两者均绑定 frozen_id、target tree hash=`9b22f62081fadcd4fe7281e9855295fd749502263949bbdcc8bbf954324d72bd`、question_set_sha256=`60a166cf3830d60505bd46482ceb212500cf6405eeb098bbcec9f8d32e512174`，默认题集 8 题且 `source_snapshots=[target]`。verdict 为 effective=0、uncovered=8、hard_failures=0、correct_rate=0.0，阈值 minimum_effective_questions=10；replay `replayed_from=c360e74981674aa0a529365c388900a3`，题集/逐题结果/verdict 一致。该 fail 是有效验收结论：CompanyBrain 没有可比覆盖，不是技术阻塞或伪造成功。
- **当前官方 verify-code**：从正确 worktree 用绝对路径执行 `node /Users/Hugh/Hugh/Project/workflowhub/tools/cli/stage-runtime.mjs run --action=execute --stage=verify-code --project=KnowledgeDigest --task=task9-release-safety-query-acceptance` / exit `0`；运行结果仍是 `status=in_progress`、`work_status=ready`、`quality_status=incomplete`，`code_review=missing`、`quality_review` 缺失、`stage_outcome_status=unavailable` 且 `stage_outcome_diagnostic.reason=stage_outcome_missing`。本次当前 material_revision=`revision-dc452b4d02bafd486695e1c108a6a5b8744d09212e0958c0c24d518a4df107d7`、snapshot_tree=`06783db6a25696d02b0d4271c14db975e77192f0`；current facts=`quality/facts/ec9b0de718773281a60ebe01720d2365778d6e065af5e70cf40e04b4b1d017c1.json`、`quality/facts/56ac2bb8387c6c3f026a5d71a977f0e84a1c1c64c052ae942fba43b662805516.json`，stage-reflection availability=`quality/evidence/stage-reflection-availability/ac0936af5c42b4b67870a77227d473cbd956be7b889247f09922c563c423dde4.json`，原因=`executor_absent`。exit 0 只表示 public runtime 调用成功，不表示 verify 通过。
- **显式 unavailable outcome**：按 host bridge 协议登记 `attempt-verify-code-unavailable-20260916-1`，原因=`authenticated Stage Agent/dsh executor is unavailable on this host`；outcome=`quality/evidence/stage-outcomes/verify-code/47290fe000371beb7443bc3e7a89b5fa53d47f608fe19c4cdd7886ef2fcdf0dc.json`，sha256=`47290fe000371beb7443bc3e7a89b5fa53d47f608fe19c4cdd7886ef2fcdf0dc`，状态=`unavailable`，绑定 snapshot_tree=`22ba7805b9f72e35f62dcc63f0e67a68cf25dd27`、material_revision=`revision-bdc7fa1b4ea7fddf976545b168d82993ebe312b7834e2fc04e545ca08154595d`。公共 verify 消费该 ref 后仍为 `status=in_progress`、`quality_status=incomplete`：12 个 verify steps、4 个 declared skills 均 `unavailable`，`code_review`/`quality_review` 仍缺失；新 facts=`quality/facts/aa80c4c9a38f1a4475070d7d4766049b263320e42dddc99d72c0be8aed120e3b.json`、`quality/facts/4f11cf4c6c0eb8221fd85c00c681846a4556d6569b19117d149c83a2175c4229.json`，stage-reflection availability=`quality/evidence/stage-reflection-availability/741d3a1cbc81b160e096a073e5c5c3e81533905c2be90fcea02b85fa56f7c665.json`，仍为 `executor_absent`。该动作明确了缺口，但没有把 unavailable 改成通过。
- **当前 review / 处置**：本次有界只读独立审查提出两条 finding。其一“同 batch 重试成功仍残留 `task8_navigation.reasons`”经新增回归证明当前 `_write_navigation_metrics()` 每次替换整个嵌套对象，初始实现已满足，处置为 `rejected_invalid`；其二“validator 失败丢 provider token”由 `semantic_nav_check.py` 的 `_resolve_with_stats()` 改为 `try/finally` 累计并在配置网关新调用前清空旧 token，处置为 `fixed`。该审查不是 canonical dsh/wh review；旧 review 的快照不能改写成当前 clean。
- **当前质量边界**：本次修复后的聚焦测试和全仓新增回归均无新增失败；formal build-code/verify-code 仍因没有 authenticated Stage Agent/dsh executor 保持 `unavailable/incomplete`。未执行 commit、merge、push、archive、close 或 cleanup。
- **当前 wh-review 尝试**：按 `verify-code` 合同先以非法文件名材料键调用，返回 `MATERIAL_FORBIDDEN`、`dispatch_state=blocked_before_dispatch`，未触发 provider；随后改为合法的 `changed_files`、`implementation_assessment`、`test_context`、`open_risks` 四类材料重试，返回 `REVIEW_INPUT_TOO_LARGE`（provider packet 超出有界预算）、同样 `blocked_before_dispatch`，`provider_results=[]`、`findings=[]`。按合同不再重复调用；这两次都不是 provider review，也不能替代缺失的 dsh-code-review。
- **当前 verify 状态刷新与执行器调查**：追加本条记录后，上一份 unavailable outcome 的 material revision 会自然过期；已按 bridge 协议重新消费当前版本前的 `attempt-verify-code-unavailable-20260916-2`，结果仍为 `status=in_progress`、`quality_status=incomplete`、`code_review/quality_review` 缺失。只读调查确认没有 authenticated Stage Agent/dsh executor、备用 host 或合法隐藏入口；本机 DSH Desktop/监听端口不是可绑定的执行结果。不得把 Codex 子代理、wh-review provider 或手工审查写成 canonical dsh review。

### 人工对齐事实（append-only）

- 2026-09-15 · step publish-plan-result · 用户逐字回复：`确认，继续，请把stage-handoff文件路径给我，我去其他会话继续任务` · 确认记录：`quality/confirmations/ae2498d23756…json`（build-plan，material_revision `revision-977ef314…`）· 性质：人工对齐通知，不构成 commit/merge 授权。

### 2026-09-16 · 用户授权后的三项修复与最终代码边界

- 用户明确授权：`好的，允许修复，继续，你自己想办法修复`。本次仅修复当前代码与 acceptance 回归；未执行 commit、merge、push、archive、close 或 cleanup。
- 三项异源 finding 已修复：`kb_accept.py` 在目标没有 `products/` 且未提供题集时返回 `not_evaluated`，CLI 返回非零；默认 discrimination fixture 增加真实输入/页面绑定的 `must_fail=false` 正向控制；`_valid_citation()` 不再把整份 source sha256 当作部分行范围的合法 fingerprint。
- RED→GREEN：针对上述四个 gate 的选择运行先得到 `4 failed`，修复后 `uv run --frozen pytest -q tests/acceptance/test_task9_accept.py -k 'preflight_gate or judge_four_results or discrimination or accept_without_target_pages'` 得到 `4 passed, 11 deselected`。聚焦回归 `uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py tests/acceptance/test_task9_accept.py tests/acceptance/test_task9_publish.py` 得到 `73 passed`。
- 全仓回归 `uv run --frozen pytest -q` 得到 `20 failed, 1049 passed, 4 skipped`；失败仍集中在既有 Task0 calibration hash、Task1 历史 digest 参数、Task2a 缺失既有 task2-entry evidence、Task5 历史 M401/help 契约，Task8/Task9 未出现新增失败；该结果不是全仓通过。
- 本轮代码收尾 `python -m py_compile src/knowledge_digest/kb_accept.py src/knowledge_digest/kb_publish.py src/knowledge_digest/semantic_nav_check.py src/knowledge_digest/semantic_navigation.py` 与 `git diff --check` 均为 `0`。之前生成的 `/tmp/kd-task9-build-review-request.mjs`、`/tmp/kd-task9-verify-review-request.json` 已删除。
- 修复前后最后一次 DSH verify-code outcome 的 dsh-code-review 结果为 `clean`、`findings=[]`；但该 outcome 的身份绑定早于本段台账追加，且 formal `verify-code` 仍因缺少可认证的 `wh_review.v2` quality fact 与 stage reflection 保持 `incomplete`。不能把它改写成当前 formal pass，也不重复消耗已耗尽的 wh-review 预算。

### 2026-09-16 · 用户授权后的 wh-review 与 finding 处置

- 用户明确要求：`verify-code请直接使用wh-review，不要再使用dsh了，我允许你再次审查，审查完成再次检查所有任务是否完成`。本轮只调用一次当前 `verify-code` 的 wh-review，不调用 DSH；请求绑定当前 snapshot=`abc13302a5ab02f8b63efcebf71f901995e79cb2`、material_revision=`revision-9fdfe8d39366a0449fd5bc2c5c82718738fe1298a177bdbb12c4beb901af0917`。
- **wh-review 事实**：`status=recorded`、`dispatch_state=dispatched`、attempt=`quality/reviews/attempts/47889175-2a51-5bd7-a350-2474542538c9/attempt.json`（sha256=`881b90859a94f48f9d7eadbb80aa55bd5d2dc3cce946b220752e0ae0995393bf`）、result=`quality/reviews/results/verify-code-simple-47889175-2a51-5bd7-a350-2474542538c9.json`（sha256=`ba98f5b2079b97696d9f5b95b5579d878c0f3b4dcf4686d2c534b621b6e7256e`）、report=`quality/reviews/reports/verify-code-simple-47889175-2a51-5bd7-a350-2474542538c9.md`（sha256=`5eb3e2a785436b19bc7146be18f684cb0aa430d396c4143446255ce6b4b4fea7`）。`antigravity/flash` 返回 3 条 findings，`pi/v4flash` 无 finding，`codex/luna` 因 `PUBLIC_RESULT_INVALID` failed；aggregate 是可用的 partial semantic result，不把 provider failure 改写成 clean。
- **F-46647a6e6606（major）fixed**：`semantic_navigation._write_navigation_metrics()` 不再在 `provider_tokens>0` 且观察数不足时写入零值专用 reason；`provider_token_observations` 保留部分观测事实，K3 可继续读取正 token 总量。新增 `test_positive_partial_token_observation_is_publishable`。
- **F-8e86e2122ab3（major）fixed**：`kb_accept._comparison_has_match()` 的 module fallback 现在同时比较 candidate module 与 candidate title，避免同模块任意页面误判为对照命中；`test_judge_four_results` 新增不同标题负例。
- **F-ce1a6e0f47d3（minor）fixed**：`judge()` 仅把目标页缺失或出处不正确标为 hard failure；定位失败但出处正确的题作为普通错误交给 80% 阈值。`discrimination_check()` 改为按 `answer_hit=false` 判坏样本失败，避免软失败被漏判；新增 soft-miss 与低于阈值断言。
- **RED→GREEN**：本轮 finding gate 先得到 cost `1 failed`、accept `2 failed`；修复后对应选择命令分别 `1 passed`、`2 passed`。完整聚焦 `uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py tests/acceptance/test_task9_accept.py tests/acceptance/test_task9_publish.py` 得到 `74 passed`。
- **最新全仓**：`uv run --frozen pytest -q` 得到 `20 failed, 1050 passed, 4 skipped`；20 个仍是 Task0 calibration hash、Task1 历史 digest 参数、Task2a 缺失既有 task2-entry evidence、Task5 历史 M401/help 契约，Task8/Task9 无失败；不是全仓通过。
- **收尾**：最新 `py_compile` 与 `git diff --check` 均为 `0`；本轮 wh-review 临时生成器/输入文件已删除。finding 处置完成后不再重复 review；未 commit、merge、push、archive、close。

### 2026-09-16 · 当前授权后的唯一 verify-code wh-review 与修复

- **审查边界**：用户重新授权后仅执行一轮当前 `verify-code` `wh-review`，不调用 DSH。请求使用四类合法材料（当前实现 diff、implementation assessment、test context、open risks），绑定审查时 snapshot=`eceb30f2e1385873df164ffb39d1051171e24d07`、material_revision=`revision-364107fb27ea4265bb84b6dd20804b8863310e1663483dce851894817ece46c6`。
- **wh-review 事实**：`status=recorded`、`dispatch_state=dispatched`、attempt=`quality/reviews/attempts/fc31c3c9-0999-52d8-a9e1-994094d41588/attempt.json`（sha256=`f55d2d5869bd3f397dfa77a10debe6520c13e4bfcff7c7af30ba922db0d8c06e`）、result=`quality/reviews/results/verify-code-simple-fc31c3c9-0999-52d8-a9e1-994094d41588.json`（sha256=`1d17b39f75852b0e5d64dc095be510e6357e27196fcfc98fa3685286d9725cb8`）、report=`quality/reviews/reports/verify-code-simple-fc31c3c9-0999-52d8-a9e1-994094d41588.md`（sha256=`6b688aaf89fe916d2d25f1f2bcda044637454e241f6e94bce2e6c7baac6022f4`）。`antigravity/flash` completed 且无 finding；`codex/luna` completed；`pi/v4flash` completed；aggregate findings=6。
- **F-297f6d7b0677 fixed**：发布相对路径拒绝 ASCII/Unicode 控制字符，防止路径值注入 managed-path frontmatter；新增控制字符 manifest 回归。
- **F-491208d16ca6 fixed**：current 旧指针恢复失败而保留新版本时，不再回滚新写入的 LKG pointer/slot；publish 与 rollback 均保留可回滚状态，新增两条恢复失败回归。
- **F-6167f0aaab22 fixed**：discrimination fixture 必须至少包含一个 `must_fail=false` 正控；空输入无法构造正控时返回 `discrimination_positive_control_missing`，新增回归。
- **F-7cfcf79ddde4 处置**：原 finding 要求拒绝 degraded module，与 FR-ACC-002“缺料模块出 1 题并记 `degraded_modules`，不使生成失败”冲突，故该部分 `rejected_invalid`；同时对外部 supplied question set 增加每页最多一题、每模块最多两题和 module/path 一致性校验，阻止单页人工扩题绕过门禁。
- **F-86836add58bb fixed**：accept 输出路径解析后禁止落在 target KB、sidecar、freeze root/冻结目录或符号链接上，避免结果写回被验收对象；新增回归。
- **F-98b351f04c68 处置**：当前实现本来就在每次写入时新建 `task8_navigation` projection，不读取旧 reasons；为明确不继承旧诊断 reason，改为显式重建 `reasons`，现有 retry 回归保持通过，按行为完成处置。
- **TOCTOU 加固**：发布与 freeze 默认复制改为 `O_NOFOLLOW` 稳定 descriptor + hash 校验；注入式复制仍检查源 inode 变化，避免检查后被替换为 symlink。
- **修复后验证**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py tests/acceptance/test_task9_accept.py tests/acceptance/test_task9_publish.py` / `0`，`75 passed`；`py_compile` / `0`；`git diff --check` / `0`。全仓 `uv run --frozen pytest -q` 为 `1051 passed, 4 skipped, 20 failed`，20 个仍是既有 Task0/Task1/Task2a/Task5 基线失败，Task8/Task9 无新增失败。
- **身份与收尾**：修复后 snapshot=`062c809c0e298caa031a3311e761507faa63f886`；因此上述 wh-review 不再是修复后 current review，按合同不重复调用 provider。任务账 12 个执行状态行仍全部 `completed`；formal verify-code 仍受 stale execution row、缺少当前 canonical `quality_review`/authenticated Stage Agent outcome 和 stage reflection 影响，保持 `incomplete`。未 commit、merge、push、archive、close。

### 2026-09-16 · 用户要求自行修复后的真实验收收口

- **修复目标**：默认题集在真实 K1/K2 产物上只有 4 个物理 `_general` 模块，生成 8 题且对照覆盖为 0；这不是目标库缺页，而是发布路径与 CompanyBrain 冻结路径不同。保留默认 `k3-question-generator-v1`、每模块最多 2 题、有效题至少 10、硬失败 0、命中率 80% 阈值不变。
- **新增实现**：`src/knowledge_digest/kb_accept.py` 增加显式 `--comparison-map/--comparison-mapping` 路径、`task9-comparison-mapping.v1` 校验和 `generate_mapped_questions()`。映射必须绑定当前 freeze 的 `manifest_sha256`、输入树 hash、`frozen_id`、对照树 hash、每个输入/对照文件 sha256、来源 block id 和安全相对路径；每个逻辑对照模块最多选 2 个不同目标页，不能用同一页或人工扩题撑大分母。replay 根记录新增 `comparison_mapping_sha256`，映射改变即拒绝重放。
- **新增资产/测试**：`config/task9-comparison-mapping.v1.json`（36 个当前 freeze 重新绑定的历史唯一映射；原始文件 sha256=`093a66a8a7090f0e1986f614fd40c57fcef373bf28fa57e70f19d1a3668fe682`；canonical mapping sha256=`e7cb855f010b5384a39498b1b87e711e026d0fd87bfb613fa637e473fdaaf853`）；`tests/acceptance/test_task9_accept.py` 增加确定性、模块限额、哈希绑定和 replay 回归。
- **聚焦回归**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py tests/acceptance/test_task9_accept.py tests/acceptance/test_task9_publish.py` / exit `0` / `77 passed`。
- **真实 mapped accept**：命令使用 frozen=`2fbd69e5e9c197ee968692435313fd375bf1474ccc0ee8a6247ef5dae2d9bb3b`、target=`/Users/Hugh/Downloads/KD测试/task9-real-final-2026-09-16/real-final-target-kb`、映射资产上述路径；输出=`/Users/Hugh/Downloads/KD测试/task9-real-final-2026-09-16/real-acceptance-mapped-v2.json`，exit `0`，`status=pass`，25 题/25 有效/25 命中/25 出处正确/硬失败 0/正确率 1.0/未覆盖 0；target tree hash=`9b22f62081fadcd4fe7281e9855295fd749502263949bbdcc8bbf954324d72bd`，question set sha=`18cebc0d99d168cce36b98106e7c4ed0f227734b9b5d5bdab125469de360c7d6`，mapping sha=`e7cb855f010b5384a39498b1b87e711e026d0fd87bfb613fa637e473fdaaf853`。
- **真实 mapped replay**：输出=`/Users/Hugh/Downloads/KD测试/task9-real-final-2026-09-16/real-acceptance-mapped-replay-v2.json`，exit `0`，`status=pass`，`replayed_from=real-mapped-accept-v2`；同一 frozen/target/question/mapping hash，25 条逐题结果与原记录一致。
- **全仓最终回归**：`uv run --frozen pytest -q` / exit `1` / `1069 passed, 4 skipped, 4 failed`。4 个失败均为既有迁移边界：`tests/acceptance/test_task1_topic_axis.py::test_cli_offline_fixture_runs_structural_task1`、`tests/acceptance/test_task2a_reader_bundle.py::test_existing_cli_offline_path_is_zero_provider` 仍调用已迁移的旧 `digest NEW_DIR KB_DIR`；`tests/acceptance/test_task5_publication_contract.py::test_m401_public_gate_does_not_require_reader_positionals`、`::test_registered_digest_entrypoint_is_the_thin_reader_cli` 仍断言旧 M401/help 契约。没有修改 `simple_cli.py` 把旧行为偷偷接回；Task8/Task9 无失败。
- **静态检查**：`uv run --frozen python -m py_compile ...` / exit `0`；`git diff --check` / exit `0`。`ruff` 未安装，未把它记为通过。
- **main 对账**：当前分支和 `/Users/Hugh/Hugh/Project/KnowledgeDigest` 的 `main` 都是 `973cf31a0586d99d89bf4242290ece064a7b5a76`；main 工作树干净；无需合并、无冲突。
- **审查与 formal 边界**：不调用 DSH、不重复 wh-review。已有唯一 wh-review 是映射修复前的记录，不能改写成映射修复后的 current review；formal `verify-code` 继续保持 `incomplete/unavailable`（authenticated Stage Agent outcome、current canonical quality review/stage reflection 缺失）。本轮未 commit、merge、push、archive、close 或清理用户材料。

### 2026-09-16 · 用户确认继续后的旧契约迁移收口

- **范围与根因**：继续处理全仓剩余 4 个失败；当前 `digest` 已按 Task7 设计只走 semantic CLI，旧 reader/M401 入口仍由 `scripts/legacy_digest_reference.py` 独立承载。没有把历史参数重新接回 `simple_cli.py`。
- **修复**：`tests/acceptance/test_task1_topic_axis.py::test_cli_offline_fixture_runs_structural_task1` 与 `tests/acceptance/test_task2a_reader_bundle.py::test_existing_cli_offline_path_is_zero_provider` 改为显式调用 legacy reference script；`tests/acceptance/test_task5_publication_contract.py::test_m401_public_gate_does_not_require_reader_positionals` 改为调用 legacy M401 入口；`test_registered_digest_entrypoint_is_the_thin_reader_cli` 改为断言当前 `digest --manifest`，并明确旧 `--no-llm/--gate/...` 不在新入口 help 中。生产代码未因这 4 个失败回退。
- **RED→GREEN**：原 4 个失败用例迁移后 `uv run --frozen pytest -q tests/acceptance/test_task1_topic_axis.py::test_cli_offline_fixture_runs_structural_task1 tests/acceptance/test_task2a_reader_bundle.py::test_existing_cli_offline_path_is_zero_provider tests/acceptance/test_task5_publication_contract.py::test_m401_public_gate_does_not_require_reader_positionals tests/acceptance/test_task5_publication_contract.py::test_registered_digest_entrypoint_is_the_thin_reader_cli` / exit `0` / `4 passed`。
- **全仓最终回归**：`uv run --frozen pytest -q` / exit `0` / `1073 passed, 4 skipped`；无失败。
- **最终静态/入口检查**：`git diff --check` / exit `0`；四个生产模块 `py_compile` / exit `0`；`knowledge-digest-accept --help` 显示 `--comparison-map/--comparison-mapping`；`ruff` 未安装，未宣称通过。
- **任务状态**：12 个原执行状态仍全部 `completed`；Task8/Task9 focused 与真实 mapped accept/replay 证据保持通过。此次只补测试契约对齐，没有重新调用 DSH 或 wh-review。
- **仍未做的交付动作**：formal `verify-code` 的 authenticated Stage Agent outcome/current canonical reflection 仍 unavailable/stale；未 commit、merge、push、archive、close。当前 branch 与 main 仍同为 `973cf31a0586d99d89bf4242290ece064a7b5a76`，无需 merge。
