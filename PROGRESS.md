# Progress

- 目标：消除同批次增量写回丢失，按目标页一次聚合写回。
- 基线：phase0 33 passed；全套 131 passed，0 skipped。
- 范围：仅改允许文件；`pipeline.py` 已撤销本任务改动；现有未跟踪文件未触碰。
- 顺序：初始 5 项、复验 7 项均先红，再修实现，最后指定验收。
- 最大风险：draft/writeback/provenance 耦合；保留路径安全、归档、原子写、faithfulness 门禁。
- 任务 1：5 个测试先红；原始 focused 输出 `5 failed, 33 passed in 1.18s`。
- 任务 2：全部目标保留；按目标聚合、去重、一次归档/原子写；S6 按目标映射。
- 任务 3：复验三项 `3 failed, 38 passed`，新增四项 `4 failed, 41 deselected`；已修 frontmatter、long evidence、归档重放、代码围栏、标题识别、contributors。
- 末两项先红：`2 failed, 44 deselected`；已修 symlink 逃逸与格式化 claim 去重；phase0 `46 passed`，全套 `144 passed`、`0 failed`、`0 skipped`。

## LLM raw_id 契约

- 基线：LLM `39 passed`；全套 `144 passed`。
- 根因：prompt 的 claims schema 漏写 `raw_id`，真实 provider 按 schema 返回后被 lineage 门拒绝。
- 方案：schema 明示 `raw_id`；仅在 fingerprint/text/source/fragment 精确且唯一匹配时恢复内部 lineage，冲突 ID 仍拒绝。
- 首次真实 qwen 验证：3 个 draft 均 `selected_round=1`、无 fallback；随后 S5 因 provider 未返回内部 provenance 字段而明确失败，已纳入同一恢复边界。
- 第二次真实 qwen 验证：3/3 draft `selected_round=1`、0 fallback；2/2 目标页写入成功；S6 24 条 provenance 全字段完整。
- 安全复审后收紧：完整源记录必须唯一；provider 伪造的内部 provenance 一律覆盖或删除；LLM `42 passed`，全套 `147 passed`。
