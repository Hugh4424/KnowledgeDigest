# KnowledgeDigest

KnowledgeDigest 是本地知识消化与发布工具。

普通运行：

```bash
uv run --frozen digest NEW_DIR KB_DIR --config config/knowledge-digest.json
```

每次运行先做 preflight，并把来源快照、逻辑批次、预计 provider calls、运行限制写入
`_digest/runs/<run_id>/plan.json`。运行中的阶段、批次、实际请求、重放、最近错误和心跳写入
同目录的 `progress.json`。终端会显示 preflight 摘要和长运行心跳。

CLI 只有执行状态为 `completed` 时返回 0；`blocked`、`failed`、`cancelled` 都返回非零。
运行执行状态和知识文件的 `page_status`、`writeback`、`delivery_status`、`released/not_released`
是不同概念，不能互相替代。

严格离线运行：

```bash
uv run --frozen digest NEW_DIR KB_DIR --config offline.json --no-llm
```

`--no-llm` 仍会走 preflight，但不会调用模型或 embedding provider。

语义运行默认读取用户级 provider 配置 `~/.config/knowledge-digest/config.json` 的 LLM/embedding URL、model 和 key；也支持 `XDG_CONFIG_HOME`，可用 `--provider-config PATH` 覆盖。环境变量仅作兼容回退，凭据不会写入运行报告。
