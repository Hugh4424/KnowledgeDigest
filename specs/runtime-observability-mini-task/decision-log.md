# Mini-task Decision Log：运行计划、进度和失败反馈

## 1. 原始需求

用户原话：

> 请调研失败的根本原因，设计解决方案！

随后用户明确：

> 不要重新走“make-decision”，当前的task3还在进行中！请使用workflowhub的mini-task模式。

在本 mini-task 的方案选择中，用户选择了 B：保留安全限制，但把限制提前、说清楚，并持续反馈进度；同时修正调用和重放的统计。

## 2. 关键事实

1. 真实 89 条语料运行超过 30 分钟，没有进入页面写入阶段；当时没有及时向用户报告当前阶段、已完成数量或阻塞原因。
2. 3 篇文档的无摘要运行实际产生 16 次 provider call，报告将 13 次计为 replay，并在完成昂贵工作后才判定预算超限。
3. 当前预算判断包含 `source_count * 4` 和 `replay_calls > 1` 等硬编码条件；批处理数量被混入 replay 统计。
4. 当前 CLI 在审计结果为 blocked 时仍无条件返回 0，调用方容易误以为运行成功。
5. provider 小请求可正常返回，因此根因不是“provider 一定不可用”；主要问题是批次计划不可见、预算门禁太晚、统计口径错误、过程无反馈、退出码不诚实。
6. Task3 的知识页面、来源链、`released/not_released` 和页面质量合同不属于本 mini-task 的修改范围。

Task3 交接合同摘录（只读依赖）：

- 正式主题页必须有 `Summary`、`Evidence`、`Provenance`，并受页面行数上限约束。
- `Home.md → indexes/<category>.md → 主题页` 是读者入口；来源索引只保存来源、指纹、状态和主题链接。
- 写入前先归档，Home、分类和主题页同批原子发布；缺失溯源、路径越界、清单变化和页面超限必须明确失败。
- 交付状态、页面状态和运行审计分开；模型请求成功、provider 返回 200 或写回成功都不能单独证明正式发布。

以上摘录只用于说明本 mini-task 的依赖边界，不改变 Task3 原文。

可复核的实现依赖快照（基线 commit `05944489f4bfa83440697bc7a3605de27d8af03a`）：

- `src/knowledge_digest/batch_run.py`（SHA-256 `37d20ef86df784cfc3a7a94b15f4881466d075257afda1c2ed870759d492c108`）：恢复会校验固定 manifest 的 hash、sources 和 runtime identity；已成功批次跳过，失败/未完成批次增加 attempt 后再跑。
- `src/knowledge_digest/pipeline.py`（SHA-256 `68f9bcdd1da4564e68c7a3c23dbdf45558c42a7ac1c1c34593935255b74b9c4c`）：旧 Task0 账本字段为 `planned_generator_calls`、`provider_calls_observed`、`replay_calls`；旧门禁还使用来源数乘 4、replay 上限和事后 audit gate，这正是本 mini-task 要修的现状，不是新合同。
- `src/knowledge_digest/draft.py`（SHA-256 `e4b7eb4f6c9f631ddac433e874ea7a8d1c21af8cd870cb21e4c6bb058e75a3ef`）：现有生成器会按 claims/字符数拆成多个 generation context；拆批本身不应记为 replay。
- `src/knowledge_digest/cli.py`（SHA-256 `f3cab494b047ac0b04175f08fdcc394d547f7897bc58199835cf8642a70764a3`）：现状无论 audit summary 是否 blocked 都返回 0；本 mini-task 的 AC-006 明确修正这一点。
- 旧真实报告的可见账本为：`planned_generator_calls=16`、`provider_calls_observed=16`、`replay_calls=13`；这些数字只用于回归复现，不是新实现的字段合同。

权威来源 `docs/plans/knowledge-digest-knowledge-publication-prd.md` 的 SHA-256 为 `77ad45eafc6c8d79c152a03d9a257b4a36ea651bb801a411ca4e1380baf3445f`；本材料已经摘录本 mini-task 依赖的 Task3 条款，后续实现不得把外部路径当作唯一证据。

事实来源：

- `/Users/Hugh/Downloads/KnowledgeDigest-small-nosummary-20260813.HJjUPs/_digest/runs/run-2b353d2f193d408ea2a1bb104616fb09/report.json`
- `/Users/Hugh/Downloads/KnowledgeDigest-real-test-20260813.ZPIqar/_digest/runs/run-b1a0ced1235849e0b78a757d77aaafdb/report.json`
- `/Users/Hugh/Hugh/Project/KnowledgeDigest/src/knowledge_digest/pipeline.py`
- `/Users/Hugh/Hugh/Project/KnowledgeDigest/src/knowledge_digest/draft.py`
- `/Users/Hugh/Hugh/Project/KnowledgeDigest/src/knowledge_digest/cli.py`
- `docs/plans/knowledge-digest-knowledge-publication-prd.md` 的 Task0/Task3 运行合同。

## 3. 选项和选择

| 选项 | 做法 | 后果与风险 |
|---|---|---|
| A | 删除所有预算和超时限制 | 可能继续长时间运行、重复花费，失败时难以止损 |
| B | 保留限制，但预检、可见、实时反馈并修正统计 | 改动较小，能止损；仍需把策略值写入运行清单 |
| C | 默认全部离线，只允许人工切换模型 | 最稳，但不符合当前语义发布需求，容易把模型能力变成隐藏开关 |

选择：**B**。

理由：用户要的是“真实运行能看懂、能停、能恢复、失败不伪装成功”，不是取消安全边界，也不是改变 Task3 的知识发布合同。B 能直接修复本次暴露的五个根因，且不扩展成调度器、数据库或后台服务。

## 4. 本次冻结的解决方向

- 运行开始先做 preflight：固定来源、生成批次计划、显示预计调用数、重放规则、超时和总时限；preflight 失败时不发模型请求。
- 运行中写入可读的 progress 状态，并在每个批次前后及长请求期间持续输出心跳。
- 预算统一按“逻辑批次”和“实际请求尝试”统计；拆批不是 replay，同一逻辑批次的第 2 次及以后尝试才是 replay。
- 删除 `source_count * 4` 这种隐式放大门槛；保留一个在配置/清单中可见的调用上限、请求超时、重放上限和总时限。
- 并发上限是执行器容量参数，也必须写入运行计划；缺失或小于 1 时在 preflight 阻塞，正常执行不得超过它，若实际超出则按实现失败处理。它不参与调用数预算，不是新的来源数乘倍门禁。
- 预算、provider、超时、用户中断等阻塞或失败立即写入报告，并返回非零退出码；成功运行才返回 0。
- 恢复沿用固定清单，只重跑受影响批次，不重复已成功批次。

## 5. 不改变的内容

- 不重新走 `make-decision`，不调用 `build-spec`。
- 不修改 Task3 的页面结构、Summary/Evidence/Provenance、来源链、发布状态语义或人工确认选择。
- 不引入调度器、数据库、向量库、daemon、自动后台重试或新知识域状态。
- 不把“模型请求成功”当成“知识发布成功”。运行执行状态、页面状态和交付状态继续分开。

## 6. 延期交接

- 当前默认调用上限和总时限的业务数值不在本文件重新拍脑袋；实现必须从显式运行策略读取并写入 manifest，兼容默认值也必须展示出来。后续如需调整默认数值，单独提交小决策。
- 本 mini-task 不负责把已经中断的 89 条真实运行自动补完；实现后先用离线回归和 3 篇小样本验证，再决定是否重跑全量。
- 本 mini-task 不负责重做 Task3 的正式 release/close；需要另行按 Task3 的交付边界处理。
