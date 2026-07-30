# KnowledgeDigest 架构优化任务

## 执行状态填写区（唯一完成权威）

本文件记录真实实现、测试和评审事实。原 WorkflowHub 规格 receipt 已冻结在旧快照，因此本次不写入或伪造正式 stage receipt。

### T1：稳定身份

- [x] status: completed
- 改动：新增 `identity.py`；来源、主题和分页路径不再依赖输入顺序、`cluster-N` 或 `draft-N`。
- 覆盖：AC-01、AC-02
- 测试：`test_architecture_optimization.py` 的顺序稳定与重跑断言；全量测试 254 passed。

### T2：最终布局、来源索引与写回

- [x] status: completed
- 改动：新增 `page_layout.py`；最终页硬性 300 行、Claim 唯一归属、来源索引仅保留来源和主题链接；写入失败会回滚已写分页。
- 覆盖：AC-03、AC-04、AC-05、AC-06、AC-07、AC-09
- 测试：覆盖重复行定位、内容修订、分页回滚、来源索引和 300 行上限；全量测试 254 passed。

### T3：批次清单与恢复

- [x] status: completed
- 改动：新增 `batch_run.py` 和同一 `digest` 命令的 `--batch-size` / `--batch-state` / `--resume`；固定全局聚类和重复来源计划，拒绝变更的输入清单。
- 覆盖：AC-08、AC-10、AC-12
- 测试：覆盖失败后恢复、输入变更拒绝、全量与分批结果一致；全量测试 254 passed。

### T4：AGENTS.md 与离线验收

- [x] status: completed
- 改动：新增根 `AGENTS.md`，说明项目、使用方式、研发边界、实际文件结构和更新规则。
- 覆盖：AC-11、AC-13
- 测试：89 篇真实输入在全新 KB 上强制无 LLM、明确 Jaccard 完整运行；结果在 Downloads 的最终回归目录。
