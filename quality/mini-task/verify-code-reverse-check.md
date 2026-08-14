# verify-code 反向验收

## 结论

当前代码没有未修复的严重实现问题。实现、测试和真实演练均已完成；正式质量结论暂为 `incomplete`，原因只有一个：异源实现审查是在修复前快照上完成，按 WorkflowHub 规则不能冒充修复后当前快照审查。用户要求只审查一次，因此不重发审查。

## 反向链

原始需求 → 决策 → spec → 用户流程 → plan/tasks → AC → 代码/测试/真实结果：

- 原始问题是“真实运行长时间无结果、预算门禁太晚、调用/replay 统计混乱、失败退出码不诚实”。decision-log 选择保留安全限制，但先做 preflight、实时反馈、诚实失败和恢复。
- spec 固定了 6 个运行执行状态，并明确它们不是 Task3 项目状态或知识文件状态；`page_status`、`writeback`、`delivery_status`、`released/not_released` 独立保留。
- 用户流程已闭合：CLI → preflight/plan → provider 或 `--no-llm` 执行 → progress/heartbeat → 成功或 blocked/failed/cancelled → 报告和退出码 → batch 固定清单恢复。
- 计划和任务覆盖显式调用上限、重放上限、请求超时、总时限、并发上限；不再用 `source_count * 4` 作为隐式门禁。
- 真实结果覆盖 89 条离线语料和 3 篇有正文 qwen3.6 样本；机器发布合同通过，未要求逐页人工验收。

## AC 结果

| AC | 结果 | 证据 |
|---|---|---|
| AC-001 | pass | preflight plan、终端限制摘要、全量 acceptance |
| AC-002 | pass | 集成 11 秒 fake provider heartbeat acceptance |
| AC-003 | pass | 3 篇 fixture：planned 16，replay 独立统计 |
| AC-004 | pass | provider failure、预算阻断、批次恢复测试 |
| AC-005 | pass | `--no-llm` 计划/进度，provider=0；89 条真实离线演练 |
| AC-006 | pass | completed 返回 0；blocked/failed/cancelled 返回非零 |
| AC-007 | pass | plan/progress/report 脱敏测试和真实结果检查 |
| AC-008 | pass | 完整回归 574 passed、3 skipped |

## 异源 finding 处置

- major：batch 恢复入口缺少 runtime 策略 fail-closed。已修复；新增缺失限制回归，provider=0、blocked failure report、非零异常。
- minor：wall-clock 文案和重复键。已修复。
- minor：根 README 未更新。已补齐。
- minor：长 provider heartbeat 和 KeyboardInterrupt 缺集成证据。已补齐 11 秒 fake provider 与 cancelled acceptance。
- 修复后未重跑 wh-review；保留原始审查、原始 finding、修复代码和当前测试事实，不伪造当前快照审查结果。

## 剩余风险和边界

- SIGKILL/断电只保证最近一次原子 checkpoint，不能承诺事后落盘。
- 89 条语料只做离线全量；在线 qwen 只做 3 篇有正文样本。
- 未做浏览器 QA；本 mini-task 不是 UI 任务，验收对象是本地计划、进度、报告、来源链和知识产物。
- 未执行 commit、merge、push、cleanup；等待用户单独授权。
