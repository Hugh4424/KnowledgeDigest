# Task2 verify-code 结论

验证对象：当前 Task2 worktree `task/KnowledgeDigest/knowledge-digest-llm-naming-classification`。

读取材料：`decision-log.md`、`spec.md`、`plan.md`、`tasks.md`。

## 新鲜测试

```text
uv run --frozen pytest -q
312 passed in 17.39s
git diff --check
exit 0
```

## AC 逐项事实

| AC | 结论 | 证据 |
| --- | --- | --- |
| AC-001 | pass | 89 snapshots；88 个有效 source-index URI；74 稳定主题；Home/父级/叶分类可达；主题不在 `pages/digest`。 |
| AC-002 | pass（机器/辅助审查） | 固定 17 个可用样本标题均无 `cluster`/`draft`/`topic-*`；重复稳定性由 acceptance 回归覆盖。独立人工语义理解仍未替代。 |
| AC-003 | pass | 110 个物理主题页均含 Summary/Evidence/Provenance/Why/Version/Related topics；最大 300 行；9,288 个 Claim entity 各只落一个当前 target。 |
| AC-004 | pass | Task1/Task2 均为 9,288 Claim entity、7,796 fingerprint；88 个 source-index 链接全部指向存在页面。 |
| AC-005 | pass | 注入 provider error/malformed JSON 的 acceptance 通过；成功页保留；失败来源同时进入 pending-review、source-index `needs-review` 和 `_queues/needs_review.md`。 |
| AC-006 | pass | `--no-llm`/Jaccard 离线回归与 no-provider 测试通过；离线报告 provider calls 为 0。 |
| AC-007 | partial | Products/Engineering/Customers/Operations 各 4 个，Principles 仅 1 个；总样本 17 个，缺 3 个。缺口来自当前语料主题不足，未从无关页面伪造。Codex agent-assisted reader audit 标题 17/17，但 `human_review_required=true`。 |
| AC-008 | partial | qwen3.6+jina-embeddings 18 批完成：172 observed calls、80 failed/fallback、2 replay；planned=172、tokens 未由 provider 提供。墙钟 3,688.666 秒，超过 3,600 秒安全线 88.666 秒。 |

## Review 事实

当前 snapshot 的官方 WorkflowHub `wh-review` 尝试为 `unavailable`：宿主 bridge 返回 `host bridge requires exactly one response after request`。这不是 pass，也没有改 WorkflowHub、换 DeepSeek 或用历史 provider verdict 冒充当前结论。

## 总结

代码、离线无损、可读发布结构和失败恢复已验证；AC-007 的语料样本缺口、AC-008 的实时 provider 性能超线以及独立人工阅读仍是明确未完成项。因此本次 verify-code 不能给出“全部 AC 通过”，也不能伪造正式 close receipt。最终 qwen 产物和完整机器对比仍保留在：

`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-batched-final-kxlAw1`
