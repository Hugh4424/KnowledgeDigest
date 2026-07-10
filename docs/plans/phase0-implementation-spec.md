# Phase 0 Knowledge Digest Implementation Spec

## 速读卡

一句话需求：Phase 0 只交付手动触发的 `digest(new_dir, kb_dir)` 单库最小闭环，把一批新材料安全消化进一个文件夹式 Markdown 知识库。

核心改动：定义 CLI 合约、`new_dir` 和 `kb_dir` 最小目录约定、KB 结构约定描述文件、S1-S6 阶段输入输出、防信息丢失硬约束和可构造验收样本。

档位判断：B 档。原因是交付物是规格文档，但内容横跨 CLI、目录契约、数据文件、六段管线、写回语义和验收设计，属于跨模块机制设计；不引入外部系统或破坏性变更，所以不是 C 档。

F10 四问结论：真实威胁是 CompanyBrain 式硬截断、规则性丢弃、空壳来源引用和写回中断造成的信息丢失；现有材料只有设计草案，没有可执行 Phase 0 合约；这些约束不能被简单绕过，因为验收样本会检查输出文件和来源字段；长期维护成本可控，因为本期只用文件约定、队列文件和原子写回，不加调度、图数据库、CAS、journal 或持久重试队列。

## 问题陈述

现有设计草案已经收敛到 `digest(new_dir, kb_dir)`，但仍偏设计说明，不能直接指导开发者实现 Phase 0。下游需要知道命令怎么调用，两个目录如何组织，每个阶段读写哪些文件，哪些防丢失规则必须第一期实现，以及如何验收跑通且没有明显信息丢失。

## 背景与目标

Phase 0 目标是单库最小闭环：给定一个新收集数据目录和一个已有 Markdown 知识库目录，系统完成采集归一、聚类判断、关联检索、提炼合并、写回和轻量溯源。所有行为围绕一次手动运行展开，失败即报错退出，重跑即重试。

本规格把 make-decision 的 D1-D6 作为边界：只做 `digest(new_dir, kb_dir)`；必须写 CLI 合约；必须写目录约定；必须写 S1-S6 输入输出；必须落地 Phase 0 防丢失最低线；明确不引入调度、图数据库、完整双库产品化或重事务系统。

## In Scope

- 手动触发的 `digest(new_dir, kb_dir)` CLI 合约。
- `new_dir` 输入目录最小约定。
- `kb_dir` 输出知识库最小约定。
- `kb.structure.md` 或等价 KB 结构约定描述文件。
- S1-S6 管线输入、输出、关键字段、失败语义。
- 防信息丢失硬约束。
- `needs_review` 和 `insufficient_signal` 队列文件。
- 一个可构造验收样本，覆盖新建、更新、merge_multiple、空壳过滤和长文拆分建议。

## Out Of Scope

- 不做 scheduler、daemon、watch 或定时任务。
- 不引入 LightRAG、Graphiti、Cognee、GraphRAG 等框架本体。
- 不做图数据库、图谱平台或可视化。
- 不做完整双库适配产品化。
- 不做完整 source attribution 审计系统。
- 不做 CAS、journal、两阶段提交、持久重试队列或告警系统。
- 不做人工复核产品流程；只产出队列文件。
- 不处理并发或多进程同时写入同一 `kb_dir`。

## 功能需求

### FR-CONTRACT-001 CLI 合约

系统必须提供一次性手动运行入口，形态为 `digest(new_dir, kb_dir)` 或等价 CLI 命令，并把 `new_dir` 与 `kb_dir` 作为必填参数。

Given 用户准备了合法的 `new_dir` 和 `kb_dir`  
When 用户运行 digest 命令  
Then 系统处理本次目录中的待消化材料，并在成功时写出 run report 和知识库变更摘要。

验收细则：
- 必填参数：`new_dir`、`kb_dir`。
- 可选参数：`--config <file>` 指向运行配置，`--dry-run` 只写中间产物和计划不改 `kb_dir`，`--top-k <n>` 覆盖关联检索候选数，`--cluster-auto-threshold <float>` 覆盖自动候选阈值，`--cluster-review-threshold <float>` 覆盖复核阈值，`--max-doc-lines <n>` 覆盖拆分建议触发线。
- 默认阈值：`top_k=5`，`cluster_auto_threshold=0.90`，`cluster_review_threshold=0.80`，`max_doc_lines=300`。
- 退出码：`0` 成功；`1` 输入或配置错误；`2` 外部模型调用失败；`3` faithfulness 失败且回退也无法产出安全草稿；`4` 写回失败；`5` 可选索引同步失败。
- 失败输出：标准错误必须包含阶段名、失败输入文件、失败原因和可重跑提示。
- dry-run 语义：不得修改 `kb_dir/pages`、`kb_dir/_archive`、`kb_dir/_queues` 或任何正式知识页字段；所有计划中的页面变更、队列变更、归档变更和 provenance 变更只写入本次 run report。允许写入运行目录中的 dry-run 报告；若运行目录也位于 `kb_dir/_digest/runs`，该目录视为审计产物，不视为正式知识库内容变更。

### FR-CONTRACT-002 目录最小约定

系统必须定义 `new_dir` 和 `kb_dir` 的最小目录/文件约定，允许用户按约定构造样本并手动运行。

Given 用户只拥有文件夹和 Markdown 文件  
When 用户按约定放置输入材料和 KB 文件  
Then digest 不需要额外数据库或服务即可读取、判断并写出结果文件。

`new_dir` 最小结构：
- `items/`：原始新增材料，允许 `.md`、`.txt`、`.json`。
- `sources.jsonl`：可选来源清单，每行包含 `id`、`source_uri`、`fetched_at`、`source_status`、`content_path`。
- `_digest/work/`：运行中间产物输出目录，由系统创建。

`kb_dir` 最小结构：
- `kb.structure.md`：KB 结构约定描述文件。
- `pages/`：正式知识页。
- `_queues/needs_review.md`：需要人工看但本期不提供复核产品流程。
- `_queues/insufficient_signal.md`：证据不足的簇。
- `_archive/`：归档的旧内容、移除内容和失败写回备份。
- `_digest/runs/<run_id>/`：本次运行报告和阶段产物。

### FR-CONTRACT-003 KB 结构约定描述文件

`kb_dir` 必须包含一个结构约定描述文件，描述字段模型、路径规则、来源字段和强制字段映射，不设计复杂代码适配层。

Given 一个目标知识库只有 Markdown 文件和目录  
When digest 读取 `kb.structure.md`  
Then 系统可以知道新增页写到哪里、更新页如何保持字段、source/provenance 如何落盘。

最小字段：
- `kb_name`：知识库名。
- `page_root`：正式页根目录，默认 `pages`。
- `archive_root`：归档根目录，默认 `_archive`。
- `queue_root`：队列根目录，默认 `_queues`。
- `frontmatter_required`：必须保留或写入的 frontmatter 字段。
- `body_sections`：建议正文段落，可为空。
- `provenance_field`：最终 claim 来源字段名。
- `why_field`：决策背景或需求动机字段名。
- `version_field`：版本历史或修订记录字段名。
- `link_policy`：内部链接写法。
- `optional_index_sync`：可选索引同步方式；未声明时跳过。

### FR-STRUCTURE-001 S1 采集归一

系统必须把 `new_dir` 中的输入材料归一为 RawItem，并过滤抓取失败或空壳内容。

Given `new_dir/items` 中存在有效材料、重复材料和空壳抓取页  
When S1 执行  
Then 有效材料进入 RawItem 输出，重复材料按 `content_hash` 精确去重，空壳材料进入 ingest failure 报告且不得进入后续来源索引。

输入：
- `new_dir/items/*`
- `new_dir/sources.jsonl`

输出：
- `_digest/runs/<run_id>/s1/raw-items.jsonl`
- `_digest/runs/<run_id>/s1/duplicates.jsonl`
- `_digest/runs/<run_id>/s1/ingest-failed.jsonl`

RawItem 字段：
- `raw_id`
- `content_hash`
- `text`
- `source_uri`
- `source_meta`
- `fetched_at`
- `non_text_refs`
- `source_status`

失败语义：无法读取的输入文件记录到 `ingest-failed.jsonl` 并导致退出码 `1`；空壳内容不导致整次失败，但不得参与 S2-S6。

### FR-STRUCTURE-002 S2 聚类判断

系统必须使用 complete-linkage 思路对 RawItem 做聚类判断，并输出 auto、needs_review、insufficient_signal 三类结果。

Given 多条 RawItem 中存在相似主题和弱链相似项  
When S2 执行聚类  
Then 只有候选项与簇内所有成员都达到阈值时才能入簇，弱链不得把不相干材料串成一个簇。

输入：
- `_digest/runs/<run_id>/s1/raw-items.jsonl`
- `kb_dir` 中已有知识页文本

输出：
- `_digest/runs/<run_id>/s2/clusters.jsonl`
- `kb_dir/_queues/needs_review.md`
- `kb_dir/_queues/insufficient_signal.md`

Cluster 字段：
- `cluster_id`
- `tier`
- `members`
- `min_pair_similarity`
- `decision_reason`
- `source_uris`

失败语义：embedding 或相似度计算不可用时退出码 `2`；`insufficient_signal` 不是失败，必须写队列并继续处理其他簇。

### FR-STRUCTURE-003 S3 关联检索与路径判定

系统必须对每个可处理簇做 `kb_dir` top-k 关联检索，并输出 `new`、`revise`、`merge_multiple` 三类演化路径。

Given 一个簇可能关联一个现有页面、多个现有页面或没有相关页面  
When S3 执行  
Then 系统保留 top-k 候选并记录选择原因，不得只看 top-1 后丢弃其他高相关页面。

输入：
- `_digest/runs/<run_id>/s2/clusters.jsonl`
- `kb_dir/pages/**/*`

输出：
- `_digest/runs/<run_id>/s3/evolution-decisions.jsonl`

EvolutionDecision 字段：
- `cluster_id`
- `action`
- `target_paths`
- `candidate_paths`
- `candidate_scores`
- `reason`

失败语义：无法判定的簇进入 `needs_review` 队列；不影响其他簇继续。

### FR-STRUCTURE-004 S4 提炼合并

系统必须生成可追溯草稿，做 claim-level verify 和 faithfulness check；faithfulness 失败时回退逐条拼接，不得输出看似通顺但来源不支持的正文。

Given S3 决定新建、更新或合并多个目标页  
When S4 生成 Draft  
Then 每条最终 claim 都能回到至少一个有效 `source_uri`，未支持 claim 不进入正式正文。

输入：
- `_digest/runs/<run_id>/s3/evolution-decisions.jsonl`
- 相关 RawItem 正文
- 目标页旧正文

输出：
- `_digest/runs/<run_id>/s4/drafts.jsonl`
- `_digest/runs/<run_id>/s4/unsupported-claims.jsonl`
- `_digest/runs/<run_id>/s4/split-suggestions.jsonl`

Draft 字段：
- `draft_id`
- `cluster_id`
- `action`
- `target_paths`
- `final_body`
- `claims`
- `removed_claims`
- `provenance`
- `faithfulness_status`
- `split_suggestion`

失败语义：claim 验证失败只移除 unsupported claim 或转队列；faithfulness 失败先回退逐条拼接；回退仍无安全输出时退出码 `3`。

### FR-STRUCTURE-005 S5 写回

系统必须使用临时文件、fsync 和原子 rename 写回 `kb_dir`，失败即报错退出，重跑即重试。

Given S4 已生成安全 Draft  
When S5 写回新建页或更新页  
Then 正式页面要么完整更新，要么保持原状，不出现半写文件。

输入：
- `_digest/runs/<run_id>/s4/drafts.jsonl`
- `kb.structure.md`

输出：
- `kb_dir/pages/...`
- `kb_dir/_archive/...`
- `_digest/runs/<run_id>/s5/write-report.jsonl`

失败语义：文件写入、fsync 或 rename 失败时退出码 `4`；已生成中间产物保留在 run 目录以便重跑排查。

### FR-STRUCTURE-006 S6 轻量溯源

系统必须让每条最终 claim 至少携带 `source_uri`，并确保空壳来源不出现在最终来源字段中。

Given S1 标记了有效来源和空壳来源  
When S6 写入 provenance  
Then 最终页面的每条 claim 都能追溯到有效来源，移除项保留原文快照和原因。

输入：
- S1-S5 的所有阶段产物

输出：
- 页面内的 provenance 字段或来源段落
- `_digest/runs/<run_id>/s6/provenance-audit.jsonl`

失败语义：缺少来源的 claim 不进入正式页面；若页面没有任何可支持 claim，则转 `needs_review`。

### FR-BEHAV-001 防信息丢失硬约束

系统必须把防丢失规则作为 Phase 0 必做行为，而不是后续优化项。

Given 输入材料包含 FAQ 问句、英文参数、数字、URL、错误码、表格、设计稿链接、版本历史和长文  
When digest 处理这些材料  
Then 不得因为表面格式或固定上限丢弃信息，长文只触发拆分建议，不截断。

硬约束：
- 不设固定条数或行数上限来丢弃信息。
- 不因为问号、英文、数字、URL、错误码、参数名而整行丢弃。
- 抓取失败或空壳页不能进入最终来源索引。
- remove 操作必须归档或记录原因，不物理删除。
- 超过 `max_doc_lines` 时只产出拆分建议，不截断。
- 表格和结构化信息应保留结构，不强行散文化。
- 设计稿链接、截图 URL、外部工单号作为 `non_text_refs` 或 claim 来源保留。
- `why` 和版本历史字段必须有承载位置。

### FR-BEHAV-002 验收样本设计

系统必须提供一个最小验收样本设计，开发者可按说明构造，不依赖全量真实知识库。

Given 开发者按样本说明创建 `new_dir` 和 `kb_dir`  
When 开发者运行 digest  
Then 输出覆盖新建、更新、merge_multiple、空壳来源过滤、长文拆分建议和人工抽查点。

样本：
- `kb_dir/pages/goinsight/filtering.md`：已有全局筛选知识页，含来源字段。
- `kb_dir/pages/goinsight/chart-types.md`：已有图表类型知识页，含图表规则。
- `new_dir/items/filter-update.md`：新材料补充筛选字段、错误提示、FAQ 原问句、双语术语。
- `new_dir/items/chart-faq.md`：新材料同时关联筛选页和图表页，触发 `merge_multiple`。
- `new_dir/items/empty-shell.md`：只含导航和无正文的抓取失败页，必须被过滤。
- `new_dir/items/long-release.md`：超过 `max_doc_lines` 的发布说明，必须出拆分建议。

人工抽查清单：
- 空壳来源未进入最终页面来源字段。
- FAQ 原问句、错误码、参数名、URL 和双语术语仍在 claim 或来源中可见。
- 每条新增 claim 至少有一个 `source_uri`。
- 长文没有被截断，只有拆分建议。
- `merge_multiple` 的候选页和落点原因写入 S3 输出。
- remove 项进入归档或 removed_claims，不物理删除。

## 场景索引

- SC-001 合法输入：有 `new_dir`、`kb_dir`、`kb.structure.md` 和有效材料，运行后生成 run report 与页面变更摘要。
- SC-002 缺少 KB 结构描述：`kb.structure.md` 不存在，运行失败，退出码为 `1`，正式 KB 不改变。
- SC-003 空壳来源：`empty-shell.md` 进入 ingest failure，最终页面来源字段引用数为 0。
- SC-004 embedding 或模型失败：S2/S3/S4 的模型调用不可用，运行失败或当前簇入队列，错误报告包含阶段和输入。
- SC-005 faithfulness 回退：合成正文偏离 claims，系统回退为逐条 claim 拼接，unsupported claim 不进入正式页。
- SC-006 写回失败：临时文件、fsync 或 rename 失败，正式页保持原状。
- SC-007 merge_multiple：一个簇同时关联筛选页和图表页，S3 输出多个 target path 和选择原因。
- SC-008 长文拆分建议：`long-release.md` 超过 `max_doc_lines`，输出 split suggestion，正文不截断。
- SC-009 dry-run：所有正式页、归档和队列不改变，计划变更只出现在 run report。

## 影响范围

目标文件范围：本阶段只产出规格文档和任务记录，不写生产代码。

后续代码范围：Phase 0 实现会新增一个手动 digest 入口、文件夹读取写回逻辑、阶段产物目录、队列文件和基本模型调用配置。它不会改变现有调度、图数据库、双库适配或事务系统，因为这些都不在本期范围。

业务影响范围：
- 现有知识页更新语义：`revise` 会改写已有页面，但必须保留仍有效的旧 claim 和来源。
- 多页面影响：`merge_multiple` 允许一次簇影响多个页面，S3 必须显式列出所有目标和原因。
- 队列可见性：`needs_review` 与 `insufficient_signal` 只积累待处理条目，不承诺复核产品流程。
- 归档可见性：remove 项必须能在 `_archive` 或 `removed_claims` 中查到原因和原文快照。
- 来源可信度：空壳或抓取失败来源不得污染最终页面来源字段。
- dry-run 用户预期：dry-run 不改正式页、归档或队列，只产生计划和报告。
- 失败重跑语义：失败后重跑应基于现有文件重新计算，不依赖持久重试队列。
- 长文处理语义：长文触发拆分建议，不会被截断或静默省略。
- 人工抽查语义：验收样本要求人工抽查来源、claim、长文、FAQ、参数、设计稿链接和归档行为。

## 验收标准

- AC-001：分母为本次验收运行生成的 run report 数；正向断言为每次合法运行都生成 1 份 run report；反向断言为合法运行不得生成 0 份或多份互相冲突的 run report；baseline 来源为验收样本的一次非 dry-run。
- AC-002：分母为 3 个缺失输入场景（缺 `new_dir`、缺 `kb_dir`、缺 `kb.structure.md`）；正向断言为 3/3 场景退出码均为 `1` 且错误信息指出缺失项；反向断言为 0/3 场景修改正式 KB；baseline 来源为 SC-002。
- AC-003：分母为 S1 处理的全部输入文件；正向断言为有效文件进入 RawItem、重复文件进入 duplicates、空壳文件进入 ingest-failed；反向断言为空壳文件进入 S2 的数量为 0；baseline 来源为 S1 输出文件行数。
- AC-004：分母为 S2 输出的全部簇；正向断言为每个簇都有 tier 和 decision_reason；反向断言为 tier 缺失或低置信度簇未入队列的数量为 0；baseline 来源为 clusters 和队列文件。
- AC-005：分母为 S3 处理的全部可处理簇；正向断言为每个簇保留最多 `top_k` 个候选并给出 `new`、`revise` 或 `merge_multiple`；反向断言为只记录 top-1 且丢失其他高相关候选的数量为 0；baseline 来源为 evolution-decisions。
- AC-006：分母为 S4 生成的全部最终 claim；正向断言为每条 claim 都有支持状态；反向断言为 unsupported claim 进入正式正文的数量为 0；baseline 来源为 drafts 和 unsupported-claims。
- AC-007：分母为 S5 计划写回的全部目标页；正向断言为成功页完整出现，失败页保持原状；反向断言为半写正式页数量为 0；baseline 来源为 write-report 和正式页快照。
- AC-008：分母为 S6 provenance audit 中的全部最终 claim；正向断言为每条 claim 至少有 1 个有效 `source_uri`；反向断言为无 `source_uri` 或引用空壳 `source_uri` 的 claim 数量为 0；baseline 来源为 provenance-audit。
- AC-009：分母为验收样本中预置的 FAQ、错误码、参数名、URL、双语术语和设计稿链接 6 类信息；正向断言为 6/6 类在最终 claim、来源或 audit 中可追溯；反向断言为因表面规则整类丢弃的类别数为 0；baseline 来源为样本清单和最终输出。
- AC-010：分母为超过 `max_doc_lines` 的样本文档数；正向断言为每个超长文档都有 split suggestion；反向断言为正文被截断的超长文档数为 0；baseline 来源为 split-suggestions 和 RawItem 原文行数。
- AC-011：分母为 Out Of Scope 中 7 类排除项；正向断言为 spec 和计划不要求实现这些项；反向断言为新增调度、图数据库、双库产品化、重事务、持久重试队列或人工复核产品流程的要求数量为 0；baseline 来源为全文 grep 和 Out Of Scope。

## 假设

1. Phase 0 用户接受手动触发。
2. 目标知识库是文件夹加 Markdown。
3. LLM 和 embedding 后端走 OpenAI-compatible 最小配置。
4. 单次串行运行，不处理并发写入。
5. 阈值可以用 ovmc 的默认经验值启动，但必须保持可配置，后续按目标库标定。

## Known Gaps

- 真实 embedding/LLM provider 的具体配置留到实现期读取运行配置。
- 阈值标定工具不在 Phase 0 实现范围内。
- 完整 source attribution 审计系统不在 Phase 0 实现范围内。
- 完整双库适配不在 Phase 0 实现范围内。
- 人工复核产品流程不在 Phase 0 实现范围内。

## 设计决策

- KEEP D1：入口锁定为 `digest(new_dir, kb_dir)`。
- KEEP D2：CLI 合约必须包含命令、参数、输出、退出码和失败输出。
- KEEP D3：`new_dir` / `kb_dir` 最小目录约定必须明确。
- KEEP D4：S1-S6 必须有输入、输出、关键字段和失败语义。
- KEEP D5：不硬截断、空壳来源不得引用、不确定内容进队列、faithfulness 失败回退逐条拼接、写回原子 rename、索引同步失败 let it crash。
- KEEP D6：不做 scheduler、graph DB、完整 dual-store、完整 source attribution 产品、CAS/journal/两阶段提交、持久重试队列、人工复核产品流程。

## Decision Trace Matrix

- D1 Phase 0 主入口是 `digest(new_dir, kb_dir)`：覆盖位置为速读卡、FR-CONTRACT-001、SC-001、AC-001。
- D2 build-spec 必须写 CLI 合约：覆盖位置为 FR-CONTRACT-001、AC-001、AC-002、dry-run 语义。
- D3 build-spec 必须写 `new_dir` / `kb_dir` 最小目录约定：覆盖位置为 FR-CONTRACT-002、FR-CONTRACT-003、AC-002。
- D4 build-spec 必须写 S1-S6 输入输出：覆盖位置为 FR-STRUCTURE-001 到 FR-STRUCTURE-006、AC-003 到 AC-008。
- D5 Phase 0 防丢失最低线必须落地：覆盖位置为 FR-BEHAV-001、FR-BEHAV-002、AC-006、AC-008、AC-009、AC-010。
- D6 明确不引入重系统：覆盖位置为 Out Of Scope、影响范围、AC-011。
- D7 用户确认必须带可核验证据：由上游 decision-log 负责记录；本规格不重复用户 comment 原文。
- D8 S7 通过依据是异源细节审查完成和用户人工放行：由上游 decision-log 负责记录；本规格只消费最终决策结果。

## 落地计划引用 / Implementation Plan Reference

本规格文档与上游 build-plan 产物共同构成 Phase 0 的完整交付上下文：

- [`specs/kd-phase0-digest-spec/plan.md`](../../specs/kd-phase0-digest-spec/plan.md)：阶段划分、文件清单、gate 命令与 STOP 点。
- [`specs/kd-phase0-digest-spec/tasks.md`](../../specs/kd-phase0-digest-spec/tasks.md)：T001-T011 任务依赖与执行顺序。
- [`specs/kd-phase0-digest-spec/data-contracts.md`](../../specs/kd-phase0-digest-spec/data-contracts.md)：CLI、`new_dir`、`kb_dir`、JSONL 阶段产物与队列文件的字段/校验规则。

plan.md 与 tasks.md 将执行分为三个阶段（plan.md 中称为 Phase，tasks.md 中称为 Stage）：

1. **Stage 1: Contract and filesystem foundation (T001-T003)** —— 完成 `digest(new_dir, kb_dir)` CLI 入口、参数与退出码合约、`new_dir`/`kb_dir` 最小目录验证、运行目录与 dry-run 不变性保证。
2. **Stage 2: S1-S4 processing pipeline (T004-T007)** —— 完成 S1 采集归一与空壳过滤、S2 complete-linkage 聚类与队列写入、S3 top-k 关联检索与 `new`/`revise`/`merge_multiple` 路径判定、S4 草稿生成与 faithfulness 回退。
3. **Stage 3: Writeback, provenance, and acceptance (T008-T011)** —— 完成 S5 临时文件/原子写回与归档、S6 轻量溯源与最终来源强制、完整验收样本与测试断言，以及本规格文档的最终落地计划引用更新。

关系说明：本规格文档描述“做什么/为什么/契约是什么”；上游 plan.md/tasks.md/data-contracts.md 描述“怎么做/执行顺序/任务拆分/数据契约是什么”；两者合在一起形成 Phase 0 可交付给实现者的 handoff 包。

注意：本规格更新仅完成规格与计划引用锚定，实际代码实现不在本次范围；下游 `verify-code` 阶段将基于本规格及上述计划产物进行实现与验收。

## 质量事实契约

### 1. scope 边界

IN scope：CLI 合约、目录约定、KB 结构约定描述文件、S1-S6 文件级 I/O、防信息丢失硬约束、验收样本和 oracle。

OUT scope：调度、图数据库、完整双库适配、完整 source attribution 产品、CAS、journal、两阶段提交、持久重试队列、人工复核产品流程、并发写入。

裁剪机制：以 make-decision D1-D6 为唯一范围来源；新增机制必须通过 F10 四问；超出 Phase 0 的能力进入 Known Gaps。

### 2. 自检结果

- 7 条自检：pass，详情见 `tasks/kd-phase0-digest-spec/artifacts/build-spec-self-check.md`。
- Spec-Purity grep：warn，质量契约中的 `[FRICTION]` 条目含 `|` 分隔符。
- FR grep occurrence count：19。
- AC grep occurrence count：22。
- scope-triage：warn，命中“不能进入最终来源索引”，判定为产品语义而非流程阻断语义。
- Artifact-first：pass。
- 行为验证：pass。

### 3. 独立审查摘要

- round 1 verdict：revise_required，3 个 blocking 和 2 个 minor。
- round 2 verdict：pass。
- 审查报告：`tasks/kd-phase0-digest-spec/reports/build-spec--5d9e14dc-52b7-4e3b-a124-07de19ecfc7f--2-pass.md`。

### 4. 未解风险

- `[FRICTION] Step 0.5 resume: worktree.json 缺失，用户授权本阶段补齐本地 context | 建议: 后续 make-decision 阶段应稳定产出 worktree.json。`
- scope-triage warn 已记录，当前不影响推进。
- baseline 对照中 missed_step_rate、test_execution_rate、rework_proxy_count 缺少可计算数据，按 unknown 记录。
- KnowledgeDigest 本地目录不是 git repo；Step 7.5 不能执行 git commit，只能记录 no-git no-commit reason。

### 5. handoff required_reads

- `docs/plans/phase0-implementation-spec.md`
- `specs/kd-phase0-digest-spec/spec.md`
- `tasks/kd-phase0-digest-spec/decision-log.md`
- `tasks/kd-phase0-digest-spec/artifacts/build-spec-requirements.md`
- `tasks/kd-phase0-digest-spec/artifacts/build-spec-self-check.md`
- `tasks/kd-phase0-digest-spec/artifacts/build-spec-constitution-check.md`
- `tasks/kd-phase0-digest-spec/artifacts/build-spec-baseline-report.md`
- `tasks/kd-phase0-digest-spec/artifacts/build-spec-f10-analysis.md`
