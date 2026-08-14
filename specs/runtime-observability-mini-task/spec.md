# Mini-task Spec：让一次 digest 运行可预期、可观察、可恢复

## 1. 用户结果

用户启动一次真实 digest 后，在模型请求发生前就能知道：处理多少来源、会拆成多少逻辑批次、预计多少次请求、限制是什么。运行很久时能看到它仍在工作；遇到预算、超时、provider 或中断时能马上知道原因；程序退出码和报告一致；恢复时不会重做已经成功的批次。

## 2. 术语边界

本 mini-task 只增加“运行执行状态”，不是知识文件状态，也不是 KnowledgeDigest 项目状态：

- `preflight`：正在检查输入和生成运行计划，尚未发 provider 请求。
- `running`：按固定计划执行。
- `completed`：执行阶段正常结束。
- `blocked`：在执行前或执行中因安全策略阻止继续。
- `failed`：发生未能安全恢复的错误。
- `cancelled`：用户或系统中断，已保存可恢复现场。

`delivery_status`、`page_status`、`writeback`、`released/not_released` 仍按 Task3 现有合同独立记录；本 mini-task 不重新定义它们。

## 3. 用户流程

1. CLI 创建 run id，进入 `preflight`，固定来源快照和运行策略。
2. CLI 输出并保存运行计划到 `_digest/runs/<run_id>/plan.json`：来源数、逻辑批次数、预计 provider calls、调用上限、请求超时、重放上限、总时限、并发上限、进度文件路径；不输出密钥。并发上限是执行器的容量参数，不单独按调用次数门禁；它从运行策略读取，缺失或小于 1 时 preflight 阻塞，执行器不得超过它。
3. 如果计划已经超过显式安全限制，写入 `blocked` 报告，说明是哪一项超限、实际值、上限和下一步，且 provider call 为 0，退出非零。
4. 计划通过后进入 `running`。从运行开始到结束启动一个旁路 heartbeat monitor，固定每 10 秒更新一次进度和终端摘要；每个逻辑批次在开始、完成、失败或重放时也更新进度。15 秒是所有运行阶段允许的最大无更新间隔，不只适用于 provider 请求。
5. 每次更新至少包含：当前阶段、已完成/总批次、成功/失败批次、实际 provider calls、实际 replay calls、最近错误、最近更新时间。
6. 正常结束时生成现有报告和知识产物；报告同时写明运行执行状态和 Task3 既有交付状态，CLI 返回 0。
7. 预算、provider、超时或用户中断时立即保存报告和进度。可恢复运行使用原固定计划，只重跑受影响批次；失败或阻塞返回非零。

## 4. 预算和统计规则

- `logical_batch` 是一次计划中的最小处理单元；拆成多个批次不等于 replay。
- `provider_call` 是一次真实发出的 provider 请求尝试。
- `replay_call` 只统计同一个 `logical_batch_id` 的第 2 次及以后请求尝试；不能用 round 数、候选数或批次数代替。
- preflight 计算并展示 `planned_provider_calls`：对固定来源快照生成固定 logical batch plan，按每个 batch 的 deterministic generation contexts 计数，求和得到预计首次请求数；不把 replay 预先算进该字段。执行中累计 `provider_calls_observed`；两者都写入报告。3 篇回归 fixture 的固定期望为 `planned_provider_calls=16`，这只是可预检的调用计划，不代表 13 个错误 replay。
- 安全限制只使用运行策略中明确列出的上限。删除按来源数隐式乘倍的门槛，不允许把隐藏常数作为唯一阻塞理由。
- 调用上限、重放上限、请求超时、总时限或并发上限任一缺失、非正数或无法解析时，preflight 直接写 `blocked`、provider call 为 0、退出非零；不允许以“未配置”当作无限制继续运行。
- 任一上限在 preflight 可预见时，必须在首个 provider 请求前阻塞；执行中首次超限时立即停止，不等到所有工作做完才提示。
- 并发上限只约束同时运行的 provider 请求数，不改变 planned/provider/replay 账本；它不是来源数乘倍预算，也不因为批次数变大而自动放大。
- 新报告保留兼容字段 `planned_generator_calls`、`provider_calls_observed`、`replay_calls`，同时新增 `planned_provider_calls`；预算门禁使用新字段，旧字段只为读取旧报告的脚本保留。
- 恢复时重新校验已保存的五项运行限制；任一缺失、非正整数或与当前策略不一致，都在 provider 请求前明确失败并要求新建 batch state，不把不完整状态当成无限制运行。

## 5. 成功和失败边界

成功：计划已保存，所有计划批次完成，报告完整，执行状态为 `completed`，退出码为 0。

失败/阻塞：

- 输入清单、策略或批次计划无法固定；
- preflight 已超过显式调用/重放/总时限策略；
- provider 请求失败、超时或返回无法验证的结果；
- 执行中达到硬限制；
- 用户中断或进程异常退出。

这些情况必须保留当前 run 的计划、进度和报告，并返回非零。不得因为有部分文件或 provider 曾返回 200 就报告成功。

状态归属固定为：preflight 发现策略超限写 `blocked`；输入清单、运行策略或批次计划无法固定写 `failed`、provider call 为 0；执行中首次达到调用、重放或总时限硬限制也写 `blocked` 并停止；并发上限是执行器约束，若实现观测到实际超出则写 `failed`；provider 返回无法验证的结果、不可恢复的输入错误或程序异常写 `failed`；可捕获用户中断/`KeyboardInterrupt` 写 `cancelled` 并保存可恢复现场。SIGKILL、断电等硬终止不承诺事后落盘，最近一次原子 checkpoint 作为最后可信进度。

## 6. Acceptance Criteria

- **AC-001**：运行首个 provider 请求前，磁盘上已有计划文件，终端已显示限制和预计调用数。
- **AC-002**：3 篇样本可以看到批次进度；长请求不会超过 15 秒没有心跳或可读状态更新。
- **AC-003**：3 篇样本的拆批数不再自动变成 replay 数；报告能区分计划请求、实际请求和真实重放。
- **AC-004**：人为触发预算或 provider 失败时，运行立即停止、写报告、退出码非零；旧的成功批次不被重跑。
- **AC-005**：`--no-llm` 运行零 provider call，仍写计划和进度，不触碰任何 provider。
- **AC-006**：成功运行的退出码为 0；`blocked`、`failed`、`cancelled` 绝不能返回 0。
- **AC-007**：计划、进度和报告不含 API key 或 Authorization header。
- **AC-008**：现有 Task3 页面、来源链、发布状态和写入原子性测试不回归。

`--no-llm` 的明确归宿：它同样先走 preflight；如果计划超限，仍写 `blocked` 报告并返回非零；只有计划通过且所有离线批次完成，运行执行状态才是 `completed`、退出码为 0，报告写 `provider_calls_observed=0` 和“未触网”。它不产生独立的交付状态，也不改变 Task3 的发布状态。

## 7. 非目标

- 不改变知识内容、页面模板、来源追溯或 released/not_released 的业务含义。
- 不新增后台调度器、数据库、向量库、daemon 或自动重试服务。
- 不取消所有安全限制，也不在本 mini-task 重新决定默认调用数值。
- 不把一次真实全量 89 条语料运行作为本次实现测试的前置条件。
