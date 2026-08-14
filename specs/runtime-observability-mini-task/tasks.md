# Mini-task Tasks：运行可观察性和诚实失败

## T001 — 固定复现与回归基线

- 新增 3 篇多批次、preflight 超限、真实重放、用户中断的最小 fixture。
- 记录当前 3 篇样本的旧报告基线：`planned_generator_calls=16`、`provider_calls_observed=16`、错误 `replay_calls=13`；新实现报告保留这三个兼容字段，并另外写入 `planned_provider_calls`，两者不混作同一门禁字段。
- 完成条件：测试先证明旧实现会晚阻塞、错误计 replay 或返回错误退出码；不调用真实 provider。

## T002 — 运行策略和 preflight

- 在 `src/knowledge_digest/pipeline.py`/`batch_run.py` 的现有边界生成 run plan。
- 计划必须有来源快照、逻辑批次、预计请求数、调用上限、请求超时、重放上限、总时限、并发上限和策略来源。
- provider 请求前写入 plan 并打印摘要；隐式 `source_count * 4` 不得再作为唯一门禁。
- 计划路径固定为 `_digest/runs/<run_id>/plan.json`，与 `progress.json` 同目录原子写入。
- 完成条件：超限 fixture 的 provider call 为 0，报告为 `blocked`，退出非零；plan.json 不含 API key 或 Authorization header。
- 并发上限只表示同时运行的 provider 请求数；从运行策略读取，缺失或小于 1 时 preflight 阻塞，不参与来源数乘倍预算。
- 完成条件：并发上限缺失/小于 1 时 provider call 为 0、报告为 `blocked`、退出非零；并发 fake provider 运行期间观测到的同时请求数不超过策略上限。
- 完成条件：调用上限、重放上限、请求超时、总时限或并发上限任一缺失/非正数/不可解析时，preflight 为 `blocked`、provider call 为 0、退出非零。

## T003 — 进度和心跳

- 增加 `_digest/runs/<run_id>/progress.json` 的原子更新。
- 从运行开始到结束启动受停止事件控制的旁路 heartbeat monitor，固定每 10 秒更新一次；批次开始、批次结束、重放、错误立即更新，主线程异常原样传播。
- 完成条件：测试能读到阶段、批次数、成功/失败数、实际请求数、重放数、最近错误和更新时间；不含密钥。
- 完成条件：20 秒 fake provider 请求期间至少出现一次不晚于第 15 秒的 heartbeat 更新时间戳。
- 完成条件：provider 抛异常时也经 `finally` 停止并 join heartbeat，进度里保留最近错误和最终阶段，异常仍返回主流程。

## T004 — 调用与重放账本

- 为逻辑批次传递稳定 `logical_batch_id` 和 attempt 序号。
- 只把同一逻辑批次的第二次及以后 provider 请求计入 replay；批次拆分和 round 不计 replay。
- 完成条件：3 篇 fixture 的 `planned_provider_calls=16` 可由固定 batch plan 重算；报告不再把 13 个拆分/候选尝试冒充 replay，计划数、实际请求数和 replay 数可分别核对。

## T005 — 失败传播和恢复

- blocked/failed/cancelled 写入计划、进度和报告，并立即停止后续批次。
- 执行中首次达到调用、重放或总时限硬限制时状态固定为 `blocked`；并发上限是执行器约束，若实际观测超出则为 `failed`；provider 无法验证、程序异常或不可恢复输入错误为 `failed`；可捕获用户中断/`KeyboardInterrupt` 为 `cancelled`；SIGKILL/断电只依赖最近一次原子 checkpoint。
- CLI 只在执行状态 `completed` 时返回 0；其他执行状态返回非零。
- 恢复只重跑受影响批次，成功批次保持不动；清单或指纹变化明确失败。
- 完成条件：恢复遇到缺失、非正整数或与当前配置不一致的任一运行限制时，在 provider call 为 0 前置失败，并明确要求新建 batch state。
- 完成条件：预算、provider、超时和中断测试均能读回准确状态，且没有假成功；最终报告不含 API key 或 Authorization header。
- 完成条件：`--no-llm` 计划超限时报告为 `blocked`、退出非零；计划通过时退出 0、报告为 `completed` 且 `provider_calls_observed=0`，测试 spy 确认没有 provider 请求。
- 完成条件：输入清单、策略或批次计划无法固定时报告为 `failed`、provider call 为 0、退出非零。

## T006 — 文档与隔离验证

- 更新 `AGENTS.md` 和根 README，说明 preflight、进度文件、退出码和状态边界。
- 跑 focused acceptance、完整测试、89 条 `--no-llm` 回归和 3 篇 qwen3.6 真实小样本；另用 20 秒本地预处理 fixture 验证 heartbeat。
- 完成条件：Task3 现有页面/来源/发布合同测试通过；真实小样本有终端和磁盘进度；不启动 89 条在线全量。

## T007 — 审查和交付准备

- 提供 diff、测试证据、运行计划/进度/报告、AC 对照、覆盖限制和剩余风险。
- 运行 `mini_task.implementation` 审查；发现问题先修复再重跑相关测试。
- Git commit/merge/push 等正式交付动作需用户另行授权。
