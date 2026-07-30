# KnowledgeDigest 开发指南

## 项目是什么

KnowledgeDigest 是一个人工触发的本地知识消化工具：读取 `new_dir/items` 中已声明来源的 Markdown、文本或 JSON，提取可追溯证据，生成主题页和来源索引，再安全写入本地知识库。

核心目标是：不丢内容、能追溯来源、可重复运行、失败不伪装成功。它不是后台任务平台、向量数据库或 AgentMemory 集成层。

## 正确使用

普通单次运行：

```bash
uv run --frozen digest NEW_DIR KB_DIR --config config/knowledge-digest.json
```

严格离线运行（不调用 LLM，也不探测 embedding）：

```bash
uv run --frozen digest NEW_DIR KB_DIR --config offline.json --no-llm
```

`offline.json` 至少包含：

```json
{"similarity":{"backend":"jaccard"},"llm_enabled":false,"llm_summary_enabled":false,"max_lines":300}
```

分批和恢复仍使用同一个 `digest` 命令：

```bash
uv run --frozen digest NEW_DIR KB_DIR --batch-size 8 --batch-state KB_DIR/_digest/batch-state.json
uv run --frozen digest NEW_DIR KB_DIR --batch-state KB_DIR/_digest/batch-state.json --resume
```

状态文件会锁定来源相对路径、URI、内容指纹和首次生成的主题/重复来源计划；来源变了必须新建状态文件，不能强行续跑。

## 实际文件结构

```text
src/knowledge_digest/
  ingest.py        # S1：本地快照、校验、去重
  identity.py      # 稳定来源 ID、主题 ID、分页路径
  cluster.py       # S2：聚类；cluster-N 只是运行审计 ID
  retrieve.py      # S3：检索候选主题页
  draft.py         # S4：Claim、保真检查、可选 LLM 草稿
  page_layout.py   # 最终主题分页、Claim 唯一归属
  writeback.py     # S5：归档、原子写入、移除过期 part
  provenance.py    # S6：来源、Claim、归档溯源
  batch_run.py     # 固定清单、批次状态、失败恢复
  pipeline.py      # 串联 S1–S6 和单写者边界
  cli.py           # digest 命令入口
tests/acceptance/  # 可运行的行为与回归测试
config/            # 默认配置；真实密钥只放环境变量
docs/              # 设计、决策、历史报告
```

核心代码放在 `src/knowledge_digest` 是标准 Python `src-layout`：打包时只导入已安装的项目代码，避免从仓库根目录误导入同名文件，也让测试和正式命令使用同一包。不要把它搬到项目根目录，也不要复制一份 `knowledge_digest` 目录。

## 研发方案

只维护三个深职责边界：

1. `identity.py`：正式主题页绝不能以 `cluster-N`、`draft-N` 或输入顺序命名。
2. `page_layout.py`：先合并完整主题证据，再按 300 行硬上限分页；每个有效 Claim 只能进入一个 part。
3. `batch_run.py`：只保存固定来源清单、固定主题/重复来源计划、批次状态和报告路径；不扩展为调度器、数据库或后台守护。

改动流程：先补能复现问题的测试，再做最小实现；改完跑相关 acceptance 测试，最后跑完整测试。涉及真实语料时先复制到新的 KB 目录，绝不在基线产物上直接回归。

## 质量合同

- 正式主题页包含 `Summary`、`Evidence`、`Provenance`，每页最多 300 行。
- Claim 必须有 `source_uri`、内容指纹、行定位和验证状态；重排后也必须只有一个 `target_path`。
- `_digest/source-index.md` 只写来源和到主题页的相对链接，不复制 Claim、Evidence 或原文。内容重复来源继承 canonical 来源的主题链接。
- 写入前先归档；路径逃逸、软链接、缺失溯源、页面超限和清单变化必须明确失败。
- embedding 不可用时整次回退 Jaccard，不能混用分数。`--no-llm` 不能发出任何 LLM 请求。
- `agentmemory`、调度器、CAS、数据库、向量库不进入正式 `pipeline.py` 或 `digest` CLI，除非先有新的已确认规格。

## 更新规则

当修改 CLI、文件结构、正式输出、质量门禁或开发命令时，同步更新本文件和对应 acceptance 测试。保留 `docs/plans/universal-knowledge-digest-design.md` 作为原始设计；本次已交付架构优化的规格、计划和任务记录归档于 `specs/archive/knowledge-digest-architecture-optimization/`。
