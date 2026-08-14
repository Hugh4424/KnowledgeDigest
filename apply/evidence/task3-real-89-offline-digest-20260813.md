# Task3 真实 89 条语料离线入口证据

- 日期：2026-08-13
- 原始语料：`/Users/Hugh/Downloads/confluence 原始数据`
- 输入绑定：89 条 Markdown；使用已有 `source-declarations.jsonl` 固定来源清单；`.DS_Store` 未进入清单
- 命令：

  ```bash
  KNOWLEDGEDIGEST_TASK1_RAW_CORPUS="$REAL_ROOT/items" \
    uv run --frozen digest "$REAL_ROOT" "$REAL_ROOT/kb" \
    --config "$REAL_ROOT/offline-config.json" --no-llm
  ```

- 实际结果：命令退出码 `0`
- 运行 ID：`run-topic-axis-bd47a2e7a52700d4`
- 来源数：`89`
- 主题数：`54`
- 主题状态：`published=31`、`degraded=23`
- 合并方式：`single=23`、`merge=8`、`degraded=23`
- 冲突：`0`
- 警告：`0`
- Provider/LLM：使用 `--no-llm`，没有调用 provider
- 输出：`_digest/source-inventory.jsonl`、`_digest/topic-plan.json`、`_digest/topic-index.json`、`_digest/runs/run-topic-axis-bd47a2e7a52700d4.json`
- 发布状态：`not_released`

## 这条证据能证明什么

它证明真实 89 条语料可以进入当前离线 Task1 结构入口，来源清单、主题规划和审计报告能写出，且没有把离线结构结果标成正式发布。

## 这条证据不能证明什么

它不是 Task3 的完整 `bundle/`、`audit/`、`reports/` 候选包；没有证明 Task3 语义页、17+3 语义质量边界、摘要确认、正式根目录读回或 provider-backed 运行。因此不能把 `not_released` 改成 `released`。

临时运行目录：`/tmp/kd-task3-real-offline.hhSktP`。该目录只用于本次运行读回，不作为正式交付物。
