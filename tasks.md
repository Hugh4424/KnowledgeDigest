# mini-task tasks：Reader 质量整合

| ID | 任务 | AC |
| --- | --- | --- |
| T01 | 来源扫描、产品/模块映射和 unclassified/general 兜底 | 01,03,07 |
| T02 | 正文清理、Reader 投影和超长拆分 | 04,05,06 |
| T03 | 产品 overview、知识类型入口、模块 index、根导航 | 01,02,06 |
| T04 | 接入 `task3_full_release.py --raw-input` | 07,09 |
| T05 | 失败边界和旧包保护测试 | 07,08 |
| T06 | 接口形状、80 分代理、相关测试和完整 pytest | 01-09 |
| T07 | 真实资料运行并与 CompanyBrain 对比 | 01-09 |
| T08 | 一次 implementation wh-review，修复有效 findings | all |

顺序：`T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08`。

设计审查结果：一次 `mini_task.design` 已完成；major finding 已通过兜底和拆分修复，minor findings 已通过 80 分口径、最小接口和过程元数据处置闭合。不得机械重复设计审查。

完成定义：相关 acceptance 与完整 pytest 通过；真实运行有独立 output、source manifest、质量报告、比较报告和降级说明；能回答产品层级、overview、模块入口、来源覆盖、Reader 泄漏和正文是否仍是原文堆放；wh-review findings 原样留存。

## T07/T08 收尾复跑（2026-08-19）

- 正式 89 条输出：`/Users/Hugh/Downloads/KnowledgeDigest-task4-reader-quality-compiler-real-20260819-v39-89`。
- 结果：`source_count=89`、`reader_source_count=88`、`failure_count=0`、`package_status=candidate`。
- 已知 title-only 空页 `emm for android /AE - AirViewer厂商管理.md` 只在精确 `source_uri + content_hash` allowlist 下进入 Audit `not_applicable`，保留原始快照，不进入 Reader，不生成 Claim；其他空源仍 hard fail。
- CompanyBrain 机器对照：`better_than_companybrain`；`blocking_reasons=[]`；路径和边界/来源清晰度严格更好，其他轴不变差。
- 回归结果：聚焦 `28 passed`；声明的最终验收集合 `291 passed in 4.40s`；完整 pytest `733 passed, 3 skipped`。
- 对应决策：`specs/task4-reader-quality-compiler/decision-log.md` 的 D-026；正式候选已完成，未把候选冒充生产 `released`。
- verify-code 外部 WorkflowHub review provider 仍不可用，已原样记录，不能写成外部复核通过。
- 用户对齐事实（2026-08-19）：用户明确要求只执行 `verify-code` 并关闭 KnowledgeDigest 任务，不归档当前会话；已按此执行。
