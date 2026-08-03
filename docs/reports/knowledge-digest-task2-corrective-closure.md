# Task2 corrective closure

本记录只记录当前 Task2 修复后的真实证据，不把失败运行包装成成功。

## 已修复

- 发布字段现在进入最终 layout record，并在主题页稳定输出 `Summary`、`Why`、`Version`、`Related topics` 与 `field_refs`。
- qwen publication prompt 改为紧凑的 publication-only 合同；OpenAI-compatible 请求设置 `max_tokens` 上限，避免无界输出拖垮请求。
- 同一主题拆成多个 Claim 批次时，publication 建议会合并保留，不再退回文件名标题。
- 生成器返回的 Summary/Evidence 外壳不会再次嵌入 Evidence，避免正文重复。
- 对比脚本区分 deterministic generator rounds 与真实 provider calls；`--no-llm` 的 provider call 明确为 0。
- 批次失败现在持久化 `batch-failure-report.v1` 和 `cost_summary`；失败侧车明确 `status_semantics=historical_failure`，另有 `final_status`，已创建的 run report 会标记 `failed_provider`、`needs-review` 和 `replay=pending`。来源数预算单独叫 `provider_calls_reserved`，不会冒充实际 provider 调用或 planned generator calls。
- 对比脚本按 report mtime 选择最新运行，并读取批次账本的失败/重放/耗时事实；批次运行的 aggregate observed calls/tokens 未知时保持 `null`。
- 离线正式 `report.json` 现在直接把 deterministic rounds 与 provider calls 分开：`provider_calls_planned/observed=0`，`deterministic_rounds` 单独记录；批次首个 provider 请求前会执行 full-manifest dry-run，planned generator calls 超过 180 时 fail-closed。

## 真实 qwen3.6 + jina evidence

固定 3 条输入的小批次运行完成，结果在：

`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-live3-JiyW7X`

- LLM：qwen3.6；embedding：jina-embeddings。
- 其中 2 条有效来源完成 5 次 generator calls，coverage 1.0，faithfulness passed，unsupported claim 0；第 3 条是 5 字节空来源，被正确拒绝并排除出 source-index。
- 主题页出现语义标题、摘要和分类；未写入 reasoning 内容。

89 篇真实 LLM 全量没有成功闭环：

- `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-full-UJPO8E`：长时间运行后中止，保留现场。
- `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-full20-UTooAc`：provider 返回空/破损 JSON，fail-closed，未写正式主题页。
- `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-failed-source-zyJuS3`：失败来源单独重放仍返回非法 JSON。

这些现场证明当前 provider/批次预算仍不足以证明 89 篇实时语义发布已经稳定完成；不再重复消耗调用伪造成功。

## 89 篇离线回归

最终离线产物：

`/Users/Hugh/Downloads/KnowledgeDigest-task2-offline-after-kJjick`

- 89 篇输入，空 KB，Jaccard，`--no-llm`。
- 9,288 个 Claim 与 Task1 基线逐项保留。
- 120 个物理主题分页，最大 300 行；Home、分类页、来源索引和 README 可读。
- 不调用 LLM，也不探测 embedding；报告中的 86 次是确定性 generator rounds，不是 provider calls。
- CompanyBrain 17 个固定样本已生成匹配表，但人工阅读字段仍是 `manual_review_required`，不能冒充人工验收。

## 当前结论

代码修复和离线无损回归已完成；Task2 的“实时 89 篇语义发布 + CompanyBrain 人工阅读验收”仍未完成。因此当前不能把 Task2 标记为全部 AC 通过或正式 close。

AC-008 当前仍为 partial：失败批次已经有统一的失败/重放/耗时/fallback 账本，成功报告也区分 planned/observed calls，180-call dry-run hard-stop 已实现；但没有 89 篇完整成功语义发布，provider 截断时 observed calls/tokens 仍未知，因此不能宣称完整 provider 成本闭环。

当前代码验证：r9 聚焦 100 项、全量 310 项通过；`git diff --check` 通过。当前快照的官方 `wh-review` 已按配置发起，但宿主 bridge 未返回唯一响应，因此质量事实为 unavailable，不是 pass。

## Task2 最终 qwen 分批发布证据（2026-08-03）

最终可读产物：

`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-batched-final-kxlAw1/company-kb`

对比报告：

`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-batched-final-kxlAw1/comparison-final-r3/COMPARISON.md`

- 89 篇来源快照；88 个有效来源进入来源索引，1 个空/无效来源被拒绝。
- 当前 Claim 实体 9,288，与 Task1 一致；Claim fingerprint 集合 7,796，与 Task1 一致。
- 74 个稳定主题、110 个物理主题页；所有主题页不超过 300 行；Home、父级分类、叶分类和来源索引均可达。
- 主题页不再落在 `pages/digest`；来源失败页进入 `needs-review` 状态和 `_queues/needs_review.md`，不会伪装成已验证。
- qwen3.6 + jina-embeddings 真实 provider 运行使用 18 个可恢复批次；累计 172 次实际 provider 调用、80 次失败/回退、2 次重放；未使用 DeepSeek，未写入 reasoning 内容。
- 由于 qwen/embedding 响应延迟，完整运行墙钟为 3,688.666 秒，超过规格的 3,600 秒安全线 88.666 秒；因此 AC-008 的“完整实时运行性能通过”仍是 partial，不能写成 pass。
- 固定样本当前有 17 个可用主题（Products 4、Engineering 4、Customers 4、Operations 4、Principles 1）；这是语料主题数量不足导致的缺口，不从无关页面伪造补齐。比较脚本已完成 Codex agent-assisted 可见字段审查，但仍明确保留独立人工阅读边界。

本次代码修复后的完整测试：`312 passed`；`git diff --check` 通过。另有一次为验证更大批次性能而启动的第三版运行在首批未完成前停止，状态和日志保留在 `KnowledgeDigest-task2-qwen-batched-final3-20260804-000841`，不计入最终成功产物。

随后又验证了 89-source 单批方案；它在约 11 分钟仍未完成首批 provider 处理，现场保留在 `KnowledgeDigest-task2-qwen-single-batch-20260804-001918`，同样不计入最终产物。两次现场共同说明：瓶颈主要是 qwen/embedding provider 响应延迟，不能靠简单改 batch-size 宣称达到 60 分钟安全线。
