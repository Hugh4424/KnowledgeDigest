# Task 2-A 入口验收与 Backfill

这里不是正文产物，而是 Task 2-A 开始前的上游退出物核对。

## 当前结论

`knowledge-publication-task2-entry-backfill.v1.json` 是一次重新计算的 backfill，不是历史 Task0/Task1 原始 exit receipt。入口控制面现在允许启动 Task 2-A，但包状态仍是 `not_released`，禁止进入 Task 2-B 正文编译。

- Task0：已重新跑 89 条语料的离线/Jaccard 运行，并保存运行审计、来源清单和溯源账本的外部证据包；没有历史 Task0 exit manifest。
- Task1：已重新跑 89 条语料并保存 `source-inventory`、`topic-plan`、`topic-index`、`kb.structure.md` 和 run report；历史 receipt 的产品/Gazetteer描述与当前结果存在冲突，尚未关闭。
- 题集：17 个正向题、3 个负向题和两个 hash 已核对。
- 样本：已补 20 个结构样本和来源证据预检；它们不是读者质量通过。逐题语义 answerability、section 完整性和人工读者门仍由 Task 2-B/2-C 负责。

## 继续条件

Task 2-A 入口门已经满足。Task 2-B 仍需等待 Task 2-A exit，并且必须另外通过语义编译门：

1. Task 2-A 读取当前 backfill manifest，不把历史缺失 receipt 当作当前证据。
2. Task 2-B 再为正文样本补齐逐题 answerability、证据来源、主题、页面类型和排除理由；正向可答题不少于 8 个。
3. Task 2-A/2-B 继续沿用当前 source-derived 词典，不把它冒充为产品维护者最终 canonical 确认。

外部 Task0 完整证据包（含 source snapshots 和 claim history）位于本机 Downloads 的 `KnowledgeDigest-task-entry-audit-20260806/task0`；仓库不提交原始语料和完整快照。

## 2026-08-12 当前修复快照

Task 1 已基于同一份本机 89 条真实原始语料重新生成当前快照：`task1-real-corpus-current-20260812/`。这次只把真实 source declaration 中显式声明的三个 page type 投影进 TopicIndex，并绑定 source URI、content fingerprint、line 1 locator 和 topic key：`product_overview`、`module_or_capability`、`procedure_or_rule` 各 1 条。旧快照保持不变，当前快照才是 Task 2-B 重跑的入口权威；控制面仍为 `not_released`，不代表语义正文或人工读者质量通过。

## 2026-08-12 Task 2-B 机器出口当前结果

Task 2-B 已消费 `task1-real-corpus-current-20260812/`，并完成真实 qwen3.6 语义运行。当前证据为 `apply/evidence/T013.semantic-run-task2b-provider-repair-v9-20260812.json`，run_id=`run-519d5c93591e45faab8e3ef56601a3f1`，证据 sha256=`c38aad3185bd534ee988766d55fc26ee68d5f8b2688f8e00ddb72d23dbbd17e4`；validator=`valid=true`、`machine_exit_passed=true`。

- 12 个 concept 通过机器门：`module_or_capability=10`、`product_overview=1`、`procedure_or_rule=1`。
- T014：Task 1 focused=`49 passed`；Task 2-B/Task 2/Task 2-A consumers=`264 passed, 2 skipped`；全量=`518 passed, 3 skipped`；`git diff --check` 通过。
- 这只是 Task 2-B 机器出口；交付仍是 `not_released`。Task 2-C 人工读者门、正式 released 和 Git closeout 不由这份入口证据提前宣称。
