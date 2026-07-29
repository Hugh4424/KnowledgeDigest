# Phase 3 Progress

- 2026-07-28：基线命令已保存到 `/tmp/kd-phase3-agentmemory-run.baseline/`；专项 `67 passed`，全套 `178 passed`，`skipped=0`，`git diff --check` 通过。数字符合任务书，无受影响项阻塞。
- 2026-07-28：更新设计计划：Phase 3 改为 agentmemory + 公司 Confluence 知识库双库验收；agentmemory 仅走官方 REST 和现有 `AgentMemoryStore`，不接入正式 `pipeline.py`、`cli.py`；OpenViking 只保留历史调研背景；Phase 4 保留 embedding 接入和阈值标定。
- 2026-07-28：新增可复跑脚本和 4 条回归测试。脚本每次创建全新 `/tmp/kd-phase3-agentmemory-run.*`，复制固定 3 个输入和其余 89 个 Markdown 页面，生成 `kb.structure.md`、`sources.jsonl`、选中文件 SHA-256、CLI stdout/stderr、报告路径和 JSON receipt。
- 2026-07-28：实际 receipt 为 `/tmp/kd-phase3-agentmemory-run.26823/receipt.json`。dry-run、正式运行均退出码 0；3/3 输入接受；4/4 formal outputs 为 `success`；agentmemory 首次写入 58 条唯一记忆，3 个来源搜索读回成功；真实 agentmemory 和原始 Confluence SHA-256 未变；company-kb 页面 hash 保存在 `/tmp/kd-phase3-agentmemory-run.26823/company-kb-pages.sha256`。
- 2026-07-28：replay 为 `created=0`、`duplicate=94`、记忆数 `58 -> 58`；provenance 反向验证 `0/0 -> 1/2 -> 0/0`；disposable agentmemory engine `pid=27579` 已 SIGTERM 停止，动态端口已释放。
- 2026-07-28：完成收尾加固：receipt 额外保存隔离 company-kb 页面 hash；历史 OpenViking 抽查措辞明确标为非当前目标；若 disposable engine 清理拒绝，脚本现在会写失败 receipt 并以非零退出。原因：补足机器可读证据和安全清理硬约束。

建议：保持当前范围；下一阶段只做 embedding 接入和阈值标定。未扩大正式产品入口，原因是本任务硬约束要求先完成隔离、真实可复跑和 provenance 证据。
