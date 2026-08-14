# Verify-code：真实输入与可绑定产物盘点

盘点时间：2026-08-13（Asia/Shanghai）

## 已确认可用

- 原始语料目录：`/Users/Hugh/Downloads/confluence 原始数据`
- 该目录包含 89 个 Markdown 来源；`.DS_Store` 未计入来源。
- Task 1 真实语料控制面回归：`49 passed`。
- 当前工作树回归（修复后）：focused `211 passed, 3 skipped`；full `634 passed, 3 skipped`。

## 查找结果

- 已找到可绑定的 Task 3 候选：`/private/tmp/kd-task3-real-semantic-20260813/candidate2`，包含 `bundle/ + audit/ + reports/`，由 run `run-a21c831619c44834`、89 条 manifest、snapshot hash 和 bundle hash 绑定。
- 已找到的 `T013.semantic-run-*.json` 是 Task 2-B 历次语义运行回执；即使其中部分记录 `source_count=89`，它们的 `delivery_status` 仍为 `not_released`，且不是可读包、审计包和报告目录的完整候选根，不能替代 Task 3 输入。
- 旧的 `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb` 是历史 Task 2 结果，不是当前 Task 3 候选；不把它改名或冒充当前运行。
- 固定 Task 1/Task 2 回归基线目录缺失：`/Users/Hugh/Downloads/KnowledgeDigest-task1-baseline-nd5n6s`、`/Users/Hugh/Downloads/KnowledgeDigest-task2-publication-offline-after-v4/company-kb`。
- 本次真实语义运行已使用用户指定的 qwen3.6 配置完成；凭据只通过进程环境变量传入，不写入候选、报告或仓库。

## 结论

当前代码、89 条真实语料控制面和 Task3 全量语义质量已验证；候选交付硬门也通过。但没有可安全绑定的旧正式根保护/readback，也没有 summary confirmation，因此不能宣称 `released`。`quality/verify.json` 继续保持 `incomplete` / `not_released` / `close_authorized=false`。
