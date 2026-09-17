# Mini-task Plan：运行可观察性和诚实失败

## 边界

一个结果：一次 digest 运行在开始前可预估、运行中可观察、失败后可恢复且退出码诚实。

不碰 Task3 的知识发布合同，不新增服务，不改数据库和持久化架构。工作目录：
`/Users/Hugh/Hugh/Project/KnowledgeDigest-runtime-observability`。

## 实施顺序

### 1. 先补失败复现测试

在 acceptance/回归测试中固定三类 fixture：3 篇会拆成多个批次的输入、preflight 超限输入、一次真实重放和一次中断。先验证当前行为确实失败，再开始实现。

### 2. 增加显式运行计划和 preflight

在现有 pipeline/batch 边界生成不可变的 run plan，记录来源快照、逻辑批次、显式运行策略和预计调用数。CLI 在任何 provider 请求前展示并写盘。移除来源数乘倍的隐式阻塞；超限前置为 `blocked`。

### 3. 增加进度和心跳

沿用 `_digest/runs/` 的审计目录，新增原子更新的进度记录。运行开始到结束启动一个旁路 heartbeat monitor；它固定每 10 秒更新 `progress.json` 和终端摘要，批次开始/结束、重放、错误也立即更新；终端只输出必要的阶段、计数和最近错误，不输出密钥或完整原文。

heartbeat monitor 由停止事件控制；主流程无论在本地预处理、provider 请求还是写回阶段，都不能因 monitor 而吞异常。运行正常返回、抛异常或收到可捕获中断，都必须走 `finally`：设置停止事件、等待 monitor 线程退出、写入包含最近错误和最终阶段的进度；然后按既定状态原样结束。monitor 线程只做状态写入，不能捕获、替换或吞掉主流程异常。

### 4. 修正调用/重放统计和退出码

为逻辑批次保留稳定 id 和 attempt 序号；只有同一批次的 attempt>1 计为 replay。将 blocked/failed/cancelled 传到 CLI，非零退出；正常完成才返回 0。超限在执行中首次发现时立即停。

恢复入口先校验 batch state 中保存的五项运行限制，缺失、非法或与当前策略不一致时 fail-closed，不进入 provider 或 batch audit。

### 5. 接入恢复和文档

复用已有固定清单和 affected-batch 恢复机制；确认恢复不重做成功批次。同步 `AGENTS.md` 和根 README 的运行命令说明，明确“运行执行状态”和“交付状态”不是一回事。

### 6. 验证

先跑 focused acceptance，再跑完整测试；用人为延长到 20 秒的 fake provider 和 20 秒的本地预处理 fixture 验证整个运行期间每 10 秒有 heartbeat 时间戳。随后用 `--no-llm` 做 89 条离线回归，用 qwen3.6 做 3 篇真实小样本。真实全量重跑另行决定，不在实现时偷偷启动。

## 风险和回滚

- 风险：已有报告字段被外部脚本读取。保留 `planned_generator_calls`、`provider_calls_observed`、`replay_calls`，新增 `planned_provider_calls`，不用静默改名；兼容解析失败要明确报错。
- 风险：长请求心跳实现不应吞掉 provider 异常。心跳只能旁路写状态，主流程仍 let it crash；硬终止不承诺事后落盘，只保证最近一次原子 checkpoint。
- 风险：恢复计划与旧 batch-state 不一致。继续使用现有清单/指纹校验，发现变化立即失败。
- 风险：旧 batch-state 可能没有完整运行限制。恢复不猜默认值，直接报告 runtime policy 不完整并要求新建状态文件，避免把旧状态误当成无限制运行。
- 回滚：只回滚本 mini-task 分支的代码和文档；不删除任何现有 Task3 worktree、运行报告或知识库。

## 交付边界

本轮只冻结设计并做 `mini_task.design` 审查。实现、测试和 `mini_task.implementation` 审查在设计审查没有未解决发现且用户允许继续后进行；Git commit/merge/push 不在当前授权内。
