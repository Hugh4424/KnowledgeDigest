# Phase 3 Card — 账本、退出码、恢复与文档

## 目标

让逻辑批次、真实 provider 尝试和 replay 的统计互不混淆；批次恢复只重跑受影响
批次；CLI 只在 `execution.status=completed` 时返回 0；同步运行说明。

## 允许改动

- `src/knowledge_digest/batch_run.py`
- `src/knowledge_digest/cli.py`
- `src/knowledge_digest/pipeline.py`
- `src/knowledge_digest/runtime_status.py`
- `AGENTS.md`
- `tests/acceptance/test_mini_task_runtime_observability.py`
- `tests/acceptance/test_task2_batch_recovery.py`（仅同步受影响断言）

## 覆盖范围

AC-003、AC-004、AC-005、AC-006、AC-007、AC-008，以及固定清单恢复边界。

## 非目标

不改知识页内容、来源链、Task3 发布状态和历史归档语义；不新增调度器、数据库或
自动后台重试。

## 预设测试路线

`feature`：批次状态单测与恢复 acceptance；普通/离线 CLI；完整 Task3 回归。重点
oracle 是 split 不计 replay、成功批次不重复、非 completed 非零退出、敏感字段不落盘。

## 停止条件

若旧报告字段丢失、固定清单变化未失败、split 被记成 replay，或 CLI 仍能把 blocked/
failed/cancelled 当成功，停止并修复。

## 阶段结束摘要

记录账本字段、恢复行为、CLI 退出码、文档变化、测试结果、AC 状态、一次审查事实和
剩余风险。
