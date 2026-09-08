# KnowledgeDigest

KnowledgeDigest 是一个人工触发的本地知识消化工具：读取原始 Markdown、文本或 JSON，用用户配置中的 LLM 生成可读业务答案，用 embedding 生成问题入口，最后把 Reader、Home 和 Audit 原子写入新的知识库目录。

## 运行

```bash
uv run --frozen digest NEW_DIR KB_DIR
```

默认读取：

```text
~/.config/knowledge-digest/config.json
```

也可以显式指定配置：

```bash
uv run --frozen digest NEW_DIR KB_DIR --config /path/to/config.json
```

固定质量候选运行（同一次运行覆盖垂直切片、89 条原始资料和 12 个问题投影；不替代正式 M401/M402 门）：

```bash
uv run --frozen digest NEW_DIR KB_DIR \
  --config ~/.config/knowledge-digest/config.json \
  --quality-config config/task5-quality-cases-v2.json
```

Task5 的当前入口只有带 gate 的 `digest` CLI：M401 消费隔离 fixture，M402 才读取批准的 raw、CompanyBrain 和 provider 配置。`scripts/task5_reader_quality.py` 与 `task5_runtime.py` 仅保留历史/回归资料，不是当前生产命令；provider-free preflight 的结果必须由对应 gate attempt 留证，不能用脚本结果替代 M401/M402。

配置中的 `llm` 和 `embedding` 必须提供 `base_url`、`model`、`api_key`，并用 `budget.max_provider_calls` 限制本次所有 provider 请求。Task5 只允许 `https://dashscope.in.whatspos.cn/v1` 的 Qwen `qwen3.8` 和 Jina `jina-embeddings`；密钥只在进程内使用，不写入知识产物。若本机配置仍写着其他模型，运行会在首个请求前阻断，不会偷偷换模型。

## 产物

```text
KB_DIR/
  bundle/
    README.md       # 阅读说明
    Home.md         # 按问题/场景进入
    Audit.md        # 来源、行号和页面回查
    products/       # 可读产品页和主题页
    _audit/
      audit-pages.json
      source-status.json
      companybrain-route-snapshot.json
      semantic-compile-ledger.jsonl
      semantic-response-ledger.jsonl
      route-ledger.jsonl
      raw-coordinate-map.json
      source-not-documented-zero-match.json
      source-not-documented-verifier.json
      run-result.json        # 本次运行身份、来源终态和 provider 统计
      directory-manifest.json
```

Reader 页面正文按定位、概念、操作、诊断、经验组织，并显示产品、模块、对象、场景、边界五轴。质量运行会先为非空来源生成逐源语义页，再生成 12 张固定问题答案页；Embedding 负责问题/场景路由，Qwen 负责逐源语义编译和跨源答案编译。机器 Claim/Block ID 不展示在 Reader 正文，页面末尾可回到具体原始文件和行号。

`completed` 只表示普通运行生成完成；Task5 candidate 也不等于 released。只有 M402 的 host-only quality-result 完成 post-rename finalize 并 promotion，且 89 条来源、四产品、Reader/Audit 和五项逐格严格胜出，才允许 `released`。

运行期间会在终端显示加载、来源页、来源校验、跨来源主题页、路由和发布进度。单个来源或主题失败时仍保留原始快照和可用页面，但运行状态明确为 `not_released`；全局 provider 不可用或预算不足则直接 `unavailable`，不伪装成功。

输出目录必须是新的空目录，避免覆盖已有知识库。
