# 通用增量知识消化技能 — 设计草案 v2

状态：**草案 v2，供细化，不是实施计划，不含代码**
日期：2026-07-05

## 参考资料（绝对路径，脱离本 repo 后仍需按此路径查阅）

调研文件：

1. `/Users/Hugh/Hugh/Project/OpenViking/.omc/research/ovmc-analysis.md` — ovmc 聚类判断机制与资源占用分析
2. `/Users/Hugh/Hugh/Project/OpenViking/.omc/research/sc-cb-analysis.md` — sleep-curator 管线 + CompanyBrain 产出结构对比分析
3. `/Users/Hugh/Hugh/Project/OpenViking/.omc/research/sleep-curator-report.md` — sleep-curator 去重/提炼/合并管线详细报告（含依赖清单）
4. `/Users/Hugh/Hugh/Project/OpenViking/.omc/research/goinsight-loss-report.md` — CompanyBrain 信息丢失根因分析（含源码行号证据）
5. `/Users/Hugh/Hugh/Project/OpenViking/.omc/research/oss-knowledge-curation.md` — 开源知识消化项目调研对比（LightRAG/Graphiti/Cognee等）
6. `/Users/Hugh/Hugh/Project/OpenViking/.omc/plans/open-questions.md` — 早期开放问题记录（历史参考）

原始代码/数据出处（非调研报告，是调研报告引用的源头）：

- `/Users/Hugh/Hugh/Project/OpenViking/tools/ovmc/` — ovmc 工具源码
- `/Users/Hugh/Hugh/Project/OpenViking/tools/sleep-curator/` — sleep-curator 工具源码（含 DESIGN.md）
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain/` — CompanyBrain 产出文档样本（repo 外，注意路径在另一台机器/另一个 repo 下）
- `/Users/Hugh/Hugh/Knowledge/SourceArchive/` — CompanyBrain 源文档归档（repo 外）

---

## v2 修订记录：用户拍板 + 简化决策

**总纲（最高优先级）**：技能要尽可能简单。场景收窄为一句话：`digest(new_dir, kb_dir)` —— 对一个文件夹（新收集数据），基于另一个文件夹（已入库知识）的内容和结构，更新文档/文件夹/结构。与此无关的复杂度一律砍掉或降级为"可选加固"。

7 条拍板落地对照：

| # | 拍板 | 落地方式 |
|---|---|---|
| 1 | 触发方式：手动 | 删掉调度/定时设计，S1 不再讨论"每日批处理 vs 事件触发" |
| 2 | LLM/embedding 后端：两库各自独立配置 | 第4节明确"配置文件层面区分"，不引入 provider 无关抽象层 |
| 3 | needs_review/insufficient_signal：只产出队列文件 | 复核流程明确移出设计范围，S2 输出即终点 |
| 4 | 公司知识库：纯文件夹+md，无读写接口问题 | 第3节适配层从"代码接口"降级为"KB 结构约定描述文件" |
| 5 | 信息预算量化：永不截断丢弃 + `max_doc_lines` 触发拆分建议 | 第5节新增量化指标，拆分是重组不是丢弃 |
| 6 | 索引同步失败：let it crash，重跑即重试 | 删除持久重试队列，S5 简化为"失败即报错退出" |
| 7 | Phase 顺序：先单库最小闭环，再补防丢失 | 第6节路线保持原顺序，按简化结果重排内容 |

简化审视清单结论见第 2 节末尾。防信息丢失 9 条对策全部保留，不简化。

---

## 1. 目标与非目标

### 目标
1. 核心场景：`digest(new_dir, kb_dir)` —— 给定一个新收集数据的文件夹，基于已入库知识文件夹的内容和结构，完成**聚类去重判断 → LLM 提炼合并 → 更新或新增到 kb_dir**，增量执行、不全量重建。
2. 同一套技能同时适配两个目标库：OpenViking 个人记忆库、公司知识库，两者本质都是"文件夹 + md"，差异收敛到一份轻量的 KB 结构约定描述（不是代码接口层）。
3. 依赖轻、本地可跑：默认零外部数据库、零专有 CLI 依赖，embedding/LLM 走标准 OpenAI 兼容协议，两库各自独立配置。
4. 系统性杜绝 CompanyBrain 式的信息丢失——不设硬编码限流、不做规则性整段丢弃、不产生虚假可追溯性。

### 非目标
1. 不做调度/定时/事件触发——手动触发，运行一次处理一批。
2. 不做知识图谱可视化、图数据库多跳查询——只做去重/合并/更新判断，产出仍是结构化 md 文档。
3. 不重新实现 ovmc 的 F1-F7 规则引擎或 sleep-curator 的 rethink 循环本体——直接复用/移植已验证机制。
4. 不解决索引全文检索本身——检索能力由目标库自己的搜索/embedding 系统提供，本技能只负责"消化"这一段；索引同步是**可选**适配步骤，不是必需环节。
5. 不设计 needs_review/insufficient_signal 的人工复核流程——只产出队列文件，复核动作完全在本设计范围外。
6. 不做持久化重试队列/告警机制——手动触发场景下失败即报错退出，重跑技能即重试。

---

## 2. 管线设计：阶段图 + 每阶段输入输出

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐   ┌─────────────┐
│ S1 采集/归一 │──▶│ S2 聚类判断  │──▶│ S3 关联检索+  │──▶│ S4 提炼合并  │──▶│ S5 写回     │
│  (Ingest)   │   │ (Cluster)    │   │  路径判定     │   │ (Synthesize) │   │ (Commit)    │
└─────────────┘   └──────────────┘   └───────────────┘   └──────────────┘   └─────────────┘
                                                                  │
                                                          ┌───────▼────────┐
                                                          │ S6 溯源留存层  │
                                                          │ (Provenance)   │
                                                          │ 横切，非串行   │
                                                          └────────────────┘
```

### S1 采集/归一（Ingest）
- 输入：`new_dir` 下的新增原始条目（文件/对话片段/抓取页），由**适配层**按 KB 结构约定读取。
- 处理：统一转换为内部 `RawItem{id, text, source_uri, source_meta, fetched_at}`；对抓取失败/空壳内容做**质量门禁**——空壳判定为"抓取失败"标记，不进入下游聚类，也不允许被后续引用为"来源"（防虚假可追溯性）。
- 输出：`RawItem[]` + `content_hash`（精确去重，独立于聚类，借鉴 ovmc gather.py 做法）。
- 手动触发：无调度逻辑，运行一次即处理 `new_dir` 当前全部待处理内容。

### S2 聚类判断（Cluster，核心借鉴 ovmc）
- 输入：`RawItem[]`（去重后）+ `kb_dir` 已有条目的 embedding 索引（增量维护，不重算全量）。
- 处理：
  - 复用 ovmc 的 **complete-linkage 聚类**（拒绝 union-find 链式合并，防弱链误合并）+ 双阈值分层（auto_candidate / needs_review）。
  - 复用 F1-F7 多特征决策树思路，但**不照抄具体阈值**——阈值必须基于目标库自己的标定数据重新校准。
  - INSUFFICIENT_SIGNAL 簇写入待复核队列文件，**到此为止**——不强行合并，不静默丢弃，也不设计复核流程本体。
- 输出：`Cluster[]{cluster_id, tier(auto/needs_review/insufficient), members[]}` + `needs_review_queue.md`/`insufficient_signal_queue.md`（纯文件产出）。

### S3 关联检索 + 路径判定（Retrieve & Decide，借鉴 sleep-curator Step1-2）
- 输入：`Cluster`（auto/needs_review 两层）+ `kb_dir` 全量条目。
- 处理：
  - 对每个簇做 `kb_dir` 的 top-k 关联检索（不只 top-1，修正 sleep-curator 的简化，避免漏合并）。
  - LLM 判定：`new`（新建）/ `revise`（原地重写某已有条目）/ `merge_multiple`（拆分合并进多个已有条目，保留——公司知识库场景一簇跨多页手册是真实需求）。
- 输出：`EvolutionDecision{cluster_id, path, target_uris[]}`。

### S4 提炼合并（Synthesize，核心借鉴 sleep-curator，但改造防丢失）
- 输入：`Cluster` + `EvolutionDecision` + 目标已有条目正文（revise/merge_multiple 路径）。
- 处理（详见第 5 节"防信息丢失机制"）：
  - 生成草稿（复用 sleep-curator 多轮 rethink 机制思路，Phase 0 先单轮，多轮作为后续加固，见第6节）。
  - **不做硬性行数/条数限流**——用"信息预算"机制替代（见第5节，含新增 `max_doc_lines` 拆分触发指标）。
  - 三分类协议（keep/revise/remove_with_reason）+ 论断级验证（claim-level verify），但 remove 必须**归档**而非物理删除。
  - synthesize_body + faithfulness check（忠实性核对失败则回退逐条拼接，不强行降级为"看起来通顺但漂移"）。
- 输出：`Draft{final_body, claims[], removed_claims[](附原因+原文快照), provenance[], split_suggestion?(若超 max_doc_lines)}`。

### S5 写回（Commit，简化版，借鉴 sleep-curator writer.py 的原子写入思路）
- 输入：`Draft` + `kb_dir` 的写入位置（按 KB 结构约定确定路径）。
- 处理：临时文件 + fsync → 原子 rename，直接写入 `kb_dir`。索引同步是**可选适配步骤**：若目标库声明了同步方式则调用；**同步失败直接报错退出（let it crash）**，不做持久重试队列、不做告警——手动触发场景下重跑技能本身就是重试。
- 输出：落盘的知识条目（+ 若目标库是 OpenViking，可选触发其索引同步）。
- 明确删除：CAS 并发检查、两阶段提交、journal 崩溃恢复（见第2节末简化审视清单，理由：手动单人触发场景并发风险低，降级为可选加固）。

### S6 溯源留存层（Provenance，横切关注点，不是串行阶段）
- 贯穿 S1-S5：每个最终 claim 必须能追溯到具体 `source_uri + 原文片段位置`；every `removed_claims` 必须保留"为什么移除"+ 原文快照（不是物理删除，是移到归档区）；"来源索引"字段只允许引用**验证过有效内容**的来源。
- 实现重量：Phase 0 阶段做**轻量版**——只要求 `source_uri` 字段随 claim 一起落盘，不做独立的溯源数据库或复杂校验流程；完整的引用二次校验留到 Phase 1（见第6节，理由：核心场景是单人手动跑一个文件夹，溯源的首要价值是"能查到从哪来"，不是"自动化审计"，重量实现在此场景下投入产出比低）。

### 简化审视清单（逐项结论）

| 项目 | 结论 | 理由 |
|---|---|---|
| CAS 并发检查 | **删除** | 手动单人触发，同一时刻不存在并发写同一 kb_dir 的场景 |
| 两阶段提交（临时文件+journal+rename） | **降级为可选加固**，Phase 0 只保留"临时文件+fsync+原子rename" | 崩溃恢复的价值只在"频繁自动运行+不可人工重跑"场景下才划算；手动触发失败直接重跑即可 |
| journal 崩溃恢复 | **删除**（随两阶段提交一起） | 同上，且 let it crash 原则下没有 journal 也能安全重跑（重跑会重新聚类判断，不会重复摊销） |
| merge_multiple 路径 | **保留** | 公司知识库场景一簇跨多个模块手册页是真实需求，不是过度设计；实现成本低（只是 target_uris 从单值变数组） |
| 多轮 rethink 轮数 | **降级为可选加固**，Phase 0 单轮生成 | 单轮生成配合 faithfulness check 已能满足最小闭环；多轮收敛是质量优化，不是闭环必需项 |
| S6 溯源层实现重量 | **降级为轻量版**，Phase 0 只保留 source_uri 落盘 | 完整校验流程价值高但非阻塞最小闭环，符合"先单库最小闭环，再补防丢失"的既定顺序 |

---

## 3. 适配层设计

核心管线（S1-S6）不依赖代码接口层，而是依赖一份**KB 结构约定描述文件**（每个目标库一份，YAML/md 均可），因为公司知识库和 OpenViking 记忆库本质都是"文件夹 + md"，不存在需要抽象的读写接口差异。

KB 结构约定描述文件包含三部分：

| 部分 | 内容 | OpenViking 示例 | 公司知识库示例 |
|---|---|---|---|
| 字段模型 | 该库 md 文件的 frontmatter 字段清单，标注哪些必填 | MEMORY_FIELDS（viking:// URI 等） | 13 字段 YAML frontmatter（tier/trust/source_status 等）|
| 目录组织规则 | 新增/更新文件放在哪、命名规则、是否分模块目录 | curated/ 目录 + viking:// URI 映射 | 模块手册体系，H2 自由正文分节 |
| 强制字段 | 本设计要求的字段（why/版本历史，见第5节）在该库如何落到具体字段名 | 映射到 MEMORY_FIELDS 里哪个字段 | 映射到 13 字段里哪个字段 |

关键设计原则：
- **没有代码层适配接口**：不再定义 `SourceReader`/`KnowledgeStore`/`IndexSync` 三个抽象类。核心管线直接读写文件系统，行为差异只由"读哪个目录、按什么字段模型写"这份约定描述文件决定。
- **索引同步是可选步骤，不是核心管线一部分**：若目标库是 OpenViking，写回后可选调用其官方索引同步能力（进程内 API 优先，CLI fallback 仅作降级）；公司知识库若无此需求，可完全不声明索引同步方式，管线不因此受阻。
- **字段模型可扩展、不可裁剪**：字段集合由 KB 结构约定描述文件声明，核心管线不假设固定字段数量或名称。
- **embedding/LLM 后端独立配置**：两个目标库各自在自己的配置文件里声明 embedding/LLM provider，不做 provider 无关抽象层，不做跨库统一路由。

---

## 4. 开源复用决策表

| 组件 | 决策 | 理由 |
|---|---|---|
| 聚类算法（相似度分组） | **自建**，移植 ovmc 的 complete-linkage 实现思路 | 逻辑简单（数十行 numpy），且 ovmc 已验证过 union-find 式合并的历史事故教训，直接复用经验比引入图数据库框架划算 |
| 阈值标定方法论 | **自建**，参照 ovmc RuleThresholds 的标定协议 | 阈值必须基于目标库自己语料标定，任何开源项目的默认阈值都不可跨语料通用 |
| 多轮提炼生成（rethink） | **移植 sleep-curator 机制思路，Phase 0 降级为单轮**（见第2节简化清单） | 收敛策略已验证，但非最小闭环必需，先跑单轮验证整体链路 |
| 论断级验证（claim verify + faithfulness check） | **移植 sleep-curator 机制** | 防止 LLM 合并阶段"看起来通顺但漂移"的关键防线，价值高、复杂度低，Phase 0 即保留 |
| Embedding 客户端 | **自建轻量 HTTP 客户端**（OpenAI 兼容协议），不引入向量数据库；两库各自独立配置 provider | 借鉴 LightRAG"默认零外部数据库"思路；两库配置互不影响，无需 provider 无关抽象层 |
| 增量索引/合并调度框架 | **只借思路，不直接引入 LightRAG/Graphiti/Cognee 本体** | 三者都是重量级图知识库框架，与"文件夹+md"场景不匹配；只借"增量 delta 合并、不做全量重建"的设计思想 |
| 合并/归档操作模式 | **只借思路**：参考 Karpathy LLM-Wiki 的"合并两篇+旧文章归档+留重定向"模式 | 与本设计 S4/S5 的"归档而非删除"原则一致，工程实现自建（文件操作即可，无需额外框架） |
| 文件锁/journal/CAS/两阶段提交 | **不引入**，降级为"临时文件+fsync+原子rename" | 见第2节简化清单：手动单人触发场景下，重量事务机制的投入产出比低，let it crash + 重跑即可 |
| 触发调度框架 | **不引入** | 手动触发是拍板结论，无需任何调度/定时/recurrence 机制 |

**build-vs-buy 结论（定案）**：不引入任何框架（图知识库框架、事务框架、调度框架），自建轻量管线。理由：总纲要求"技能要尽可能简单"，核心场景收窄为单文件夹对单文件夹的手动 digest，任何框架带来的依赖面、学习成本、配置负担都超过它能解决的问题规模。价值全部落在**移植 ovmc + sleep-curator 已验证过的逻辑思路**（不引入其运行时依赖），并按简化清单砍掉不匹配当前场景的重量机制。

---

## 5. 防信息丢失机制（对照 CompanyBrain 教训逐条设计，9 条全部保留）

| CompanyBrain 教训 | 本设计对应机制 |
|---|---|
| `max_lines=12`、`limit=8/3/6`、`scored[:3]` 等硬编码上限 | **不设固定条数/行数上限、永不截断丢弃**。改用"信息预算"机制：S4 生成草稿时以"是否所有 claim 都被 verify_claims 覆盖"为终止条件，而非"是否达到 N 行"。新增可配置指标 `max_doc_lines`：某文档超过 N 行后，**触发"分模块/分页面"拆分建议**（按业务型、逻辑性组件组织成多个页面/文件），拆分是**重组**而非丢弃——原内容全部保留，只是从一个文件变成结构化的多个文件 |
| 问号结尾行（FAQ 原始问句）规则性丢弃 | S1 归一阶段不做任何基于表面模式（标点/字符占比）的整行丢弃；若确需预筛选，必须用**空壳内容判定**（结构性判定：正文密度、是否含实际信息），而非表面规则 |
| 双语文本英文部分丢弃、纯字母数字行丢弃 | 同上，S1 不做语言/字符类别过滤；错误码、参数名、双语术语原文统一进入 S4 的 claim 拆分与验证流程，由 LLM 判断是否有信息价值 |
| 决策动机(why)系统性无字段承载 | KB 结构约定描述文件（第3节）**强制要求声明至少一个"决策背景/why"类字段**；S4 的 claim 分类协议明确包含"背景动机类陈述"作为独立类别 |
| 版本历史/修订记录无字段承载 | KB 结构约定描述文件要求声明"来源版本/修订时间线"字段；S6 溯源层记录每次 revise 的 diff 摘要 |
| 视觉设计稿/截图引用完全丢失 | S1 采集阶段的 `RawItem` 结构显式包含"非文本引用"字段（设计稿链接、截图 URL），S4 claim 拆分与合并逻辑必须显式处理 |
| 抓取失败页仍被列入"来源索引"，虚假可追溯性 | S1 质量门禁：空壳内容标记为 `ingest_failed`，禁止出现在最终"来源索引"字段中；S6 二次确认每条引用确实提供了被使用的内容 |
| `discarded_pages.unlink()` 物理删除源文件 | 任何"移除"操作一律**归档而非删除**——移入 `_archive/` 或等价冷区，保留原文可追溯；硬性约束，不是配置项 |
| 表格→散文改写导致结构化信息丢失 | S4 synthesize_body 阶段：原始表格/结构化数据保留原始结构化形式作为附件或独立字段，只有陈述性内容才走"重组为连贯段落"路径 |

---

## 6. 分期落地路线：最小可用 → 完整（按简化结果重排）

### Phase 0（最小可用，单一目标库打通全链路，`digest(new_dir, kb_dir)` 跑通）
- 实现 S1（基础质量门禁：空壳判定）→ S2（复用 ovmc 聚类算法，走标准 embedding HTTP 客户端）→ S3（top-k 关联检索 + new/revise/merge_multiple 判定）→ S4（单轮生成 + claim-level verify + faithfulness check，`max_doc_lines` 拆分建议）→ S5（临时文件+fsync+原子rename 写入 `kb_dir`，无 CAS/journal，索引同步为可选步骤，失败即报错退出）。
- S6 溯源层轻量版：只要求 source_uri 随 claim 落盘。
- 目标：跑通"`new_dir` 新内容进来 → 判断是否已有相似条目 → LLM 生成一版更新/新建/拆分合并 → 落盘 `kb_dir`"，验证 KB 结构约定描述文件是否够用。
- 验收：在 OpenViking 记忆库上对一批真实新增内容跑通，人工抽查合并结果无明显信息丢失；`needs_review`/`insufficient_signal` 队列文件正确产出。

### Phase 1（防丢失机制完整版 + 溯源层加固）— **已落地**

- 补齐 S6 完整溯源留存层：claim 级来源追溯、归档而非删除、来源索引二次校验。
- 信息预算机制的 `max_doc_lines` 拆分建议逻辑打磨（按业务/逻辑组件切分页面的具体规则）。
- KB 结构约定描述文件加入 why/版本历史字段的强制声明检查。
- 验收：故意构造"抓取失败页 + 高信息密度页混合"的测试簇，验证空壳页不进入来源索引、高密度页无信息丢失；构造超长文档验证拆分建议合理。
- **实现状态（2026-07）**：`tests/acceptance/test_phase1_loss_prevention.py` 覆盖 AC01–AC16；Phase 2.5 后归档语义改为「写前归档只增不删」（不再做 90 天物理清理）。

### Phase 2（已回退：曾无条件启用，按拍板 1 删除）

- **历史**：Phase 2 本应是条件性可选加固（design 原文：仅当 Phase 0/1 实测单轮质量不足，或场景扩展到可能并发时才启用）。实际上曾被无条件合入（多轮 rethink + CAS/两阶段提交/`recovery.py`），触发条件从未满足。
- **Phase 2.5 拍板 1**：删除 `recovery.py` 全套事务机制，改为「写前归档只增不删」。接受极端写失败时知识库半写；原文在 `_archive/`，重跑即恢复。
- **保留**：单轮 rethink 收敛（B3 压到一轮）；LLM 真提炼（B4）；并发文件锁仅作 CLI 互斥，不做 CAS/journal。
- 若未来真要并发/崩溃恢复，另开 Phase，不在本轮恢复两阶段提交。

### Phase 2.5（瘦身 + 真实 LLM；2026-07 落地）

见 [`phase2.5-slim-and-llm.md`](./phase2.5-slim-and-llm.md)：B1–B6 已落地。目标是把「事务很重、核心恒等」压成「防丢失完整、真会提炼」的小工具。

### Phase 3（双库适配验证）
- 完成公司知识库的 KB 结构约定描述文件（13 字段模型 + H2 自由正文 + 目录组织规则）。
- 验收：同一套核心管线代码，分别指向 OpenViking 库和公司知识库跑通，行为一致，仅 KB 结构约定描述文件不同。

### Phase 4（完整能力：阈值标定工具化）
- 提供阈值标定工具（照搬 ovmc 标定协议：标注金标准簇 → 检验特征分离度 → 生成阈值建议），供每个新目标库自行标定。
- （不再包含触发调度优化——手动触发是既定拍板，无需 recurrence 式调度）

---

## 7. 开放问题清单

用户已就原 7 条开放问题全部拍板（见文档开头"v2 修订记录"），本节清空。若后续实施中出现新的需要用户决策的问题，记录于 [`.omc/plans/open-questions.md`](../../.omc/plans/open-questions.md)（[`docs/plans/open-questions.md`](./open-questions.md) 为同步副本）。

---

## 附：关键设计取舍摘要

- **借鉴不照抄**：聚类算法结构抄 ovmc，阈值不抄（必须重新标定）；提炼合并流程抄 sleep-curator，专有格式/CLI 依赖/多轮 rethink 的"必需性"不抄（降级为可选加固）；结构化分级抄 CompanyBrain 的字段思路，硬限流和规则性丢弃不抄。
- **不引入任何框架**：图知识库框架（LightRAG/Graphiti/Cognee）、事务框架（CAS/两阶段提交/journal）、调度框架全部不引入或降级为可选加固——总纲"尽可能简单"下的定案。
- **适配层从代码接口降级为约定描述文件**：因为两个目标库本质都是"文件夹+md"，不存在需要抽象的读写差异，只需一份 KB 结构约定描述（字段模型+目录规则+强制字段）。
- **两处显式修正 sleep-curator 简化**：S3 从 top-1 改为 top-k 关联判定；新增 merge_multiple 路径（不再只有 new/revise 二选一）——这两条是真实需求，予以保留。
- **防丢失是硬约束不是选配项**：归档而非删除、来源索引校验、no 硬编码限流、`max_doc_lines` 拆分而非截断，这几条贯穿所有 Phase，不作为"未来再加"的技术债处理。
- **手动触发 + let it crash**：无调度设计，无持久重试队列；失败明确报错退出，重跑技能即重试，符合"依赖轻、本地可跑"的最简场景定位。
