# sleep-curator 管线 + CompanyBrain 产出结构 调研

调研日期：2026-07-05
范围：`tools/sleep-curator/`（本 repo） + `/Users/Hugh/Hugh/Knowledge/CompanyBrain/`（**repo 外**独立目录，与 OpenViking 本体无 git 关联）

---

## 一、路径澄清（重要，任务描述里的路径不存在，已定位真实路径）

- 任务给的 `Knowledge/CompanyBrain/Products/GoInsight/` 和 `Knowledge/SourceArchive/` 在本 repo（`/Users/Hugh/Hugh/Project/OpenViking`）下**不存在**。
- 真实位置：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/`，`/Users/Hugh/Hugh/Knowledge/SourceArchive/`——这是 repo 外、完全独立的一个目录树（`ls /Users/Hugh/Hugh/Knowledge` 可见 `CompanyBrain/`、`BrainInbox/`、`SourceArchive/`、`Projects/` 等同级目录）。
- OpenViking repo 自己的知识数据在 `data/viking/default/resources/maxstore/`（对应 MAXSTORE 产品，不是 GoInsight），是另一套独立体系，与 CompanyBrain 无关，调研中未使用。
- 已有沉淀记忆确认此区分：`data/viking/default/user/default/memories/entities/knowledge_base/company_brain.md` 和 `.../events/2026/07/05/sleep_curator_vs_company_brain_clarified.md` —— 2026-07-05 用户已和之前的 assistant 澄清过这个定位问题，结论：sleep-curator 不是要做出 CompanyBrain 式结构化文档，是把 OpenViking 内部知识密度低的原始记忆提纯成密度高的单篇文档。本次调研只是把这个已有结论坐实到具体机制和数据层面。

---

## 二、sleep-curator 管线：去重 → 提炼 → 合并 各步做什么

版本：DESIGN.md v0.3（477 行，`tools/sleep-curator/DESIGN.md`），代码总量 ~5981 行（`sleep_curator/` 下 15 个模块）。

### 定位（§0 结论表）
- 独立小工具，是 `ovmc`（去重工具）的姊妹工具，不是替代品。
- **分工**：ovmc 判定"两条记录是不是同一件事"（去重合并，规则引擎，已验证到头见 `tools/ovmc/ovmc/rules.py:76-79`）；sleep-curator 判定"一堆原始记录能不能长出一条知识"（提炼归纳）。二者不重叠。

### 处理单元：每簇独立、幂等、可断点续跑（DESIGN.md §4，`orchestrator.py:95-174` `process_one_cluster`）
不是"阶段流水线"（阶段1处理全部簇→阶段2……），是逐簇跑完整流程：

```
for cluster in pending_clusters:
    if 已在 journal.jsonl 里是终态(done/needs_review/skipped_permanent): continue
    result = process_one_cluster(cluster)  # 检索→生成→验证→落盘/needs_review→索引同步
```

`process_one_cluster`（`orchestrator.py:95`）内部两阶段：
1. **Plan phase**（`orchestrator.py:133-135`）：`retrieve_related`（embedding top-k 检索）+ `decide_evolution_path`（LLM 判断走"新建"还是"原地重写"）——在 journal 写 `started` 之前先跑完，这样 `target_uri`/`target_before_hash` 提前确定（`orchestrator.py:148-153`）。
2. **Generate phase**（`orchestrator.py:157-170`）：`run_pipeline`（`pipeline.py`，828 行，最大模块）执行 rethink 生成→三分类重写→论断级验证。

四事件 journal 协议（`journal.py`，407 行）：`started → prepared → committed / failed`，用于崩溃恢复（DESIGN.md §4.2）。恢复逻辑：只信"事件序列"，不信"cluster_id 出现过"。

### 核心生成机制（DESIGN.md §5，方案篇幅占比最大的部分）
1. **关联检索**（A-Mem 第一步）：cluster 合并文本做 embedding，在 `curated/` 全库（含 `_pinned/`、含 dormant，不含 `_needs_review/`）做 top-k=5 相似度检索。
2. **演化路径判定**：LLM 判断"是否存在应该因新素材更新的旧条目"→ 走"原地重写"；否则"新建"。
3. **多轮 rethink 生成**（Letta 机制，`max_rethink_rounds` 默认 **3**，非 v0.2 的 10，理由：轮数越高不是成本问题而是长 prompt 上下文溢出导致质量退化风险，DESIGN.md §5.2）。每轮都重新带原始素材全文（防止"退化成润色上一轮摘要"），批判+改进同次调用完成，LLM 自己输出 `DONE` 或达硬上限终止。
4. **原地重写用三分类协议**（不是裸覆盖，§5.3）：对旧页每条论断标 `keep`/`revise`/`remove_with_reason`，防止"新简介裸替换旧正文"静默冲掉未被新素材提及但仍有效的旧论断。
5. **论断级验证**（§5.4）：定稿拆成"关键论断"，逐条反向核对是否被 `source_uris` 指向的原始文件支持，不支持则删除或降级为"待确认"；若删除比例过半，整条候选转 `_needs_review/`，不落盘。
6. **索引同步**（§5.6，v0.2 最大缺口，v0.3 补上）：写盘成功后调用官方 URI-scoped 增量 `reindex`（**明文禁止全量 reindex**——全库 6746+ 文件全量 reindex 量级 1.5-2.5 万次 embedding 调用，是单次写入范围成本的数千倍）。

### 合并/落盘产出物结构
- `curated/`：flat 目录（无 domain 子目录，理由：目录漂移代价高于标签漂移），靠 `MEMORY_FIELDS.tags` 软分类。
- `_pinned/`：人工权威页，不参与自动重写。
- `_needs_review/`：验证未过的候选，非"只进不出"——有重新排队机制（§4.4，`needs_review_attempts.json` 记录尝试次数，超 `max_review_attempts`=3 或 120 天无新素材则标 `status: dormant`）。
- 文件格式：**不是 YAML frontmatter**，是 OpenViking 原生 `MEMORY_FIELDS` JSON 注释块（正文 + `<!-- MEMORY_FIELDS {...} -->`），只 6 个存储字段：`memory_type`/`page_id`/`tags`/`source_uris`/`created_at`/`status`。`trust`（新鲜度）不存储，读取时现算：`now - RecallIndex.last_hit_ts` 与 `stale_days`（默认60天）比较。

### 关键文件索引
| 文件 | 行数 | 职责 |
|---|---|---|
| `DESIGN.md` | 477 | 设计文档，v0.3，经四路审查修订 |
| `pipeline.py` | 828 | rethink 生成、三分类重写、论断级验证核心逻辑 |
| `orchestrator.py` | 278 | `process_one_cluster` 单簇全流程编排 |
| `cli.py` | 746 | `curate`/`status`/`archive`/`dry-run` 命令 |
| `journal.py` | 407 | 四事件崩溃恢复协议 |
| `rollback.py` | 593 | 回滚（archive 语义，不物理删除）+ checksum 一致性校验 |
| `llm_client.py` | 367 | LLM 调用封装（litellm，见依赖清单） |
| `writer.py` | 370 | 落盘格式化（MEMORY_FIELDS）+ 触发索引同步 |
| `reactivation.py` | 318 | `_needs_review/` 重新激活检测（embedding 相似度阈值 0.75） |
| `heldout_monitor.py` | 309 | Phase 3 持续监控，held-out 验证跌破基线 -15pp 触发人工复查 |
| `memfile.py` | 299 | MEMORY_FIELDS 读写格式化 |
| `config.py` | 370 | `sleep_curator.toml` 配置加载 |
| `index_sync.py` | 198 | URI-scoped 增量 reindex 调用封装 |
| `lock.py` | 158 | 原子文件锁（`O_CREAT|O_EXCL`，修正 ovmc 的 check-then-write 竞态） |
| `cluster_source.py` | 155 | 只读 ovmc `report.json`，含新鲜度前置检查（mtime 过期 fail loud） |
| `freshness.py` | 98 | 现算 fresh/stale |

---

## 三、sleep-curator 外部依赖清单（"依赖太高"具体指什么）

**不依赖**：OpenViking HTTP server（`index_sync.py` 的 `"http"` 接口**未实现**，`config.py:113-118` 明文注释"deliberate decision, not a bug"——因为 HTTP reindex endpoint 形状从当前环境不可发现，设为 http 会立即抛 `NotImplementedError`）。也不改 OpenViking 任何已有代码（"零侵入"承诺，只新增 `tools/sleep-curator/`，只读 `memories/`）。

**实际依赖**：
1. **`ov` CLI 二进制**（唯一实现的索引同步接口，`config.py:110-111,119`）：`ov reindex <uri> --mode ... --wait true`。索引同步 100% 依赖这个 CLI 存在且行为符合预期，无 HTTP fallback。
2. **LLM API**（`llm_client.py`，走 `requests` 直连，provider 配置为 `litellm`，`config.py:78-86`）：生成（rethink）、演化路径判定、论断级验证的语义核对，均需要真实 LLM 调用；`judge_model`（可选独立判题模型）用于 held-out 验证阶段（防自我一致性偏差）。API key 通过环境变量 `SLEEP_CURATOR_LLM_API_KEY` 或 `ov.conf` fallback 解析。
3. **Embedding 服务**（`config.py:87-89` `reuse_openviking_config: True`）：关联检索、演化路径判定、`_needs_review/` 重新激活检测均需要 embedding。默认复用 OpenViking 自身的 embedding 配置，非独立服务，但仍是外部调用依赖。
4. **ovmc 的产出物（只读，非代码依赖）**：`report.json`（`tools/ovmc/ovmc/report.py:51-53` 的 `cluster_size`/`min_similarity`/`max_similarity` 结构）和 `ovmc/recall_index.py` 的 `RecallIndex`（用于新鲜度现算）。sleep-curator 只读这两个产出物，不 import ovmc 代码做业务逻辑，但**数据格式耦合**：`report.json` 的 schema 变了 sleep-curator 就读不出簇。
5. **OpenViking 原生数据格式**：`MEMORY_FIELDS` JSON 注释块格式（`tools/ovmc/ovmc/memfile.py:7` 确认的现有格式）、`context_type` 按 URI 路径段自动分类（`openviking/core/namespace.py:13-16,46-67`）——写入 `memories/curated/` 路径本身就要求严格符合 OpenViking 的 namespace 约定，不能任意换路径。
6. **`requests` 库**：`llm_client.py:21`、`heldout_monitor.py:33` 直接用，无重试库封装，指数退避是自己实现的（`config.py` `retry.max_attempts=3`）。

**"依赖太高"精确含义**：不是"依赖太多外部系统"，而是**单簇处理链条上任一环节失败都会阻断整条链**——LLM 调用（生成+判定+验证，一簇个位数到十几次）→ embedding 调用（检索+重新激活检测）→ `ov` CLI（索引同步，无 HTTP 兜底）。660 簇总量级"数千至一万次 LLM 调用"（DESIGN.md §6），任何一个依赖（LLM 限流/API key 失效/`ov` CLI 行为变化/`report.json` schema 漂移）出问题，都会造成大批量簇卡在 `skipped_error`/`needs_review`。且 HTTP 接口路径完全未实现，一旦 CLI 调用方式在未来 OpenViking 版本变化，索引同步会直接失效而没有替代路径。

---

## 四、CompanyBrain（GoInsight 产品线）产出结构

路径：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/`

### 顶层分类（6 类固定业务域目录，非软标签）
```
产品定位/       使用场景索引.md   技术实现/   模块手册/   经验与坑/   规范与资产/
_config/        <- 编译元数据，非发布内容（module_rules.json / quality_report.md / structure_review.md / compile_review/）
```
模块手册下再按主题细分（如"图表与展示"），每个主题目录下有多篇具体页 + 一份"资料汇总"子目录存放清洗后的原始素材（尚未编译的候选）。

### 已编译发布页（"正式"页）的 13 字段 YAML frontmatter
以 `模块手册/图表与展示/图表类型选择.md` 为例：

```yaml
title: 图表类型选择
type: concept
page_model: derived
scope: company
product: GoInsight
section: 模块手册
module: 图表与展示
tier: 2
trust: medium
source_status: compiled
quality_status: formal
created: "2026-05-25"
updated: "2026-05-25"
generated_by: deepen_goinsight_chart_display_pages.py
tags: [company, GoInsight, 模块手册, 图表与展示]
```
= 14 个 key（`产品定位/产品定位与价值.md` 少一个 `module` 字段 = 13 个 key，"13 字段"指后者这类无 module 细分层级的页面）。**分级信息集中在 `tier`（1/2/3 重要度）+ `trust`（high/medium/low 可信度）+ `source_status`（compiled/raw）+ `quality_status`（formal/draft）四个字段的组合**，不是单一维度打分。

### 页面内部组织（知识图谱式互链）
正文本身是叙事结构（非固定模板，视内容而定），但统一有：
- **"什么时候先查这页"** 段——面向 agent 检索意图的入口引导。
- **"和其他页面的关系"** 段——用 `[[双链]]` 语法显式链接同域其他页（如"[[图表配置与样式]]"），构成一张可遍历的知识图谱，而非孤立文档。
- **"来源索引"** 段——回链到原始 Confluence/GitLab 页面 URL + 更新时间戳，保留可追溯性。
- 每个产品目录还有 `使用场景索引.md`（场景→该看哪个页的路由表）和 `产品关系与边界.md`（产品间边界说明）——这是"索引页 + 边界页"机制，专门解决"agent 该往哪个产品域查"的问题（sleep-curator 完全没有这层，因为它是 flat 目录）。

### "资料汇总"层：编译前的中间态（未编译候选）
`模块手册/资料汇总/4.1 Chart Type.md` 只有 3 个字段级信息（`GENERATED_BY` 注释 + 来源 URL + 清洗时间），正文基本是原始 HTML/Markdown 逐条搬运（`<details>`/`<summary>` 标签原样保留），仅有"主要内容"/"使用边界"两个粗分段，**没有跨图表类型的统一规则提炎、没有排查路径、没有双链**。对比编译后的 `图表类型选择.md`——后者把散落在 14 个独立 FAQ 条目里的"配置规则"（1 维度1指标之类）合并成统一的"常见图表配置边界"表述，新增了原始素材完全没有的"排查路径"（问题定位步骤）、"选错图表的常见表现"（反向索引：症状→原因）。**这一步跨越（资料汇总→正式页）才是真正的"知识密度提升"发生的地方，是人工/半自动脚本（`generated_by` 字段记录的脚本名）驱动的，不是自动化管线兜底产出**。

---

## 五、对比源文档：具体丢弃了哪些类别的信息

对比链条：`SourceArchive/company/gitlab/docs-center-res/repo/insight/4.1 Chart Type.md`（原始 GitLab 文档）→ `模块手册/资料汇总/4.1 Chart Type.md`（"已清洗"中间态）→ `模块手册/图表与展示/图表类型选择.md`（正式发布页）。

**原始文档结构**（`insight/4.1 Chart Type.md`）：一段导语 + 一张架构截图 + 14 个 `<details>` FAQ 折叠块，每个图表类型一段独立说明，包含具体配置规则数字（如"Comparison Bar Chart 需要 1 dimension + 2 indicators"）。

**"资料汇总"清洗步骤丢弃/劣化的信息**：
1. **架构截图**（`![](https://img.s3.whatspos.com/...)`）——图片引用被完全剔除，清洗产物只保留纯文字，图表布局这类只能靠截图理解的界面细节永久丢失。
2. **HTML 语义结构降级为扁平列表**：14 个 `<details>` 折叠块被打散成"主要内容"里几条摘录 + "使用边界"里几条打了 `[Chart type]`/`[FAQ]` 前缀的碎片，**14 种图表类型里只保留了 2-3 种的只言片语**（Cross Table、Table 的部分），其余 11 种图表类型（Bar/Column/Double Y-Axis/Line/Pie/Tree Map/Digital Card/Scatter/Map/Track Map/Heat Map）的配置规则在清洗阶段**直接消失**，脚本（`clean_product_source_docs.py`）只是做了截取式摘录，不是全量保留。
3. **时效元数据退化为"未知"**：`页面 ID：未知；上游更新时间：未知`——原始 Confluence/GitLab 页面的更新时间戳信息在清洗环节没有正确提取，"资料汇总"层的时效判断字段直接写"未知，使用时需要回到来源核对"，相当于放弃了这个维度。

**编译（正式页）阶段的补偿与再次损耗**：
- **补偿**：`图表类型选择.md` 实际上是绕开"资料汇总"的残缺摘录，**重新回到完整信息集合做二次整理**（14 种图表类型全部覆盖，含配置规则数字如"交叉表最多支持左侧和顶部共 6 个维度字段"、"双轴图指标最多可到 8 个"），补上了"资料汇总"丢的 11 种图表信息，还新增了原始文档完全没有的"排查路径"和"选错图表的常见表现"（这是编译脚本/人工在原始信息基础上做的归纳提炼，非原文本有）。
- **仍然丢失**：截图/界面视觉信息全程未恢复；时效戳仍是"未知"（`来源索引`部分沿用了模糊的更新时间，且部分链接指向内部 Confluence，外部不可达时无法核验）；原始文档里 markdown 分隔符 `***` 划分的"# Chart type / # FAQ"两大板块结构被拉平成 9 个语义子标题，原文"这是产品说明 vs 这是常见问答"的双层结构区分消失。

**"结果太简略遗漏太多知识"反馈的机制定位**：
- 反馈更可能指向**资料汇总层**（`模块手册/资料汇总/*.md`）——这一层的清洗脚本是**截取式摘录**（只挑"主要内容"几条 + 打标签的"使用边界"），系统性丢弃未被摘录到的原始条目（本例中 14 种图表丢了 11 种），且没有任何验证机制检查"摘录是否完整覆盖原文"。
- 已编译"正式页"层（本例 `图表类型选择.md`）本身信息密度是**提升**的（覆盖更全、新增排查视角），但**并非所有产品/模块都推进到了"正式页"阶段**——`Release 2025.1.md`（`经验与坑/` 目录下）经核实**仍停留在资料汇总的原始清洗态**（只有 `GENERATED_BY` 注释，无 YAML frontmatter，无 tier/trust 分级，正文仍是"主要内容/使用边界/来源"三段式摘录，同样有"Data Analysis 高级模板报表"等条目被截断式摘录、原文完整功能列表未必全覆盖）。**换言之，CompanyBrain 内部同一产品下"编译完成度"参差不齐：模块手册的图表类页面已推进到正式页，经验与坑的版本发布记录仍停留在资料汇总态**——用户反馈的"简略遗漏"很可能同时来自（a）尚未编译到正式页的大量资料汇总态文档，和（b）资料汇总清洗脚本本身的截取式摘录丢信息。

---

## 六、两个系统的核心差异总结

| 维度 | sleep-curator | CompanyBrain |
|---|---|---|
| 分类 | flat + 软标签（tags），无 domain 目录 | 6 固定业务域目录 + 场景索引页 + 边界页，主题驱动 |
| 字段 | 6 个存储字段，`MEMORY_FIELDS` 原生格式 | 13-14 个 YAML frontmatter 字段（tier/trust/source_status/quality_status 四维分级） |
| 生成方式 | 多轮 rethink + 论断级验证，自动化管线 | 脚本清洗（资料汇总）+ 人工/半自动编译（正式页），两阶段，编译阶段推进程度不一 |
| 知识图谱 | 无——`_needs_review/`/`_pinned/` 只是状态标记，无跨页链接 | 有——`[[双链]]` + 索引页 + 边界页构成可遍历图 |
| 已知短板 | 索引同步无 HTTP 兜底、依赖链条长（LLM+embedding+ov CLI 任一环失败即阻断）、rethink 轮数上限未经大规模验证 | 资料汇总层截取式摘录系统性丢信息（本例 14 种图表丢 11 种）、编译完成度参差（同产品下有的模块到正式页，有的仍卡资料汇总态）、时效元数据大量退化为"未知" |

---

## 参考文件清单

- `/Users/Hugh/Hugh/Project/OpenViking/tools/sleep-curator/DESIGN.md`（477 行全文已读）
- `/Users/Hugh/Hugh/Project/OpenViking/tools/sleep-curator/sleep_curator/orchestrator.py:95-174`
- `/Users/Hugh/Hugh/Project/OpenViking/tools/sleep-curator/sleep_curator/config.py:60-200`
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/模块手册/图表与展示/图表类型选择.md`
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/模块手册/资料汇总/4.1 Chart Type.md`
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/产品定位/产品定位与价值.md`
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/经验与坑/Release 2025.1.md`
- `/Users/Hugh/Hugh/Knowledge/SourceArchive/company/gitlab/docs-center-res/repo/insight/4.1 Chart Type.md`
- `/Users/Hugh/Hugh/Project/OpenViking/data/viking/default/user/default/memories/entities/knowledge_base/company_brain.md`
- `/Users/Hugh/Hugh/Project/OpenViking/data/viking/default/user/default/memories/events/2026/07/05/sleep_curator_vs_company_brain_clarified.md`
