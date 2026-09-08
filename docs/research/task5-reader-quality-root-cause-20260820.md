# Task5 Reader-quality 根因调查（2026-08-20）

## 结论

Task5 的真实产物没有走 KnowledgeDigest 原有的 LLM/embedding 语义链。它把原始 Markdown 解析成 block/claim，再套固定路由；六个质量 case 的答案由配置文件预先提供，其余非空来源直接生成 `full-source` 页面。因此当前结果是“目录包装 + 少量手写答案样板 + 大量原文搬运”，不是完整知识消化。

仓库里的原始 LLM/embedding 实现没有被删除，但 Task5 通过独立入口绕开了它们；从用户交付结果看，等价于能力丢失。

## 事实证据

### 原有 KnowledgeDigest 能力

- `src/knowledge_digest/config.py` 默认 `llm_enabled=false`，只有显式配置或 `KD_LLM_FORMAT` 才打开 LLM。
- `src/knowledge_digest/draft.py` 的 `resolve_generator()` 在 LLM 打开时调用 `llm.generator_from_env`；关闭时才使用 identity generator。
- `src/knowledge_digest/llm.py` 实现 OpenAI/Anthropic-compatible 请求、qwen3.6 JSON 约束、超时和输出校验。
- `scripts/task3_semantic_compile.py` 直接调用 `call_llm()`，默认模型为 `qwen3.6`，端点为 `https://dashscope.in.whatspos.cn/v1`。
- `src/knowledge_digest/embedding.py` 实现 OpenAI-compatible `/embeddings` 客户端、模型/维度/探针/校准绑定；`pipeline.py` 在 S2/S3 使用它做聚类和检索，失败时按旧合同记录 Jaccard fallback。
- CLI 默认只读取项目 `config/knowledge-digest.json`，目前没有自动读取 `/Users/Hugh/.config/knowledge-digest/config.json` 的逻辑。

### Task5 实际调用链

`scripts/task5_reader_quality.py` → `task5_runtime.run_task5()` → `build_source_inventory()` → `compile_semantic_bundle()` → `project_semantic_bundle()` → `_write_bundle_route_files()`。

该入口没有调用 `resolve_settings()`、`resolve_generator()`、`call_llm()`、`resolve_similarity_backend()` 或 embedding client。Task5 计划还明确写了“不新增 provider”和“真实全量测试不调用 LLM/embedding”。这是方案设计选择，不是 provider 当时不可用的结论。

### Task5 为什么会生成原文堆积

- 全量编译器为每个非空来源强制创建 `full-source` projection。
- `full-source` 投影把 source claims 作为正文候选。
- `_reader_text()` 只是清理 Markdown 外壳，不是摘要器。
- `KnowledgeUnit` 的 module 取 raw 顶层目录，scene/boundary 默认空；六个 Q case 的业务字段来自 `task5-quality-cases-v1.json`，不是从 89 条来源自动推导。
- `_route_chain()` 固定生成 `modules`、`boundaries`、`knowledge` 等路径；没有正文的节点仍会写导航空壳。

这解释了 v50 的事实：103 个 knowledge 页面中 88 个是 `full-source`；modules/boundaries 大多数只是几行链接；515/539 个 Markdown 文件名带 8 位 hash；质量报告虽然写 `strict_all_kd_win=true`，但 `G-EMPTY-89`、`G-COVERAGE-89`、`G-SLICE-RISK` 仍 blocked，包状态是 `not_released`。

### v50 的真实交付路径

用户实际查看的包是：

`/private/tmp/task5-reader-quality-real-v50/staging/run-c176c1a764c9616742f302e9/attempt-2d149140466c408ba6271ab7f53854de/candidate-bundle`

其 `run.json` 的状态是 `not_released`，`candidate_bundle_dir` 指向 staging 下的 candidate，`status.json` 明确 `official_bundle_updated=false`。Task5 CLI 要求调用者传入 `--output`；本次 output 是 `/tmp/task5-reader-quality-real-v50`，运行时只是把 candidate 写到该 output 的 staging 子目录，没有把可检查的 candidate 原子复制到 Downloads。这是交付路径缺陷。

### CompanyBrain 当前生成方式

当前 CompanyBrain 的 EMM 生成脚本没有发现 LLM 调用：

- `tools/synthesize_emm_guides.py` 直接定义产品定位、使用场景、能力边界、高频问法、开通步骤、前置条件、排查路径和来源线索等业务页正文。
- `tools/generate_product_retrieval_guides.py` 生成常见问答入口、关键词和推荐入口，避免把完整正文复制到路由页。
- `automation/run_daily_import.sh` 先清洗/整理/审计，再运行这些合成脚本；Confluence 原文批量生成脚本目前还被注释，原因就是可读性不足。
- 同一脚本在有 `OPENAI_API_KEY` 时运行 `gbrain embed --stale`。这里 embedding 主要服务检索，不负责写业务答案。

因此 CompanyBrain 的可读性主要来自“稳定的业务本体、人工/脚本定义的答案结构、问题入口和边界页”，而不是“调用了 LLM 就自动变好”。KnowledgeDigest 应吸收这个输出合同，同时让 Qwen 负责把原始 89 条资料规模化抽取为事实和答案候选。

## 修复约束

1. 生成输入只能是 `/Users/Hugh/Downloads/confluence 原始数据`；CompanyBrain 只能作为只读比较基线和结构参考，不能向 Reader 补事实。
2. 语义运行必须实际调用 qwen3.6 和 embedding，并记录 provider/model/endpoint/call receipt；`--no-llm`/Jaccard 只能是离线回归，不能标记为语义发布。
3. 原文只能进入 Audit/SourceArchive；Reader 禁止 `full-source` fallback。无法编译成答案时必须 `degraded/not_released`，不能换个目录名伪装完成。
4. 五维比较必须打开真实 candidate 和 CompanyBrain 文件，记录页级、维度级、文件行号和 hash；配置里的 `strict_advantage=true` 或非空占位 evidence 不能成为 verdict。
5. candidate 即使被质量门阻断，也必须落到 `/Users/Hugh/Downloads/KnowledgeDigest-reader-quality-real-<date>-<run_id>/`，并明确 `candidate/not_released`；临时目录只做 staging。

## 设计方向

把 Task5 的固定投影器替换为 Reader Semantic Compiler：raw snapshot → embedding 分块/聚类/检索 → Qwen 结构化事实抽取 → 事实验证与冲突处理 → 五类业务答案页编译 → Home 问题路由 → Reader/Audit 分离 → 五维比较 → Downloads 原子发布。公开路径使用可读语义 slug，稳定 hash 只保留在 frontmatter、Audit 和 manifest。
