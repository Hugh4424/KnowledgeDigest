# KnowledgeDigest 开发指南

## 项目是什么

KnowledgeDigest 是一个人工触发的本地知识消化与发布工具：读取 `new_dir/items` 中已声明来源的 Markdown、文本或 JSON，提取可追溯证据，生成可读主题页、分类导航和来源索引，再安全写入本地知识库。

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

Task1 主题轴是 `kb.structure.md` 中 `topic_axis_enabled: true` 的显式 opt-in 结构运行：

```bash
uv run --frozen digest NEW_DIR KB_DIR --config offline.json --no-llm
```

它只写 `_digest/source-inventory.jsonl`、`_digest/topic-plan.json`、`_digest/topic-index.json` 和 `_digest/runs/<run_id>.json`，状态为 `not_released`，不写 Home、分类页或主题正文；Task1 opt-in 不支持旧的逐批正文写入。

真实 89 条语料的验收不会提交原始文件；需要显式设置 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 指向本机原始目录。`kb.structure.md` 的 Task1 设置读取受控 frontmatter 中的单行标量（`key: value`，可用简单单引号或双引号）；不支持行内注释、嵌套 YAML 或复杂值，遇到不支持的格式应先修正输入。

`offline.json` 至少包含：

```json
{"similarity":{"backend":"jaccard"},"llm_enabled":false,"llm_summary_enabled":false,"max_lines":300}
```

新知识库可直接发布：命令会建立默认的 `kb.structure.md`、`Home.md`、`indexes/pending.md`，再写入主题页。旧知识库只做增量新增和更新：必须已有有效的 `kb.structure.md`，且 KnowledgeDigest 只管理其中声明的目录和带 `managed_by: KnowledgeDigest` 标记的文件。

分批和恢复仍使用同一个 `digest` 命令：

```bash
uv run --frozen digest NEW_DIR KB_DIR --batch-size 8 --batch-state KB_DIR/_digest/batch-state.json
uv run --frozen digest NEW_DIR KB_DIR --batch-state KB_DIR/_digest/batch-state.json --resume
```

状态文件会锁定来源相对路径、URI、内容指纹和首次生成的主题/重复来源计划；来源变了必须新建状态文件，不能强行续跑。

发布结果目录的阅读顺序：先读 `README.md`，再从 `Home.md` 进入 `indexes/<parent>.md` 和叶分类页，最后打开 `pages/<领域>/<分类>/<主题>.md`。`_digest/source-index.md` 只保存来源、指纹、状态和主题页链接；`_digest/runs/` 是运行审计；`_archive/` 是历史快照，不是当前阅读入口。

生成固定对比报告（只读，不调用模型）：

```bash
uv run python scripts/task2_publication_comparison.py \
  --task1 /path/to/task1/company-kb \
  --task2 /path/to/task2/company-kb \
  --companybrain /Users/Hugh/Hugh/Knowledge/CompanyBrain \
  --output /path/to/task2-comparison
```

需要语义发布时只允许使用项目配置约定的 `qwen3.6`（`https://dashscope.in.whatspos.cn/v1`）和 `jina-embeddings`（`https://llm.paxszapp.com/v1`）；默认从用户配置 `~/.config/knowledge-digest/config.json` 读取 URL/model/key，也支持 `XDG_CONFIG_HOME`，环境变量只作兼容回退。凭据禁止写入代码、结果、报告或缓存。离线回归使用 `--no-llm` + Jaccard，不触碰任何 provider。

每次运行都会先做 preflight，并在 `_digest/runs/<run_id>/plan.json` 写入来源数、逻辑批次、预计 provider calls 和显式限制；运行中可读状态在同目录 `progress.json`，每 10 秒更新一次。`completed` 才返回退出码 0；`blocked`、`failed`、`cancelled` 都返回非零。运行执行状态只描述本次执行，不等同于知识文件或 `released/not_released` 状态。

## 实际文件结构

```text
src/knowledge_digest/
  ingest.py        # S1：本地快照、校验、去重
  identity.py      # 稳定来源 ID、主题 ID、分页路径
  cluster.py       # S2：聚类；cluster-N 只是运行审计 ID
  retrieve.py      # S3：检索候选主题页
  draft.py         # S4：Claim、保真检查、可选 LLM 草稿
  publication.py   # 语义标题/分类/摘要建议校验与 fail-closed fallback
  navigation.py    # README/Home/分类索引/来源索引的读者渲染
  page_layout.py   # 最终主题分页、可读路径和 Home/分类导航记录
  topic_axis.py    # Task1：结构 inventory、ProductGazetteer、TopicPlan/Index、affected/conflict 审计
  writeback.py     # S5：Home/分类/主题同批归档后原子发布，不删除旧 part
  provenance.py    # S6：来源、Claim、归档溯源
  batch_run.py     # 固定清单、批次状态、失败恢复
  pipeline.py      # 串联 S1–S6 和单写者边界
  cli.py           # digest 命令入口
tests/acceptance/  # 可运行的行为与回归测试
config/            # 默认配置；真实密钥只放环境变量
docs/              # 设计、决策、历史报告
scripts/task2_publication_comparison.py # 只读生成 Task1/Task2/CompanyBrain 对比报告
```

核心代码放在 `src/knowledge_digest` 是标准 Python `src-layout`：打包时只导入已安装的项目代码，避免从仓库根目录误导入同名文件，也让测试和正式命令使用同一包。不要把它搬到项目根目录，也不要复制一份 `knowledge_digest` 目录。

## 研发方案

只维护三个深职责边界：

1. `identity.py`：正式主题页绝不能以 `cluster-N`、`draft-N` 或输入顺序命名。
2. `page_layout.py`：先合并完整主题证据，再按 300 行硬上限分页；每个有效 Claim 只能进入一个 part；离线标题依次取既有托管标题、来源 metadata title/H1、文件名。
3. `batch_run.py`：只保存固定来源清单、固定主题/重复来源计划、批次状态和报告路径；不扩展为调度器、数据库或后台守护。

改动流程：先补能复现问题的测试，再做最小实现；改完跑相关 acceptance 测试，最后跑完整测试。涉及真实语料时先复制到新的 KB 目录，绝不在基线产物上直接回归。

## 质量合同

- 正式主题页包含 `Summary`、`Evidence`、`Provenance`，每页最多 300 行。
- 主题页路径和标题可读，但页头保留稳定 `digest_topic_id`、`digest_published_path` 与托管标记；已发布路径不会因日常更新改名。
- `Home.md → indexes/<category>.md → 主题页` 是读者入口；每次增量会保留未参与本次处理的合法托管主题链接。
- Claim 必须有 `source_uri`、内容指纹、行定位和验证状态；重排后也必须只有一个 `target_path`。
- `_digest/source-index.md` 只写来源和到主题页的相对链接，不复制 Claim、Evidence 或原文。内容重复来源继承 canonical 来源的主题链接。
- 写入前先归档；Home、分类和主题页同一事务发布。只允许 `kb.structure.md` 声明路径；手写文件、路径逃逸、软链接、页头路径不符、缺失溯源、页面超限和清单变化必须明确失败。
- 旧知识库只新增或更新，不删除旧主题页或旧分页；主题收缩时旧 part 保留归档价值，但不再出现在当前分类导航。
- embedding 不可用时整次回退 Jaccard，不能混用分数。`--no-llm` 不能发出任何 LLM 请求。
- Task1 主题轴在 provider 前冻结；canonical 词表、语义 key、旧路径映射、affected set 和人工 hash 冲突均需可追溯，degraded 不得伪装成已发布。
- `agentmemory`、调度器、CAS、数据库、向量库不进入正式 `pipeline.py` 或 `digest` CLI，除非先有新的已确认规格。

## 更新规则

当修改 CLI、文件结构、正式输出、质量门禁或开发命令时，同步更新本文件和对应 acceptance 测试。保留 `docs/plans/universal-knowledge-digest-design.md` 作为原始设计；已交付的知识发布合同记录归档于 `specs/archive/knowledge-digest-publication-contract/`，架构优化记录归档于 `specs/archive/knowledge-digest-architecture-optimization/`，Task2 知识发布架构记录归档于 `specs/archive/knowledge-digest-llm-naming-classification/`。
