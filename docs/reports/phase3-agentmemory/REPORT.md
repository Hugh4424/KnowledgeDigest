# KnowledgeDigest Phase 3 双库验收报告

日期：2026-07-28

复跑命令：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --frozen python scripts/phase3_agentmemory_acceptance.py \
  --source-dir '/Users/Hugh/Downloads/confluence 原始数据'
```

1. **事实：输入隔离成功。** 原始目录发现 89 个 Markdown；固定 3 个新输入全部复制到隔离 `new-input/items`，其余页面复制到隔离 `company-kb/pages`。选中文件 SHA-256、隔离 company-kb 页面 hash、原始目录前后 manifest 均已保存。完整 receipt：`/tmp/kd-phase3-agentmemory-run.26823/receipt.json`；页面 hash 文件：`/tmp/kd-phase3-agentmemory-run.26823/company-kb-pages.sha256`。

2. **事实：company-kb 正式验收成功。** `--no-llm --dry-run` 和正式运行退出码均为 0；3/3 新输入被接受，4/4 formal outputs 的状态均为 `success`。正式报告：`/tmp/kd-phase3-agentmemory-run.26823/company-kb/_digest/runs/run-e3666a46d39e4f14b2841edd0b6623f3/report.json`。

3. **事实：agentmemory 隔离 REST 验收成功。** disposable 实例使用独立 `HOME`、`iii-config.yaml`、state/stream 路径和端口 `60730/14707/14708/14709`；`livez` 为 `status=ok`，官方 REST + `AgentMemoryStore` 首次写入 58 条唯一记忆，3 个来源均可搜索读回。LLM 和 embedding 均禁用；真实 agentmemory manifest 未变化，disposable worker 和 engine 均停止。

4. **事实：replay 和 provenance 反向验证成功。** 原样 replay 为 `created=0`、`duplicate=94`、记忆数 `58 -> 58`；provenance 校验为 `before exit_code=0, missing=0`，删除后 `exit_code=1, missing=2`，REST 恢复后 `exit_code=0, missing=0`。证据：`/tmp/kd-phase3-agentmemory-run.26823/provenance-reverse.json`。

5. **判断与未验证项：Phase 3 验收通过。** 本阶段只更新设计计划并提供隔离验收，不接入正式 `pipeline.py`、`cli.py` 或生产入口；未验证 embedding 质量、阈值效果和真实 agentmemory 数据迁移。下一步只剩 embedding 接入和阈值标定。
