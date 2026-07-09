# 开源项目调研：增量知识消化（去重/聚类 → LLM 提炼合并 → 结构化更新）

调研日期：2026-07-05
场景约束：本地可跑、依赖轻、支持增量更新（非全量重建索引）、LLM 驱动内容整合（不只是向量检索）

---

## 1. Microsoft GraphRAG

- **核心机制**：CLI `graphrag update` 命令（v1.0+）计算新增内容与已有索引的 delta，LLM 抽取实体/关系后合并进图，必要时重算受影响的 community（社区摘要），避免全量重建。
- **依赖重量**：中等偏重。Python 3.11-3.13，默认用 LanceDB 做本地向量存储，无需外部数据库即可跑；但 community 检测/摘要机制复杂，图和摘要随语料超线性增长，内存/成本会滚雪球。
- **增量更新支持**：原生支持（`update` 子命令），但设计上只支持"追加"内容，不支持删除/人工编辑/按 delta 打标签查询；小版本升级需要 `graphrag init --force` 迁移配置。
- **许可证**：MIT
- 来源：https://github.com/microsoft/graphrag ，https://github.com/microsoft/graphrag/discussions/511 ，https://microsoft.github.io/graphrag/cli/

## 2. LightRAG (HKUDS)

- **核心机制**：新数据只走一次标准图索引管道生成"local graph"，再通过 set merging 直接并入已有全局图，无需重建；论文/综述提到 Delta Index 机制用后台合并线程处理新增实体/边，跳过 community 重建这一层。
- **依赖重量**：轻。Python 3.10+，默认文件持久化的内存态存储（KV/向量/图/文档状态四类），开发环境零外部数据库依赖；生产可选 Postgres/Mongo/Milvus+Neo4j。嵌入模型推荐用轻量本地模型（如 BAAI/bge-m3）。
- **增量更新支持**：原生且是其核心卖点——号称比传统 RAG 更新处理时间减少约 70%，索引 token 成本降约 60%。
- **许可证**：MIT
- 来源：https://github.com/hkuds/lightrag ，https://arxiv.org/abs/2410.05779 ，https://lightrag.github.io/

## 3. Graphiti (Zep 开源核心)

- **核心机制**：双时态（bi-temporal）知识图谱，实时增量摄取每条 episode，用时间元数据做冲突消解而非重算全图；语义边与情景记忆双向索引，支持溯源引用。
- **依赖重量**：中等。需要一个图数据库后端（Neo4j / FalkorDB / Neptune / 已弃用的 Kuzu），有 `graphiti-core[falkordblite]` 嵌入式选项（Python 3.12+，无需独立服务），可配合 Ollama/vLLM 等 OpenAI 兼容端点做本地 LLM。
- **增量更新支持**：原生强项——专为持续增量摄取设计，不是"批量重建 + 偶尔增量"的补丁方案；小模型的结构化 JSON 输出不稳定会影响抽取质量。
- **许可证**：Apache-2.0
- 来源：https://github.com/getzep/graphiti ，https://arxiv.org/abs/2501.13956 ，https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/

## 4. mem0

- **核心机制**：`add()` 时用 LLM 做 FACT_RETRIEVAL + UPDATE_MEMORY 两段式 prompt，决定新事实是 ADD/UPDATE/DELETE，从而在写入时就完成去重和合并（而非后处理）。
- **依赖重量**：轻到中。核心包依赖 qdrant-client/pydantic/openai 等，按需装 extras（向量库、LLM provider、spacy）；必须有一个 LLM（默认 gpt-4o，可换本地模型）。
- **增量更新支持**：设计上是增量优先（一条条对话处理），但第三方分析指出去重"不完全自动"，相似记忆仍可能堆积，依赖简单的 recency/LRU 兜底。
- **许可证**：Apache-2.0（托管平台另有商业条款，免费版会拿用户数据训练模型，需注意）
- 来源：https://github.com/mem0ai/mem0 ，https://arxiv.org/html/2504.19413v1 ，https://docs.mem0.ai/open-source/overview

## 5. Cognee

- **核心机制**：六阶段 cognify 管道（分类→分块→LLM 抽取实体关系→摘要→嵌入→图写入），默认开 `incremental_loading=True`，两层去重：add() 阶段内容哈希去重，cognify() 阶段按 pipeline 状态跳过已完成项（无 LLM 调用/无重嵌入/无图写入）。
- **依赖重量**：中等。支持 NetworkX（纯本地无外部依赖）/FalkorDB/Neo4j 多种图后端，30+ 数据源连接器，可先本地跑后续按需上云。
- **增量更新支持**：原生且分层设计相对成熟，但 `improve()`（改本体/ontology）是全量重建，无增量；部分场景仍是"清空重灌"而非真增量删除。
- **许可证**：Apache-2.0
- 来源：https://github.com/topoteretes/cognee ，https://docs.cognee.ai/core-concepts/main-operations/legacy-operations/cognify

## 6. txtai

- **核心机制**：纯嵌入数据库 + 可选 LLM 编排层，本身不做"LLM 驱动的合并/冲突消解"，增量能力停留在索引增删记录层面（upsert/delete API），去重判断需要自己在其上层编排。
- **依赖重量**：很轻。Python 3.10+，核心只需 Transformers/Sentence-Transformers/FastAPI，模块化按需装依赖，可本地跑、可容器化。
- **增量更新支持**：支持增量 upsert，但**不是**"LLM 提炼合并"式的知识整合，只是向量索引的增删——不满足硬约束里"不只是向量检索"这一条。
- **许可证**：Apache-2.0
- 来源：https://github.com/neuml/txtai ，https://neuml.github.io/txtai/embeddings/indexing/

## 7. Khoj

- **核心机制**：经典 RAG 管道——文件哈希+修改时间判断增量，只重新处理变更文件，生成嵌入存入 pgvector，查询时做语义检索后交给 LLM。
- **依赖重量**：中等（需要 Postgres+pgvector，支持 Docker Compose 一键起）。
- **增量更新支持**：文件级增量（只处理变更文件），但**没有**知识库内部的去重/聚类/合并机制——它是"个人第二大脑问答工具"而非"知识库整理引擎"，定位不匹配。
- **许可证**：AGPL-3.0（注意：非 Apache/MIT，商业二次分发有传染性限制）
- 来源：https://github.com/khoj-ai/khoj

## 8. HippocampAI

- **核心机制**：自治记忆引擎，v0.5.1 加了显式去重（dedup）端点和批量 API，支持开启后"夜间自动整合（nightly consolidation）"。
- **依赖重量**：未知细节（文档信息有限），推测中等（Python 服务 + API）。
- **增量更新支持**：有专门的去重/整合端点，设计目标即增量场景，但项目成熟度、社区规模、生产验证程度不明，需谨慎评估。
- **许可证**：Apache-2.0
- 来源：https://github.com/rexdivakar/HippocampAI

## 9. Karpathy LLM-Wiki 模式（非项目，是工作流范式）

- **核心机制**：不做向量检索，而是让 LLM 把原始资料一次性编译成结构化 Markdown wiki；"merge" 操作专门解决重复概念——LLM 读两篇重复文章，合并成一篇干净版本，更新反向链接，旧文章归档并留重定向说明，每次合并一个 git commit。
- **依赖重量**：极轻——本质是一个 Claude Code / Cursor / Codex 的 Agent Skill + CLAUDE.md 规范，加 Git 做版本控制，Obsidian 做查看器，无需额外服务栈。
- **增量更新支持**：天然增量（新资料来了就 compile 一次，触发时才 merge/reflect），但**没有自动去重判断**——依赖人或 agent 主动发现重复概念再触发 merge，没有内置的"新记录进来自动比对已有知识"的调度逻辑。
- **许可证**：模式本身无许可证概念；社区实现各自独立仓库（如 Astro-Han/karpathy-llm-wiki，通常 MIT）。
- 来源：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f ，https://louiswang524.github.io/blog/llm-knowledge-base/ ，https://github.com/Astro-Han/karpathy-llm-wiki

## 10. RecMem / SimpleMem（2026 学术项目，仅供借鉴思路）

- **核心机制**：RecMem 把交互先存入"潜意识层"，只有语义相似的交互反复出现（recurrence）才触发 LLM 做情景/语义记忆抽取，减少不必要的 LLM 调用；SimpleMem 用三段式管道（语义压缩→递归式记忆整合→自适应检索），"递归整合"异步地把相关记忆单元合并成更高层摘要以降低冗余。
- **依赖重量**：研究代码，非生产级框架（RecMem 在 github.com/CaiusDai/RecMem，SimpleMem 在 aiming-lab/SimpleMem），文档/易用性未知。
- **增量更新支持**：核心论文贡献就是"何时触发整合"的增量调度策略，思路很贴合本场景，但工程化程度低，不建议直接引入生产。
- **许可证**：待查（学术仓库常见 MIT，需逐个确认）
- 来源：https://arxiv.org/html/2605.16045 ，https://arxiv.org/html/2601.02553v1

---

## 推荐 Top 3

1. **LightRAG**（首选）——理由：依赖最轻（默认零外部数据库）、增量合并是核心设计（set merging + 增量 patch）、MIT 许可、LLM 驱动的实体/关系抽取天然带有"去重合并"语义，本地用一个中等开源模型（30B 级）即可跑通。最贴合"本地跑 + 依赖轻 + 增量 + LLM 整合"四条硬约束。

2. **Graphiti（Zep 开源核心）**——理由：专为持续增量摄取设计（非"批量重建改造成增量"），有 FalkorDB 嵌入式选项做到近乎零外部服务依赖，双时态设计天然支持"新记录 vs 已有知识"的冲突判断和更新（而非只是追加）。Apache-2.0。如果场景强调"时间线/版本演进"（记录是会变化/过时的知识而非静态文档），比 LightRAG 更合适。

3. **Cognee**——理由：内容哈希 + pipeline 状态两层去重是内置的、开箱即用，NetworkX 后端可以做到真正零外部数据库依赖，Apache-2.0，模块化管道方便按需替换某一步（比如换掉它的 LLM 合并逻辑接自己的 prompt）。成熟度和文档完整度介于 LightRAG 和研究型项目之间，适合想要"六阶段管道现成骨架、自己改抽取/合并 prompt"的场景。

**次优可选**：mem0 若场景是"对话式、单条记忆流"而非"文档聚类"更合适，但去重非完全自动，需要自己补冲突消解逻辑。

## 只值得借鉴思路、不建议直接引入

- **Karpathy LLM-Wiki 模式**：merge 操作的"合并两篇文章+归档重定向+单独 git commit"设计非常值得抄，但它没有自动触发去重判断的调度层，直接搬要自己补"新记录进来时该不该 merge"的判断逻辑——等于只借鉴了"整合"这一半，"判断"那一半要自己写。
- **khoj**：定位是问答工具而非知识库整理引擎，且 AGPL 许可有传染性风险，不建议作为底层引入，但它"文件哈希+mtime 判断增量"的简单实现值得抄。
- **txtai**：不满足"LLM 驱动整合"的硬约束（只是向量库），不建议作为核心方案，但其"模块化按需加依赖"的工程方式值得参考。
- **RecMem / SimpleMem**：思路（recurrence 触发整合、递归式记忆压缩）对"什么时候该整合"这个调度问题有启发，但学术代码不建议直接生产引入。
- **HippocampAI**：功能对口但成熟度未知，建议先观察社区活跃度，暂不作为首选。
