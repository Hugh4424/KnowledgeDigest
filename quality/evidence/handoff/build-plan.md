# Stage Handoff · task8-entry-navigation / build-plan → build-code

> 按 stage-handoff 技能合同（v1.0.0）生成；current view，原子覆盖，不替代四材料/stage outcome/reflection。
> 状态事实：本会话无外部 Stage Agent 宿主，stage outcome / reflection 全程 `unavailable`
> （stage_outcome_missing / executor_absent）——原样可见，不构成质量缺口。

## 1. 任务身份

| 项 | 值 |
| --- | --- |
| task_id | `task8-entry-navigation`（K2 入口与导航，母任务 PRD 第二张卡） |
| worktree | `/Users/Hugh/Hugh/Project/KnowledgeDigest-task8-entry-navigation` |
| branch | `task/KnowledgeDigest/task8-entry-navigation` |
| HEAD（本会话终态） | `d5893c0`（worktree 干净） |
| 上游基线 | `main @ a3fe464`（已 merge 进本分支，merge commit `361114e`） |
| 四材料 | `specs/task8-entry-navigation/{decision-log,spec,plan,tasks}.md`（decision approved / spec frozen / plan frozen / tasks 42 卡） |

## 2. 背景与目标

K1 把 89 份冻结语料编译为批次页面（已合并主干），但读者无入口：基线 87/99 无入口、95/99 同质。
K2 在同一批次内生成三层导航（Home.md → Index.md → 模块 Index.md），模型写每页描述句，
机器自检两道门（零孤儿覆盖判定 / 描述四判据）+ N=10 路径抽查，全绿才落盘并增写 manifest
`navigation` 机读节；任一红 = blocked 不产出导航。产物是结构门，不是知识可用性证据（归 K3）。

## 3. 当前阶段与进度

- make-decision ✅ approved（三轮 Talk 19 项答复；direction+detail 双审查 26 findings 全处置）
- build-spec ✅ frozen（15 步官方链；review 11 findings 全处置；K1 合并后已对齐真实 schema）
- build-plan ✅ frozen 已发布（13 步官方链；plan-task.v4 **42 卡**=21 对 RED/GREEN；review 18 findings 全处置；
  DEF-K2-2 十条题目用户已确认冻结；DEF-K2-4 实现参数 DEC-K2-004 已冻结）
- build-code ⬜ 未开工 —— **gate 全关闭，从 T001R 直接开工**
- 外部宿主事实：stage outcome / reflection `unavailable`（executor_absent），如实保留

## 4. 重要决策（冻结，勿重开）

| 决策 | 内容 | 出处 |
| --- | --- | --- |
| 三层结构 | Home.md→Index.md（按 product 分节）→products/<product>/<section>/Index.md→页面；3 跳=点击次数 | decision D-003/R2-Q1 |
| 量化域权威 | manifest pages[] 条目 + 双向路径对账（非计数等式）；保留名 Index.md | spec PFACT-K2-002 |
| 描述四判据 | ①规范化相等容忍=0 ②骨架≥3 ③问句模板≥3 ④空描述即失败；超阈值 blocked | spec FR-CHK-002 |
| 失败处置 | 修复循环轮数=0；blocked=清暂存+navigation_status=blocked+reasons；K1 状态零改写 | spec FR-CHK-004 |
| commit 顺序 | ①三导航文件 ②run-metrics ③manifest navigation 最后写（fail-closed：写失败→K3 凭缺节拦截） | plan B-13 修复 |
| 缓存 | 同格式独立键空间：`cache/model-cache/entries.jsonl`，键前缀 task8-desc:/task8-suggest:；键构成 FR-GEN-003 | plan DEC-K2-002 |
| CLI 挂接 | MODIFY semantic_cli.py：compile_batch 成功后、打印 output 前调 compile_batch_navigation | plan DEC-K2-001 |
| 生产接线 | 三依赖显式注入（cache/gateway/query_fixture），无默认 Null/None | plan review B-2 修复 |

## 5. 核心方案（build-code 落地口径）

单模块 `src/knowledge_digest/semantic_navigation.py`，四职责块按 Phase 推进：
`load_and_validate → reconcile_pages → build_index/build_module_indexes/build_home（机械）→
generate_model_outputs（缓存/拒绝词/非空）→ self_check（覆盖判定+四判据+路径抽查）→
commit_or_block`。对外唯一入口
`compile_batch_navigation(batch_dir, *, cache, gateway, query_fixture) -> NavigationResult`。
测试全离线（DictCache/FakeGateway）；生产 gateway 按 DEC-K2-003 读 `~/.config/knowledge-digest/config.json`。

## 6. 踩过的坑（下一会话别再踩）

1. **CONTEXT.md 合并冲突**：K1/K2 都登记术语——解法=两节并存、K1 在前。下次 K3 同理追加，勿合并改写。
2. **versioned_refs hash 是活的**：每次改 spec/plan 后 tasks.md 里 42 处引用必须重算重同步
   （本会话两次返工：`sha256sum plan.md` → 全局替换）。
3. **K1 缓存不同构**：`ModelCache.get_or_call` 是主题级（topic_key+members），K2 对象不同——
   勿强行复用接口；已决策同格式独立键空间。
4. **基线变了**：merge K1 后 20 failed（旧 15 task2a + K1 入口切换预期破坏 5）——
   守卫断言用 `tests/fixtures/task8_nav/baseline_failures_20.txt`，不是旧数字 16。
5. **spec/plan 里引用旧命名的自描述**会被 grep 误判为残留——写核对记录时用转义或加"（旧命名）"。
6. **macOS sed 的 `$(())` 行号展开**在嵌套引号下易炸——批量改文件用 python，别用 sed 脚本。

## 7. 重要参考调研（已核实，带锚点）

- K1 真实链路：`simple_cli.main → semantic_cli.main(@55) → compile_batch(@1459) → BatchResult(@326:
  output_dir/outcome/attempt_id/provider_calls/cache_hits)`；`_write_audit` 最后落盘 manifest
  （semantic_audit.py @986）；挂接前**全库无 navigation 调用**（已核实）。
- manifest 真实 schema：`task7-page-manifest.v1`，pages[] 条目 = **topic_key、
  page_path、page_paths[]、source_paths[]、block_count、claim_count、block_ids[]、claim_ids[]**；
  source_ledger 条目 source_status 五态（ready/known_empty/duplicate_alias/audit_only/blocked）。
- 页面 frontmatter 16 字段（semantic_page.py @839 构造，@714 渲染硬校验顺序）。
- 缓存条目字段（semantic_cache.py @24-33）：cache_key/model_id/prompt_version/topic_map_version/
  result/created_from_fingerprint；键=composite_cache_key(@178, canonical JSON→sha256)。
- 基线实跑（2026-09-14）：1000 收集 / 20 failed / 976 passed / 4 skipped；K1 新测试 89 个=84P+4F+1S。
- 十条查询路径：`tests/fixtures/task8_nav/query_fixture_sample.json`（frozen，target_slug 待 K1
  真实产出后回填映射）。

## 8. 关键事实与数据状态

- fixture 样例 manifest 必须按真实 schema 构造（T001 Knowledge 已写明字段树）；blocked 第五态进映射表。
- 双跑字节一致（AC-K2-6）：created/updated 取页面 frontmatter 归一化值的最早/最晚；source 固定写
  `batch`；时间戳/批次目录名不进任何产物与缓存键。
- 预算：计划调用=页面数+1（描述=页面数次 + 建议=每批 1 次批量）；无重试（一次即决）。
- run-metrics 补记 K2 成本；navigation 节计数公式 success_pages==页面集、blocked_sources==blockers[]。
- `/Users/Hugh/Downloads/KD测试/` 当前为空——真实冒烟要等 K1 真实跑一次批次后。

## 9. 成功与失败边界

- 成功 = 42 卡全部 RED→GREEN；全量 pytest 20 failed 集合零变化 + 本卡零新增失败；
  七 AC 各有机器 oracle（AC-K2-3 用已冻结清单可执行）。
- 失败（blocked，均须 manifest navigation 记录）：孤儿/死链/指向 manifest 外、描述判据任一、
  路径超跳、模型输出空/拒绝词、K1 非 complete、对账违例、frontmatter 缺三字段、零页面、slug=Index 冲突。
- 越界即失败：写批次目录外、批次内超白名单六项、K2 改写 K1 任何已写字段、新增第 17 frontmatter 字段。
- interrupted（manifest 损坏）：K2 不写 manifest，显式报告退出——K3 凭 K1 契约拦截。

## 10. 未决项与风险

| 项 | 状态/owner |
| --- | --- |
| DEF-K2-1/2/4/5 | 全部关闭 |
| DEF-K2-3（CB 入口合并/取代） | 归 K3，勿动 |
| RISK-K2-5（K1 fixture≠真实产物） | 降级：挂接后缩到一行+BatchResult 字段；P4 T022 用 mock provider 验真实链路；真实 89 语料冒烟待 K1 跑批次后人工记录 |
| K1 遗留 5 个红（task5×2/task0/task1/task2a-existing_cli） | **不归 K2**；K2 只保证零新增失败；清理归 K1 后续或 K4 |
| target_slug 回填 | K1 真实产出后按 K1 slug 规则填 query_fixture_sample.json |
| stage outcome/reflection | unavailable（无宿主）——如需正式 outcome 要接外部 Stage Agent |

## 11. 下一步动作（下一会话第一句可执行）

1. `cd /Users/Hugh/Hugh/Project/KnowledgeDigest-task8-entry-navigation && git log --oneline -3` 确认 HEAD=d5893c0；
2. 读 `specs/task8-entry-navigation/tasks.md` 头部 gate 说明 + **T001R** 卡（P1 第一张 RED）；
3. 按 T001R 动作写失败测试（fixture：K1 真实 schema 迷你批次）→ 提交 RED → T001G 实现对账层 → GREEN；
4. 逐卡推进 P1→P2→P3→P4→T022，每卡回填执行状态填写区；P3 起全离线（FakeGateway/DictCache）；
5. 全量回归对照 `baseline_failures_20.txt`。

## 12. 待读文件清单（按序）

1. `specs/task8-entry-navigation/tasks.md`（头部 gate + T001R 卡）——开工入口
2. `specs/task8-entry-navigation/spec.md` §5 FR + §11 AC（oracle 口径）+ PFACT-K2-002/005
3. `specs/task8-entry-navigation/plan.md` DEC-K2-001..004 + File Boundary + Test Strategy
4. `src/knowledge_digest/semantic_audit.py`（_manifest @779 / write_audit @986）+ `semantic_cli.py`（挂接点）
5. `src/knowledge_digest/semantic_page.py`（_build_frontmatter @839）+ `semantic_cache.py`（@178/261/294）
6. `tests/fixtures/task8_nav/query_fixture_sample.json` + `baseline_failures_20.txt`
7. 仓库根 `AGENTS.md`（K1 合并后的现行开发指南/运行命令）

## 13. 可自行判断与必须问用户的边界

**可自行判断**（勿问）：fixture 内部结构与样例数据措辞；测试断言的具体写法（守住 oracle 语义）；
实现内的函数拆分（守单模块四职责块与 500 行拆分线）；refactor 不改行为；临时调试命令。

**必须问用户**（停）：任何 spec/plan/tasks 的设计变更（含 AC 门槛、判据口径、白名单路径、挂接位置）；
需要修改 K1 文件（除 semantic_cli.py 挂接区）或动 K1 遗留 5 个红；新增/删除需求或页面类型；
要用真实 provider 网络跑非冒烟测试；发现 K1 真实实现与 spec PFACT-K2-002 不符到对账层兜不住；
要把产物写出白名单（如想加导航到别的目录）。
