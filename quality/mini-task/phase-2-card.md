# Phase 2 Card — progress、heartbeat 与失败收尾

## 目标

让一次运行从 preflight 到 writeback 都有同一份可读进度；每 10 秒心跳一次，批次和错误立即落盘；异常、阻塞和中断不伪装成完成。

## 允许改动

- `src/knowledge_digest/runtime_status.py`
- `src/knowledge_digest/pipeline.py`
- `src/knowledge_digest/draft.py`
- `tests/acceptance/test_mini_task_runtime_observability.py`

## 覆盖范围

AC-002：过程可见；AC-004：失败立即停并留证；AC-005：离线不触网；AC-006：执行状态与退出码一致；AC-007：进度不落密钥。

## 非目标

不改知识页内容、来源链、Task3 发布状态、归档语义或后台调度。

## 测试路线

`fullstack`：生产代码跨 `src` 与 `tests`，运行 heartbeat、异常收尾、preflight 和现有 Task0/Task2 acceptance；oracle 是 progress/report 状态一致、非 completed 非零、provider call 统计正确。

## 阶段事实

- test-routing-advisor：实际 changed files 跨 `src` 与 `tests`，从预设 `feature` 重路由为 `fullstack`。
- focused GREEN：`uv run --frozen pytest -q tests/acceptance/test_mini_task_runtime_observability.py tests/acceptance/test_task0_runtime_audit.py tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_phase25_llm.py`，99 passed。
- 追加三篇计划测试：3 个来源固定生成 16 个 logical batches，计划超限时 provider call 为 0、退出非零。
- 阶段审查：沿用本 mini-task 已获得的异源审查建议，已修复 wrapper/report、终端 preflight、planned batch root 和晚预算门禁问题；本阶段不重复发起审查。

## 停止条件

进度文件不能原子更新、主异常被心跳吞掉、失败报告显示 completed，或 logical batch 与实际请求账本无法对齐时停止。
