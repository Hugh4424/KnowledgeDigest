# HANDOFF · task9-release-safety-query-acceptance（K3：安全地交出去）

> **当前状态入口（2026-09-16）**：本文保留 build-plan 阶段历史快照；继续执行请优先读取任务共享目录的 [canonical handoff](/Users/Hugh/Hugh/Knowledge/Projects/KnowledgeDigest/tasks/task9-release-safety-query-acceptance/.agenthub/handoff/handoff-verify-code-current-20260916.md)，其中已记录用户授权后的修复、最新测试、main 对账和当前外部阻塞。

> 交接给新会话继续 **build-code** 阶段。本文件是唯一交接入口；材料以 specs 目录四件套为准。

## 1. 任务身份

- **任务**：task9-release-safety-query-acceptance = 母任务 task6 PRD 的 K3 卡（发布安全 + 真实查询集验收）
- **worktree**：`/Users/Hugh/Hugh/Project/KnowledgeDigest-task9-release-safety-query-acceptance`（分支 `task/KnowledgeDigest/task9-release-safety-query-acceptance`，基线 `973cf31`）
- **任务记录（质量库）**：`/Users/Hugh/Hugh/Knowledge/Projects/KnowledgeDigest/tasks/task9-release-safety-query-acceptance/`
- **WorkflowHub**：`/Users/Hugh/Hugh/Project/workflowhub`（CLI：`node tools/cli/stage-runtime.mjs ...`）
- **上游已交付**：K1=`specs/archive/task7-semantic-layer-compiler/`、K2=`specs/archive/task8-entry-navigation/`（均只读）

## 2. 已完成阶段（均按标准 WorkflowHub 流程，无跳步）

| 阶段 | 状态 | 关键事实 |
| --- | --- | --- |
| make-decision | **approved**（用户确认"确认，这个方向就定了"） | decision-log.md（28 条 R 全收敛、D-001…013、AC-K3-1…5、16 OI 全 confirmed）；确认记录 `quality/confirmations/f99974ae…json` |
| build-spec | **frozen** | spec.md（29 FR/5 AC/12 场景；C1–C5 用户口径冻结；tree hash 算法 FR-PUB-008 已冻结） |
| build-plan | **confirmed**（用户确认"确认，继续…"） | plan.md + tasks.md（6 相位 21 对 RED/GREEN + 1 聚合卡）；确认记录 `quality/confirmations/ae2498d23756…json`（revision-977ef314…，snapshot c57a6e40…） |

**阶段关键方向**（全部有用户真实答复背书，不得回退）：整库原子换版+库根 `current` 符号链接固定入口；合并=库内原有内容+本批（未声明路径保留、碰撞硬失败、证据页逐字节复制）；托管判定只对照 `kb.structure.md`（本批页面集先**登记进声明**）；LKG/记录/收据/staging/冻结全部在库外同级隐藏目录 `.<库名>.kd/`；失败成本三项真实且承接编译侧；问题集每模块 2 题×3 模板机器生成（**RISK-K3-2：与母任务 OPEN-002/ADR-0014 冲突，用户明确维持**，随材料携带不静默）；汇总=硬失败 0+命中率≥80%+未覆盖不计分；三类坏样本各绑 2 必失败题；no-op 允许；**不接 gbrain/检索层/不写既有 1347 页知识库/无人工闸门/发布验收不调 LLM**。

## 3. 新会话怎么开工（build-code）

1. `cd /Users/Hugh/Hugh/Project/KnowledgeDigest-task9-release-safety-query-acceptance`
2. 先读（按序，别跳）：本文 → `specs/task9-release-safety-query-acceptance/tasks.md`（材料导航+开工 gate+RED/GREEN 纪律）→ `plan.md#File Boundary` 与 `#Technical Decisions` → 首卡 T001R 所需 spec 节。
3. 执行纪律：严格 RED→GREEN（RED 先行提交、非零预期；同 gate_cmd 同 oracle identity）；权威命令 `uv run --frozen pytest -q`；每卡回填 tasks.md 执行状态区（唯一完成权威）。
4. 阶段入口照标准流程（读 workflowhub `workflows/build-code/SKILL.md`）；本会话无宿主 Stage Agent bridge，官方 outcome 记 `unavailable（executor_absent）` 属正常，不阻塞继续干活，不伪装。

## 4. 硬边界（违反=返工）

- **DO NOT TOUCH**：digest 三个 CLI（cli/simple_cli/semantic_cli）、semantic_*.py（K1/K2）、full_release.py、publisher.py、lock.py、kb_structure.py（仅 import）、K1/K2 全部测试、CONTEXT.md、docs/、CompanyBrain、gbrain、真实语料目录。唯一 MODIFY：`pyproject.toml` +3 脚本行（T001G，先 `uv sync`）。
- **不得改动冻结口径**：阈值 80%/硬失败定义、题数与模板、坏样本三类、tree hash 算法（FR-PUB-008）、三入口结构、sidecar 命名（DEC-K3-005）。要改=回 make-decision 增量裁决。
- **不 commit/merge/push**（含验收后的清理）——每次都要用户当场授权。
- 崩溃级一致性（掉电/SIGKILL）不做（FR-NEG-002）；不承诺多格式输入/检索层。

## 5. build-code 之后

- **verify-code**：含 clarify C5 定时点——**真跑一次 89 份冻结语料的 K1/K2 编译→发布→验收全链路**（provider 用项目约定 Qwen/jina；成本计入 AC-K3-2 账）；RISK-K3-4 提醒 provider 可用性要在 plan 执行期确认。
- 真实冻结语料：`/Users/Hugh/Downloads/confluence 原始数据`（89 份 .md，1.4MB）；改造前快照 `…/KnowledgeDigest-task5-m402-20260908.release4`（108 md）；既有知识库 1347 md（只读对照，排除 `_gbrain/` 与点文件）。
- 坏样本/题集 fixture 归 P5/P6 卡（task9_publish fixture 模块内构造）。

## 6. 当前 git 状态

worktree 仅 `?? specs/task9-release-safety-query-acceptance/`（决策+规格+计划+任务清单+9 份审查证据，全部未提交）；**未授权提交**。

## 7. 上下文控制建议（沿用前三阶段做法）

- 审查/取证全派子代理（本任务已用 8 个：取证 2、方向/规格/计划审查 6），主会话只保留结论+文件路径+hash。
- 材料全文不用重读：tasks.md 材料导航表标了 M/S/B/P 读取时机。
- 子代理一律限时收口（4 分钟），宁少而真。

---
生成：build-plan 阶段收尾 · 2026-09-15 · 生成后即静态，后续阶段产物另行登记。
