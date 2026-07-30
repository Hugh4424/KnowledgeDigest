# KnowledgeDigest 架构优化实施计划

> 说明：原 WorkflowHub 的 `build-spec` receipt 绑定了早于 AGENTS.md 要求的快照，不能安全补绿。本计划直接落实用户已确认的规格；不把它伪装成正式 stage receipt。

## 实施原则

- 保留 `src/knowledge_digest` 标准 Python src-layout。
- 只新增三个职责边界：稳定身份、最终页面布局、批次运行。
- 页面、Evidence、Provenance、归档和单写者合同优先于兼容临时文件名。
- 最终验收只允许离线、`--no-llm` 路径。

## 阶段一：稳定身份

新增 `identity.py`，用规范化来源 URI 生成稳定来源 ID；用已归属来源集合生成主题 ID。`cluster.py`、`draft.py` 只传递该 ID，不再把 `cluster-N`、`draft-N` 用作正式页面身份。

完成标准：同一来源集合换顺序仍得到相同主题 ID；已有主题会保留其主题 ID；碰撞明确失败。

## 阶段二：最终页面布局和来源索引

新增 `page_layout.py`，在读取旧主题页和合并本批 Claim 后再做确定性分页。每个 part 都带完整 Evidence/Provenance，最多 300 行；Claim 恰好属于一个 part。`writeback.py` 只负责验证、归档、原子物化和清理过期 part。

来源索引写入 `_digest/source-index.md`，每个有效来源一条，只含来源标识和相对主题页链接；JSONL 审计记录保持为兼容输出。

完成标准：最终页硬上限、无截断、无重复结构、索引链接可达，替换和减少分页先归档。

## 阶段三：轻量批次恢复

新增 `batch_run.py`，CLI 可用 `--batch-size` 与 `--batch-state` 运行。状态文件只保存固定来源清单、固定主题/重复来源计划、每批状态和报告路径。恢复时重新核对来源 URI、相对路径和内容指纹；变化即拒绝，且不重新计算主题计划。成功批次跳过，失败和未运行批次重跑。

完成标准：中断后可恢复、成功批次不重复、清单变化失败明确；不新增后台队列或调度器。

## 阶段四：文档、回归与真实语料验证

新增根级 `AGENTS.md`，说明项目定位、命令、开发方法、实际目录、质量门禁和维护更新规则。补齐针对身份、布局、索引、批次和无 LLM 网络门禁的测试；执行完整 pytest 和 89 篇离线真实语料回归。

完成标准：全部测试通过；真实语料来源 accounted、索引和分页合规、无 LLM HTTP；将结果与改造前无 LLM 基线比较。
