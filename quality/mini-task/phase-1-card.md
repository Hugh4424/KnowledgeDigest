# Phase 1 Card — run plan 与 preflight

## 目标

在任何模型生成请求前，固定本次来源快照、生成批次和显式运行策略，写入
`_digest/runs/<run_id>/plan.json`，并在计划超限或策略不完整时以 `blocked`
结束，provider 请求数保持为 0。

## 允许改动

- 生产代码：`src/knowledge_digest/config.py`、`src/knowledge_digest/pipeline.py`、
  `src/knowledge_digest/batch_run.py`、`src/knowledge_digest/cli.py`。
- 测试：新增 `tests/acceptance/test_mini_task_runtime_observability.py`，必要时补现有
  Task0/Task2 回归断言。
- 本阶段事实：本卡及同目录证据文件。

## 覆盖范围

- AC-001：计划先落盘，再进入 provider 阶段。
- AC-003：区分 planned provider calls、实际 calls 和 replay calls 的字段基础。
- AC-005：`--no-llm` 也先经过 preflight。
- AC-006：preflight blocked 不返回成功。
- AC-007：计划不写 API key 或 Authorization。

## 非目标

本阶段不改知识页、来源链、`released/not_released`、Task3 交付状态、heartbeat、
失败收尾和正式恢复流程。

## 兼容边界

保留旧报告字段 `planned_generator_calls`、`provider_calls_observed`、`replay_calls`；
新增 `planned_provider_calls`。旧 Task3 状态继续独立存在。

## 预设测试路线

`feature`：先运行新增 preflight 行为测试获得 RED，再运行
`uv run --frozen pytest -q tests/acceptance/test_mini_task_runtime_observability.py`
作为 GREEN oracle；覆盖 3 篇计划、显式策略缺失/超限、`--no-llm` 和敏感信息扫描。

## 停止条件

计划未在首个 provider 请求前落盘、隐式 `source_count * 4` 仍是唯一门禁、缺失策略
被当成无限制，或现有 Task3 回归被改变时停止并修复；不为追求空 review 重复审查。

## 阶段结束摘要

实现后记录实际 changed files、测试命令/退出码、AC 结果、一次异源审查事实、finding
处置和遗留风险。
