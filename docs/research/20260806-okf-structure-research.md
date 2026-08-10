# OKF v0.2 知识结构与信号研究

调研日期：2026-08-06  
范围：只阅读 Google Cloud 官方 OKF 博客，以及 `GoogleCloudPlatform/knowledge-catalog` 的 `okf/` 规格、样例和参考实现源码。GitHub `main` 本次读取到的提交为 `930b65fc3f5619d5d0591f88c72ebae8b848d60d`。

## 一句话结论

OKF v0.2 是一个“目录树里的 Markdown 概念文件 + YAML frontmatter + 普通 Markdown 链接”的交换格式，不是知识库运行时、图数据库或发布平台。它最值得 KnowledgeDigest Task2+ 借鉴的是：把来源、生成者、验证事件、生命周期和新鲜度放到正文读取前就能访问的 frontmatter；最不能照搬的是它的极简合规线、无类型链接和 advisory trust tier。KnowledgeDigest 仍需保留自己的 TopicIndex、Claim/Evidence/Provenance、读者包/审计包、原子写回和 `published/degraded`、`released/not_released` 两层状态。

## 1. 官方来源与事实边界

### 官方博客

- [Introducing the Open Knowledge Format（2026-06-13，v0.1）](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)：OKF 的初始定位、目录/概念/链接模型、`index.md` 和 `log.md`、git/文件分发、参考 agent 和静态 viewer。
- [Open Knowledge format v0.2 tackles agentic trust（2026-07-24）](https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals/)：v0.2 为什么增加 provenance、trust、freshness、lifecycle、attestation，以及这些字段必须在 frontmatter 的理由。

### GitHub 规格和参考实现

- [OKF v0.2 `SPEC.md`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)：规范性结构、字段、信号、链接、索引、日志、Attested Computation、合规和 v0.1 迁移。
- [`okf/README.md`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/README.md)：参考 agent、样例 bundle、静态 viewer 和分发方式的实现说明。
- [`bundle/document.py`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/src/reference_agent/bundle/document.py)：frontmatter 解析、`type` 校验、`verified` 归一化、trust tier 和 stale 判断。
- [`bundle/index.py`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/src/reference_agent/bundle/index.py)：按目录和 `type` 重建 `index.md`，并使用 `title`/`description` 做渐进披露摘要。
- [`bundle/paths.py`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/src/reference_agent/bundle/paths.py)：概念 ID 与 `.md` 路径转换及路径段安全校验。
- [`tools/bundle_tools.py`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/src/reference_agent/tools/bundle_tools.py)：写入时自动补 `generated`，以及 web pass 不得缩减 BigQuery schema/source 的保护。
- [`runner.py`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/src/reference_agent/runner.py)：先逐概念写入，再执行受限 web pass，最后重建索引。
- [`viewer/generator.py`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/src/reference_agent/viewer/generator.py)：离线把概念和 Markdown 内链编译成 self-contained HTML graph，并显示 v0.2 信号。
- [`bundles/acme_retail/`](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf/bundles/acme_retail)：v0.2 的完整样例，覆盖来源、trust、lifecycle 和 Attested Computation。

下文的“OKF 事实”只来自以上官方链接；“对 KnowledgeDigest 的建议”是结合当前 Task2+ PRD 的设计判断，不把 OKF 的建议性内容冒充为 KnowledgeDigest 既有合同。

## 2. OKF v0.2 的知识结构

### 2.1 Bundle、目录和身份

OKF bundle 是自包含的 Markdown 目录树，分发单位是整个 bundle。根或任意子目录可以有 `index.md`（目录清单）和 `log.md`（更新历史）；所有其他 `.md` 文件都是 concept 文档。`index.md` 和 `log.md` 是保留文件名，不能拿来命名概念。目录如何按领域、表、指标、流程或其他方式组织由 producer 决定，不存在中心 taxonomy 或 schema registry。

概念身份是文件路径去掉 `.md` 的 Concept ID。文件路径因此是一个稳定的可 diff 身份，但它仍然是 bundle 内部身份，不是跨 bundle 的全球 ID。bundle 推荐作为 git repository 发布，也允许 tar/zip 或大仓库子目录。

`index.md` 的目标是 progressive disclosure：先看一层目录，再打开需要的概念；条目通常带标题、相对链接和简述。消费者可以在缺少 index 时扫描 frontmatter 现场合成。`log.md` 使用 ISO 日期倒序记录更新历史。

`index.md` 通常不带 frontmatter；唯一例外是 bundle 根的 `index.md` 可以用 frontmatter 声明 `okf_version: "0.2"`。消费者即使不认识该版本，也应尽力读取而不是拒绝整个 bundle。

### 2.2 Concept、类型和实体边界

每个 concept 是一个 UTF-8 Markdown 文件，frontmatter 只有 `type` 为强制字段；`type` 是短字符串，不注册、不要求固定枚举。消费者必须容忍未知 type，通常按 generic concept 处理。示例包括 BigQuery Table、Dataset、API Endpoint、Metric、Playbook、Reference 和 `Attested Computation`。

推荐字段是 `title`、`description`、`resource`（底层资产 URI）和 `tags`。body 没有强制段落；`# Schema`、`# Examples`、`# Computation` 只是约定标题。未知 frontmatter key 和未知 body 结构应被保留，便于 producer 扩展。

### 2.3 关系：目录隐含父子，Markdown link 表达其余关系

概念之间使用普通 Markdown link。以 `/` 开头的 bundle-relative link 最稳定；相对 link 也支持。链接表示有向关系，但 OKF v0.2 不定义边类型：`parent/child`、`references`、`joins-with`、`depends-on` 等语义由周边正文表达。消费者通常把它们当作 untyped directed edges，并可从反向边生成 backlinks。

断链不是格式错误，消费者必须容忍；这让知识可以先链接到尚未写入的概念。`references/` 是常用但非强制的目录约定，用来把外部材料、executor、attester 或代码也作为 bundle 内概念引用。

来源的 lineage 也不另造专用图字段：如果 `resource` 指向另一个 OKF concept，消费者可以沿链接递归读取该 concept 的 `sources`；更深的外部 `derived_from` 或完整数据血缘不在 v0.2 范围内。

### 2.4 Attested Computation 是“可验证计算”实体

`type: Attested Computation` 是 v0.2 新增的概念类型。它把一个 sanctioned computation 单独建成 concept，再让 Metric 等普通概念用 Markdown link 引用它；这样每个计算有独立的 trust、freshness 和 attestation 状态。

该类型要求 `runtime`；通常还声明 typed `parameters`、inline `# Computation` 或 `computation` 文件、`executor.resource`/`receipt` 和 deterministic no-LLM `attester.resource`。executor 返回的 receipt 是运行时产物，不写入 bundle。OKF 只固定接口，不规定脚本、Skill、容器等资源如何打包，也不执行计算。

## 3. Frontmatter、metadata 和 trust signals

### 3.1 基础 frontmatter

最小合法概念可以只有：

```yaml
---
type: Reference
---
```

常见字段及用途：

| 字段 | 语义 | 约束 |
| --- | --- | --- |
| `type` | 概念类型 | 唯一始终必填；值不注册 |
| `title` | 读者显示名 | 缺省时可由文件名派生 |
| `description` | 一句摘要 | 供索引、搜索和 preview |
| `resource` | 底层资产 URI | 抽象概念可不填 |
| `tags` | 横切标签 | YAML 字符串列表 |

消费者不能因为缺少可选字段、未知 type、未知扩展 key、断链或缺少 index 而拒绝 bundle。

### 3.2 `sources`：来源和可解释的 credibility signals

`sources` 位于 frontmatter，描述 concept 从哪些内外部材料得到。每个 entry 的 `resource` 必填，可选 `id`、`title`、`author`、`usage_count`、`last_modified`。`usage_window: {from, to}` 是 sibling，用来解释所有 `usage_count`；单个 entry 可以覆盖共享窗口。

OKF 只记录客观信号，不写统一 credibility score：分数主观、跨消费者不可移植，并会在写入后过时。`usage_count` 只适合判断活跃/沉寂、趋势或数量级，不能当跨来源类型的精确排名。`last_modified` 是来源本身的修改时间，和 concept 自己的 `generated.at` 不同。

正文对单个 claim 的归属使用脚注，脚注 label 必须等于 `sources[].id`。使用稳定 `id` 而不是 `sources[0]`，是为了在 agent 重排 sources 后仍不发生静默错配。

### 3.3 `generated` 与 `verified`：写入者和确认者分开

`generated: {by, at}` 记录当前正文由谁产生、何时最后一次有意义地改变。`verified` 是一个 `{by, at}` 事件列表，记录针对来源或底层 resource 的独立确认；单个事件可以写成 bare mapping，消费者必须按一项列表处理。

两者故意分开：agent 可以生成、人或 process 可以确认；正文修改可以早于重新确认，重新确认也不必重新生成。Actor 约定是：agent/tool 用 `<producer>/<version>`，人用 `human:<id>`，自动过程用 `process:<id>`。

从 `verified` 派生三档 advisory trust tier：没有 key 是 `unverified`；只有非 `human:` actor 是 `machine-confirmed`；任意 `human:<id>` 事件使其为 `human-reviewed`。这不是 ACL，也不等于允许发布；它只是消费者在搜索、筛选和展示时可用的信号。

### 3.4 `status` 与 `stale_after`：生命周期和新鲜度

`status` 为 `draft | stable | deprecated`，缺省等于 `stable`。`deprecated` 的概念仍保留以支撑旧链接和历史重现，但不应被新工作默认使用。

`stale_after` 是绝对日期；当 `today >= stale_after` 时视为 stale。OKF 特意不用相对 TTL，使 deterministic consumer 只需做日期比较，不依赖“何时读到”这个变量。

### 3.5 Attestation 与验证不是一回事

`verified` 是慢速、文档级的定义确认，写回 bundle；attestation 是每次调用的运行时检查，确认本次 receipt 的实际 computation、参数绑定和返回值是否符合 sanctioned contract，receipt/verdict 不存入 bundle。消费者应在 attestation 失败时拒绝显示，或至少显式告警；定义 stale 和运行 attestation 是两条独立轴。

### 3.6 v0.1 迁移兼容

v0.2 是 minor bump，但有两个有意的字段替换：`timestamp` 被 `generated.at` 取代；正文 `# Citations` list 被 `sources` 取代。v0.2 consumer 可以兼容读取旧字段，因此 v0.1 bundle 可以原样被 v0.2 consumer 消费。

## 4. 官方参考实现如何生成和发布

这部分描述源码的参考实现，不是 OKF 的强制运行时：

1. BQ pass 按 source advertises 的概念逐个写 concept doc；web pass 从显式 seed URL 出发，受 `max_pages`、hop depth、allowed hosts/path 和 denied substrings 限制，决定 enrich 既有 concept、建立 `references/<slug>`，还是跳过。
2. `write_concept_doc` 只要求 `type`，缺失时自动补 `generated`；web pass 对已有 BigQuery Table 检查 schema 字段和 `sources` 数量不能缩减，避免 enrichment 覆盖底层 metadata。
3. 全部 concept 写完后重建各级 `index.md`。参考 `index.py` 按 `type` 分段，条目使用 `title`/文件名和 `description`；目录说明可能由模型生成，但有确定性 fallback。
4. `visualize` 读取所有非 `index.md` 的 Markdown，解析相对 `.md` 链接生成 directed graph、反向 backlinks、搜索和 type filter；把 frontmatter/body 一次性嵌入单 HTML。viewer 也展示 `status`、trust tier、stale badge、generated、verified 和 sources。
5. README 明确 producer/consumer 独立，bundle 可以由 git、静态文件服务器、知识 UI、LLM、搜索索引或 graph viewer 消费。静态 viewer 只是一个 proof-of-concept consumer，不是规范要求。

实现层的三个值得注意的“软语义”是：`document.py` 的 parser 以 `type` 为唯一 required key；`normalize_verified` 将 mapping 归一成 list；`paths.py` 只允许安全的 ASCII-ish path segment。它们是可复用的工程参考，但不应覆盖 KnowledgeDigest 更严格的安全/溯源合同。

## 5. 不能直接照搬到 KnowledgeDigest 的部分

### 5.1 “只有 `type` 必填”不能成为正式发布门

OKF 的目标是跨工具交换，所以把其余字段都做成 optional，并要求消费者宽容。KnowledgeDigest 的正式页必须回答用途、边界、版本、Evidence 和 Provenance，并且每条 Claim 要有 source URI、指纹和定位；这些是产品发布合同，不是 OKF 最小互操作合同。可以采用 OKF 的字段命名/语义作为 reader projection，但不能放宽现有缺失字段和 fail-closed 门禁。

### 5.2 路径身份不能替换 TopicIndex 和旧路径映射

OKF 把文件路径作为 Concept ID，适合一个 producer 自己管理 bundle。KnowledgeDigest 已把 `digest_topic_id`、`topic_key`、首次 published path 和 `old_path_mapping` 分开，以处理主题合并、拆分、输入顺序变化和分页。不能把 `path` 当成主题全球身份，也不能因 OKF 风格目录重命名而丢历史映射。

### 5.3 无类型 link 不能替换显式关系和相关主题证据

OKF 允许所有关系都只是 directed untyped link，且断链容忍。KnowledgeDigest 的 `related_topics`、`claim_refs` 和 affected set 需要能说明关系为什么存在、由什么证据支持；正式导航的失效链接应该 fail-closed，而不是按 OKF 的宽容规则悄悄放过。可以把 Markdown link 作为读者边的渲染形式，但内部仍保留 typed relation + evidence。

### 5.4 advisory trust tier 不能直接映射 released

OKF 明确 trust tier 不是 ACL，也不代表发布许可。KnowledgeDigest 必须继续分离 `machine_pass`、`agent_assisted`、`human_reviewed`，以及页级 `published/degraded` 和交付级 `released/not_released`。`verified: human:*` 只能成为读者可见 trust signal，不能绕过 reader gate 或覆盖失败来源。

### 5.5 `sources` 不能成为第二份溯源事实源

OKF 的 `sources` 很适合概念级来源清单和正文脚注。KnowledgeDigest 的审计账本仍应以 source manifest、Claim/Evidence/Provenance records、content fingerprint 和 locator 为权威；Reader Package 的 `sources`/source-index 只能是同一 records 的投影。不要让模型自由重建 sources，也不要把 `usage_count` 当排序分数。

### 5.6 Attested Computation 不是当前 Task2 的默认范围

OKF 的 executor/attester 合同有价值，但 v0.2 把 runtime protocol、receipt/verdict wire format、attester ABI 和 sandboxing 明确留给未来。KnowledgeDigest 当前任务是离线读者发布，不应为了“像 OKF”引入计算执行器、脚本打包或新的运行时；如未来要表达可复算指标，应另立 scope revision，并把 receipt 留在 Audit Package。

### 5.7 optional index/log 和 reference agent 不能覆盖本项目发布合同

OKF 允许没有 `index.md`，而 KnowledgeDigest 的 Home、父/叶分类索引、来源索引、Reader README 和原子发布是既定入口。OKF reference agent 的 BQ+web LLM 两 pass、web crawler 和 fallback 也不能替代 KnowledgeDigest 的 qwen allowlist、`--no-llm`、Jaccard fallback、预算和批次恢复合同。

## 6. 对 KnowledgeDigest Task2+ 的具体建议

### 6.1 采用“OKF-like reader projection”，不改保存层权威

- 在现有正式主题页 frontmatter 中**增量映射** `type`、`title`、`description`、`resource`、`tags`；继续保留 `digest_topic_id`、`topic_key`、`published_path`、managed marker 等本项目字段。
- 在有可靠证据时增加 `generated: {by, at}`、`verified: [{by, at}]`、`status`、`stale_after` 和 `sources`。这些字段用于读者筛选和展示，不取代 source manifest 或 Provenance。
- `generated.at` 表示页面内容最后一次有意义变化；来源自身 `last_modified`、Claim 的 locator/fingerprint 和运行时间继续分开记录。
- `verified` 的 bare mapping/list 两种输入统一归一；actor 采用 OKF 约定，但不要把 `human:` 自动解释成整包发布批准。
- `usage_count` 只有在能给出明确 `usage_window` 且读者需要活跃度提示时才保留；禁止作为跨来源精确排名或标题/分类依据。

### 6.2 把 frontmatter 信号接入 Reader Package 的“先筛后读”路径

OKF v0.2 的核心洞察是读者/agent 往往先看元数据再决定是否打开正文。Task2+ 可以在 Home、分类页和主题页顶部展示：页面类型、`status`、trust tier、stale 提示、来源数和最后生成时间。筛选条件必须是可重放的 deterministic filter；页面正文仍保留 Summary、Why/适用边界、Version、Evidence、Provenance。

建议的机器门：

- `status=deprecated` 不进入默认新任务入口，但旧链接和历史页保留；
- `stale_after` 使用绝对日期比较，stale 只提示需要复核，不自动删除；
- 缺少 `verified` 显示 `unverified`，机器确认与人工确认分开显示；
- `sources[].id` 与正文 claim footnote/`claim_id` 做稳定键校验，重排 sources 后仍不变；
- frontmatter 未知扩展 key 保留，不因 round-trip 丢失。

### 6.3 关系采用“内部有类型、外部用 Markdown”

保留现有 TopicIndex/affected set 的关系证据，至少记录 `relation_kind`、source topic、target topic、Claim/Evidence 引用和可读原因；Reader Package 再渲染成普通 Markdown link。这样能获得 OKF 的可读/可移植入口，又不会失去 KnowledgeDigest 的语义关系和链接审计。正式导航链接失效时继续 fail-closed；“断链可容忍”只适用于可选 OKF 导出或非正式草稿。

### 6.4 目录和发布：借鉴 progressive disclosure，保留双包边界

- 读者主轴仍是 `Home.md → indexes/<parent>.md → 叶分类/产品/模块 → 主题页`，不要改成按 OKF 任意目录自由组织；目录由 `kb.structure.md` 和 TopicIndex 控制。
- 可以在每个公开目录生成 OKF 风格 `index.md` 作为静态交换/导出视图，但不要把它变成第二份导航事实源；生成内容必须来自同一 TopicIndex/records，稳定排序、原子发布。
- Reader Package 可以作为 git 目录或 tar/zip 分发；Audit/Archive Package 仍单独保存快照、Claim、Evidence、运行日志、失败原因和恢复材料。不要把 `_digest`、`_archive` 和 provider 原始响应混入默认阅读入口。
- OKF 的 self-contained HTML viewer 可作为离线 QA/分享物；它不能替代 Home、分类索引、来源回溯或正式 reader gate。

### 6.5 把 OKF 信号写进 Task2+ acceptance，而不是只做字段填充

建议新增/明确以下验收样例：

1. **元数据先行**：从 Home/分类页不打开正文就能看到 type、用途摘要、status、trust tier、stale、来源数；抽样页标题能表达主题用途。
2. **来源键稳定**：sources 重排、重复运行和分页后，正文脚注/`claim_id` 仍指向同一 source id；每条 Claim 仍只有一个当前 target path。
3. **信号归一**：bare `verified` mapping 与 list 得到相同 trust tier；没有 `verified` 明确显示 unverified；来源 `last_modified` 不被误当成生成时间。
4. **生命周期**：`status=deprecated` 保留旧路径但默认入口隐藏；`stale_after` 在当天及之后 deterministic 告警；两者不删除内容、不伪造 released。
5. **关系可回溯**：读者内链可导航，内部 relation record 有 kind/reason/evidence，坏 link 和未知 topic 在正式写回前被拦截。
6. **发布分离**：Reader Package 离线可读；Audit/Archive Package 可回放来源、指纹、Claim、失败和归档；source-index/Home/主题页同批归档后原子发布。
7. **失败边界**：LLM/provider 失败时只走已有 deterministic fallback，不能因为 OKF 的宽容 optional fields 把缺失 Summary/Why/Version 伪装成合格正文；`degraded` 不进入 `released` reader package。

### 6.6 Attested Computation 的后续边界

只在明确的 scope revision 后考虑把某些“可复算指标/规则”建成 `Attested Computation` 投影。届时应：

- 计算定义、参数、executor、attester 作为独立概念/审计对象；普通主题只链接它；
- receipt/verdict 存 Audit Package 或运行记录，不写入静态正文；
- attester 必须 deterministic、无 LLM，并有独立的 ABI/sandbox/失败合同；
- `verified`（定义复核）和 attestation（本次运行）仍分别验收。

当前 Task2+ 不引入 executor、attester、runtime 或 provider 运行时。

## 7. 最终判断

OKF v0.2 适合作为 KnowledgeDigest 的**交换形状和读者信号参考**：一个概念一页、frontmatter 先筛选、sources 以稳定 id 对 claim、生成与验证分离、绝对日期 freshness、Markdown link 形成可移植图。它不适合作为 KnowledgeDigest 的完整业务合同：OKF 故意不定义 taxonomy、页面类型、typed relations、原子发布、来源清单闭合、Claim 级证据或 reader acceptance。

因此 Task2+ 的最稳路径是：保存层和发布门继续由 KnowledgeDigest 自己负责；Reader Package 可提供一个受控的 OKF-like projection/导出；所有 OKF 字段都从现有权威 records 确定性生成，并把 trust/freshness 变成读者可见的筛选信号，而不是把 OKF 的宽容合规线倒灌进正式发布。
