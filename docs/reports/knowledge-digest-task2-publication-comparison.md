# KnowledgeDigest Task2 对比报告模板

使用 `scripts/task2_publication_comparison.py` 生成隔离目录中的 `COMPARISON.json` 与 `COMPARISON.md`。

报告必须同时保留：

- Task1、Task2 的机器结构、来源索引、页面上限和运行成本事实；
- 固定的 Products、Engineering、Customers、Operations、Principles 样本 manifest；
- Task1/Task2/CompanyBrain 的匹配状态，匹配不到时写 `no_match`；
- 人工阅读字段与机器事实分栏。标题理解度使用固定分母，未人工审查时只能写 `manual_review_required`。
- 可选 `--agent-reader-review` 只记录 Codex 的可见契约审查；它必须标记 `human_review_required=true`，不能冒充独立人工阅读或真实计时。

Claim 数、页面数、token 数和耗时不能单独作为“质量提高”结论。报告不得包含 API key 或原始正文，不得修改原始 Confluence、Task1 baseline 或 CompanyBrain。
