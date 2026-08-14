# Mini-task 实施事实

## 已完成阶段

- Phase 1：显式运行计划、preflight、策略和 CLI 状态码。
- Phase 2：原子 progress、10 秒 heartbeat、错误收尾、逻辑批次进度和执行中预算拦截。
- Phase 3：调用/重放字段保留兼容口径，批次恢复补齐运行策略，运行说明同步。

## 路由与测试

- Phase 2 实际范围：`src/knowledge_digest/runtime_status.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_mini_task_runtime_observability.py`；advisor 结果 `fullstack`，原因是跨 `src`/`tests`。
- Phase 3 实际范围：`src/knowledge_digest/draft.py`、`src/knowledge_digest/cli.py`、`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/pipeline.py`、`AGENTS.md`、相关 acceptance；advisor 结果 `fullstack`，原因是跨 `src`/`tests`/文档。
- 当前 focused GREEN：93 passed；完整回归 574 passed、3 skipped。
- 异源实现审查：`f4e7e0d5-2b52-45e9-9de3-53a90a01057f`，provider `opencode/v4flash` 返回 1 个 major actionable、3 个 minor；major 已修复，未重复发起审查。
- 修复后完整回归：574 passed、3 skipped；最终 aggregate receipt 在全部文件冻结后重新采集。
- 当前最终收据：`quality/tests/mini-task-final-aggregate-v3.json`；收据同时绑定本工作树最终 snapshot。
- 新增三篇 fixture：preflight 输出 `sources=3 batches=16 planned_provider_calls=16`；设置上限 15 时状态 `blocked`、provider observed 为 0、退出码 1。
- Manifest 失败：首次运行不先写 `Home.md`，生成 failed run、plan、progress，CLI 返回非零。
- 离线真实语料：来自 `/Users/Hugh/Downloads/confluence 原始数据` 的 89 条声明；`--no-llm` 退出 0，执行状态 `completed`，86 logical batches 为 86/86，provider observed 0，120 Reader pages，136 formal changes；1 条空正文源保留为 failed snapshot。
- qwen3.6 真实语料：3 篇有正文文件；preflight 5 planned calls，5/5 logical batches 完成，provider observed 5、replay 0，生成 3 个 Reader pages，CLI 退出 0。

## 关键修复

- 计划按实际 generation contexts 展开 logical batches，拆批不再被当成 replay。
- provider 请求前检查 max provider calls、max replay calls、max wall seconds；请求超时从运行策略传给 LLM client；执行器并发取策略上限。
- preflight blocked 也写 similarity/runtime audit、report、progress，并返回非零。
- provider/运行异常先写最近错误，再结束 progress；正常完成才让 CLI 返回 0。

## 当前限制

- qwen provider 不可用时现在明确为 `failed`、非零退出，不再伪装成 `completed`；本次 3 篇有正文样本已成功完成。
- `_source_rows` 之前的路径/config 校验错误仍由 CLI 直接返回；它们没有 run 目录，这是输入路径层错误，不属于已接管的执行阶段。
- 未执行 Git commit、merge、push 或 cleanup；用户没有授权。
