# KnowledgeDigest 知识发布架构 PRD

**版本**：v1.7
**日期**：2026-08-06
**状态**：Task 0/Task 1 已完成；Task 2 实施前最终合同修订版（已吸收最终三方盲审）
**适用范围**：Task 0–Task 3 的知识发布架构，以及 Task 3-Closeout 的文档和仓库收口

## 0. 这份 PRD 怎么用

这份文档是后续新任务的唯一业务需求入口。它把今天的原始方案、Task2 结果审查、CompanyBrain 对照、21 份研究/盲审材料和 3 路默认首层盲审压成一套可执行的需求、方案和验收合同。

今天的原始报告不删除。它们是证据附件；本 PRD 是决策和任务入口。报告与本 PRD 冲突时，以本 PRD 的冻结决策和验收标准为准，原始报告只用于追溯证据。

本 PRD 不推翻原来的 S1–S6 保存、安全和溯源底座，而是在其上补齐“知识编译与读者发布层”。目标不是把 Markdown 重新排版，而是让用户能从一个产品、模块或实际问题出发，快速找到能独立阅读、能判断边界、能追溯来源的知识。

本版吸收默认 `3rd-review` 首层 `pi/k3`、`opencode/v4flash`、`antigravity/flash` 的三轮有效盲审，以及 2026-08-06 对 Google OKF v0.2 的官方资料审查。历史 `cursor/grok`/`claude-code/opus` 报告只作历史证据，不代表当前默认路由。Task 0 和 Task 1 已在 `main` 完成；Task 1 只产出 TopicIndex 控制面，不是读者知识结果。原来的 Task 2 拆成 2-A、2-B、2-C：先固定可读文件合同，再编译小语料正文，最后做信任信号和读者质量门；不通过小语料门，不得进入 89 条全量发布。

盲审建议的取舍已经冻结：采纳稳定主题身份、词典治理、状态分层、题集冻结、语义分页、占位禁止、claim-id、人工修改保护、调用预算和总览前置条件；不采纳“embedding 失败一律硬失败”（保留既有整次 Jaccard fallback 合同）、“单来源一律降级”、正文复制率硬阈值、精确三字段硬编码、增加十维本体/永久人工队列/数据库图谱，以及为完整性而每次全量重规划。

## 1. 一句话结论

KnowledgeDigest 当前主要是“来源保真和审计发布器”，还不是“可读知识发布器”。

修复路线固定为：

```text
S1–S6 保真层
  → 结构归一化
  → 受管产品/模块主题索引
  → 三类类型化页面编译
  → 机器质量门 + 读者质量门
  → 读者包与审计/档案包分离发布
```

严格按以下顺序实施：

```text
Task 0 诚实化与交付包
  → Task 1 产品/模块/主题主轴
  → Task 2-A OKF-compatible Reader Bundle 与 Concept Contract
  → Task 2-B 小语料知识对象规划与正文编译
  → Task 2-C 信任信号与读者质量门
  → Task 3 全量发布与读者验收
  → Task 3-Closeout 文档同步、清理与归档收口
```

### 1.1 当前状态和任务边界

- **Task 0 已完成**：保存完整性、账本对账、失败隔离、Reader/Audit 分包和页级/交付级状态已是现有底座。
- **Task 1 已完成**：`topic_axis.py` 只生成 `_digest/source-inventory.jsonl`、`topic-plan.json`、`topic-index.json` 和运行报告，状态为 `not_released`；它负责稳定身份和主题规划，不负责生成可读正文。
- **当前问题不应通过重做 Task 1 解决**：下一阶段缺的是“Concept 是什么、读者如何进入、正文如何编译、信任信号如何展示”的发布层。
- **Task 2 采用 2-A → 2-B → 2-C 三个小任务**。2-A 和 2-B 只使用隔离 fixture/小语料；2-C 通过后才允许 Task 3 使用 89 条全量语料。
- **OKF 只作为文件交换和读者信号 profile**：不替换 TopicIndex、Claim/Evidence/Provenance、原子写回、`published/degraded` 和 `released/not_released`。

## 2. 背景和真实问题

### 2.1 用户真正需要的产品

KnowledgeDigest 要服务个人和企业知识消化，不是简单的 Markdown 重写脚本。用户打开结果后，应能完成这些动作：

- 从 Home 进入产品或系统；
- 看到产品下有哪些模块、能力和使用场景；
- 打开一页后，直接知道“这是什么、什么时候用、怎么做、有什么限制”；
- 看到版本、异常、前置条件和来源；
- 在不打开原始文档的情况下理解主答案，需要审计时再回到原文和 Claim；
- 新资料到来时只更新受影响主题，不因批次顺序改变目录和页面身份；
- 失败资料不会伪装成正式知识，也不会覆盖已有的好页面。

### 2.2 Task2 结果的硬证据

结果目录：Task2-Qwen final9（证据 ID：`task2-qwen-final9-20260804`；本机路径只保存在研究附件）

对结果的本地审计显示：

- 86 个主题、120 个页面，其中 34 个分页；85/86 个主题只有单一来源；
- `product_slug` 非空数量为 0；21 个叶分类只有 8 个非空，13 个为空；
- 58/120 个页面的 Summary 是“请阅读 Evidence”类占位；58/120 个 Why 是“来源未说明”类占位；
- 54/120 个页面缺少有效版本信息；120/120 个页面 Related topics 为空；
- 约 31 个来源失败或 `needs-review`，但仍被运行结果和导航部分包装成成功；
- 89 个批次、`batch_size=1`，把来源/批次边界错误地变成了主题边界；
- source-index 只有 88 行，而 batch/snapshot 记录有 89 个来源；
- 运行现场约 279MB，其中 `_digest`、`_archive` 和 provider 日志混在用户阅读目录，正文只有约 4.9MB；
- 出现 `topic-<hash>`、`1.md`、`ae.md`、`ios.md` 等无法脱离路径理解的主文件名；
- Evidence 保留了原文，却没有经过“问题—结构—页面类型”的编译，所以内容像原始资料堆积，不像知识。

这些不是“文件名不好看”或“分页阈值不合适”的单点问题，而是产品目标错位：Task2 优先保证保存和溯源，却没有知识本体、正文编译和读者质量合同。

### 2.3 CompanyBrain 为什么更好

CompanyBrain 参考语料（证据 ID：`companybrain-reference`）的可借鉴点不是文件多，而是它先定义了读者如何理解知识：

- Home 和 Products 是明确入口；
- 产品 → 模块 → 技术/经验/场景页面是主轴；
- 每一跳都有“适用范围、边界、下一步”，不是只有链接；
- 页面有类型和质量元数据，正文标题按问题组织；
- 原始资料、编译资料和正式页有不同职责；
- 来源、版本、信任度和状态可以审计。

CompanyBrain 自身也有不确定模块和内容不均衡的问题，因此本项目借鉴方法，不复制其规模、人工脚本和全部目录。

## 3. 参考资料和证据边界

### 3.1 权威业务参考

1. [`docs/plans/universal-knowledge-digest-design.md`](./universal-knowledge-digest-design.md)：原始 S1–S6 设计和非目标。
2. [`specs/archive/knowledge-digest-llm-naming-classification/`](../../specs/archive/knowledge-digest-llm-naming-classification/)：Task2 的语义命名、分类、分页和导航规格；它是历史实现记录，不是完整知识编译方案。
3. `companybrain-reference`：读者体验和信息架构参照；实际路径只在研究附件中保留。
4. [`docs/plans/summary-evidence-output-design.md`](./summary-evidence-output-design.md)：Summary/Evidence 历史输出合同；其中“正文逐字包含 Claim”的部分被本 PRD 明确替代。
5. [Google Cloud：OKF v0.2 trust signals](https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals)：官方说明 provenance、trust、freshness、lifecycle、attestation 五类信号，以及“信号记录不等于信任评分”的原则。
6. [OKF v0.2 SPEC.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) 和 [OKF README](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/README.md)：Markdown + YAML frontmatter、`type`、`sources`、`generated`、`verified`、`status`、`stale_after`、`index.md`、`log.md`、标准 Markdown cross-links 和宽松扩展规则。

### 3.2 今天新增的研究文件

以下 21 份文件在 Task 3-Closeout 前保留在 `docs/research/`，其核心结论已经写入本 PRD；Closeout 后统一迁入带日期的研究归档目录，并由研究索引和本 PRD 保留可追溯入口：

| 研究文件 | 已吸收的核心结论 |
|---|---|
| `20260804-knowledge-publication-fix-direction.md` | 保存层已成形，知识产品层缺失；提出两层架构和问题总诊断 |
| `20260804-knowledge-publication-blind-review-synthesis.md` | 初版三方盲审综合；冻结三类页面、两态发布和四任务顺序（后续已拆为 Task 2-A/2-B/2-C，并增加 Closeout） |
| `20260804-companybrain-comparison.md` | CompanyBrain 的本体、正文、导航和治理差异 |
| `20260804-companybrain-content.md` | Task2 内容质量统计、占位和标题问题 |
| `20260804-companybrain-ia.md` | 两套信息架构和产品/模块主轴差异 |
| `20260804-companybrain-reader-journey.md` | 真实阅读路径、空分类、死入口和跳转信息对照 |
| `20260804-output-audit.md` | Task2 总体审计；绿色机器检查不等于读者质量 |
| `20260804-output-content-quality.md` | Summary/Why/Version/Related 和 Evidence 可读性证据 |
| `20260804-output-navigation.md` | Home、分类、pending、source-index 和分页导航问题 |
| `20260804-output-provenance-integrity.md` | 账本不闭合、重复不幂等、状态误报和写回时序问题 |
| `20260804-design-compliance.md` | 原方案 S1–S6 的实际实现度和未实现项 |
| `20260804-design-research-coverage.md` | 原方案对工程安全充分，对知识价值和读者质量不足 |
| `20260804-design-s1-s3.md` | S1–S3 的聚类、检索、产品归属和增量索引缺口 |
| `20260804-design-s4-s6.md` | S4 正文编译、old body、S5 事务和 S6 时序缺口 |
| `20260804-blind-review-pi-k3.md` | 先做账本、失败隔离和交付包；增量和四类/三类页面建议 |
| `20260804-blind-review-cursor-grok.md` | 批次不能等于主题；产品页和结构化读者入口；不要引入重框架 |
| `20260804-blind-review-claude-code-opus.md` | claim-id 回指替代逐字 Claim；三类页面、两态发布、人工门独立 |
| `20260806-okf-structure-research.md` | 官方 OKF v0.2 的 bundle、Concept、sources、generated/verified、生命周期和 Attested Computation 边界 |
| `20260806-task2-replan-okf-audit.md` | Task 1 控制面与读者产品的边界；Task 2-A/2-B/2-C 重排和 YAML/frontmatter 实现风险 |
| `20260806-3rd-review-routing-audit.md` | 默认 3rd-review 路由核对；历史 Opus/Cursor 调用与当前首层分离 |
| `20260806-3rd-review-prd-v1.5-final.md` | v1.5–v1.7 默认首层三方盲审；记录发布状态、topic key、样本门、oracle、parser 和最终实施前合同修正 |

### 3.3 历史调研的保留结论

`docs/research/` 中的以下历史文件在 Task 3-Closeout 前作为方法依据继续保留；归档后只改变路径，不改变内容和证据身份：

- `goinsight-loss-report.md`：硬编码截断会丢 FAQ、参数、错误码、Why、版本、视觉引用；归档不能是假来源。
- `sc-cb-analysis.md`、`sleep-curator-report.md`：可借鉴 claim 级验证、revise/merge、可恢复写回和产品/模块页面体系，但不照搬外部运行时。
- `ovmc-analysis.md`：完整链接聚类、阈值需按目标语料标定、不能默认引入重型依赖。
- `oss-knowledge-curation.md`：只借鉴增量 upsert、实体/关系和文件化治理，不引 GraphRAG、数据库或调度框架。
- `ov_find_maxstore_retrieval_report.md`：OpenViking 检索背景，不进入正式架构依赖。

OKF 的定位边界：它是可移植的文件格式和元数据约定，不是 KnowledgeDigest 的运行时、固定本体、服务端或质量评分器。本 PRD 目标采用“OKF v0.2-compatible publication profile”；若 Task 2-A 无法通过固定版本 parser smoke，必须降级命名为 `OKF-inspired profile`。两种 profile 都保留 KnowledgeDigest 的 `digest_*` 溯源和发布字段；不照搬 OKF 的 `Attested Computation` 运行时协议，不引入 OKF 之外的数据库或图服务。

## 4. 原始方案实现度和缺口

| 原方案部分 | 当前结论 | 本 PRD 的处理 |
|---|---|---|
| S1 采集、快照、内容指纹 | 基本成立，但父子页、表格、图片、双语归一不足 | Task 0 对账；Task 2-B 补结构归一化 |
| S2 聚类、complete-linkage | 有工程形态，但没有完整 F1–F7 和产品/模块语义 | Task 1 建 TopicIndex；批次不再生成主题 |
| S3 top-k 检索和 new/revise/merge | 代码存在，语义页面规划未真正实现 | Task 1 冻结主题计划；Task 2-B 实现编译上下文 |
| S4 Claim/faithfulness | 保留和验证较强，但正文仍是 Evidence 堆积；`old_target_body` 未真正参与 | Task 2-B 引入 Typed Page Compiler |
| S5 原子写、归档、fsync | 基本成立；来源索引和多文件发布事务仍有缺口 | Task 0 把 S6 和账本审计前置 |
| S6 provenance | Claim 可回指，但写回后审计、账本不闭合 | Task 0 统一 manifest/ledger，写前阻断 |
| 防丢失机制 | 主要覆盖“保存完整”，没有覆盖“读者能用” | 新增读者门和正文独立可答合同 |
| Task2 语义命名分类 | 解决了 slug、分类、分页的表面问题 | 作为历史基础，不能代替知识编译层 |

原始方案的根本遗漏：没有定义产品/模块/场景本体，没有定义页面类型，没有把原文编译为读者正文，没有注册真实读者问题，也没有区分“模型调用成功”和“知识质量发布成功”。

## 5. 产品目标、非目标和硬约束

### 5.1 目标

1. 在不丢来源、Claim、版本、表格、图片引用和历史的前提下，生成可阅读的产品/模块/问题页面。
2. 读者可以从 Home → 产品 → 模块/能力 → 页面进入，并在页面内直接得到主答案、边界、限制、版本和来源。
3. 主题身份与批次、输入顺序、单一来源 hash 解耦；增量运行只重编译受影响主题。
4. 已 `released` 的正式阅读目录只包含通过质量门的页级 `published` 页面；失败、冲突和低置信内容进入 `degraded` 档案，不伪装成正式知识。未完成 Task 3 读者验收的候选包不得覆盖上一次已 released 的目录。
5. 用固定读者问题、机器门、人工读者门和可重放 manifest 比较优化前后质量，而不是只比较页数或 Claim 数。
6. 方案完成后，维护者能从 `AGENTS.md`、`CONTEXT.md` 和根 `README.md` 三个入口分别知道怎么开发、字段是什么意思、如何运行和阅读结果；三者不能互相矛盾。
7. 项目只保留当前入口、有效设计、可追溯证据和必要验收材料；历史方案、旧任务报告和生成物安全归档，不把清理变成无证据删除。

### 5.2 非目标

- 不重写已经成立的 S1–S6 保存、安全、原子写、写前归档和 provenance 底线。
- 不引入数据库、图数据库、向量数据库、CAS、journal、调度器、后台守护或 AgentMemory 正式接入。
- 不复制 CompanyBrain 的全部文件数量、人工脚本和不确定模块体系。
- 不一次做八种页面、完整十维实体本体、永久 candidate 队列或没有处理人的人工工作流。
- 原始设计把人工复核列为非目标；本 PRD 新增的人工读者门只是 Task 3 的一次性发布验收，不是运行时队列、调度器或长期人工工作流。
- 不把 `AGENTS.md`、`CONTEXT.md`、根 `README.md` 混成一份文档：维护规则、术语契约和用户用法分别归位。
- 不为“保持干净”删除原始方案、ADR、验收证据、历史报告或仍被配置/测试引用的文件；清理必须先做引用扫描、分类和可恢复归档。
- 项目仓库清理与知识库输出中的 `_archive/` 保留规则是两个边界：前者清理工具现场和历史文档，后者必须保留来源/页面历史，不能混为一谈。
- 不以改文件名、改 Summary、加链接、压到 300 行等表面修补宣称完成。

### 5.3 硬约束

- 文件型 Markdown 知识库，人工触发，单写者。
- `--no-llm` 必须保证零 LLM、零 embedding 网络调用。
- 旧正式页面不得被失败运行静默覆盖；路径变更必须有旧路径到新路径映射。
- 原文不删除；移除和更新都先归档。
- 模型只能提出产品/模块候选，不能自动修改受管正式词典。
- 页级状态和交付级状态必须分开：页级只用 `published`/`degraded`，交付级只用 `released`/`not_released`。
- `machine_pass`、`agent_assisted`、`human_reviewed` 是独立证据字段，不能互相替代；Task 0–2-C 可以生成页级结果，但不能把整包标为 `released`。
- 主题 key、`claim_id`、词典版本、编译参数都必须可重算、可重放，不能依赖批次、输入顺序或单一来源 hash。
- 语义运行必须记录 provider、model、endpoint、embedding 维度、probe/calibration hash、超时、重放次数和调用预算；凭据只从环境变量读取，绝不写入日志、报告或知识库。
- 当前语义发布 profile 的示例 allowlist 沿用项目约定的 `qwen3.6`（`https://dashscope.in.whatspos.cn/v1`）和 `jina-embeddings`（`https://llm.paxszapp.com/v1`）；这不是架构身份。每次运行必须在 manifest 冻结实际 provider/model/endpoint；语义合同不变时可更换 provider，但必须重跑样本门并更新验收基线，不能把历史结果直接横比。
- 成功运行也不得静默覆盖人工修改：若正式托管页与上次生成 hash 不一致，必须标为冲突/`degraded`，保留旧页并要求显式处理。
- 方案完成后必须同步更新 `AGENTS.md`、`CONTEXT.md` 和根 `README.md`；README 是使用入口，AGENTS 是维护入口，CONTEXT 是术语/字段入口。
- 清理结果必须有 inventory、分类、引用扫描、归档清单和恢复路径；删除只允许针对可重建缓存或经确认无引用的临时产物。

## 6. 目标产品和架构

### 6.1 两个交付包

每次发布生成两个职责不同的包：

**Reader Package**：用户默认打开的知识产品，只包含 `README.md`、兼容入口 `Home.md`、唯一 canonical 的根 `index.md`、产品/模块索引、正式主题页和读者可见来源入口。不包含 `_digest`、`_archive`、provider 日志、模型原始响应和审计现场。

**Audit/Archive Package**：完整输入 manifest、快照、Claim、Evidence、原始文档、失败原因、归档快照、运行报告和模型/配置 hash，用于审计和恢复。

全量来源状态的唯一事实源是 audit manifest，例如 `_digest/source-manifest.json`；读者侧的 `references/` 和来源索引是它的投影。若为兼容保留 `_digest/source-index.md`，必须由同一 records 原子生成，不能维护第二份独立事实。`Home.md` 只负责把人带到根 `index.md`，不得维护第二套目录事实。

### 6.2 目标流水线

```text
S1–S6 Preservation
  ├─ source snapshot / claim / provenance / archive
  ├─ pre-write audit / ledger reconciliation
  └─ raw source archive
          ↓
Structure Normalizer
  └─ 父子页、标题、表格、FAQ、图片、双语、版本和噪声结构
          ↓
ProductGazetteer + TopicIndex
  └─ 产品/系统 → 模块/能力 → 对象/问题意图
          ↓
Typed Page Compiler
  └─ 三类正式页面；正文与 Evidence 分离；claim_id 回指
          ↓
OKF-compatible Concept/Bundle Writer
  └─ frontmatter、sources、generated/verified、lifecycle、index/log
          ↓
Publication Gate
  ├─ page published/degraded
  ├─ released reader package
  └─ not_released audit/candidate package
```

### 6.3 受管产品词典和主题索引

`ProductGazetteer` 是小而受管的词典。v1 至少记录：产品/系统 slug、模块 slug、别名、对象/功能名、置信度、匹配优先级、冲突原因、词典版本、owner 和变更说明。优先作为 `kb.structure.md` 的受管区段，或作为由该结构文件明确声明的词典文件；不得形成第二个未声明的事实源。

Task 1 首次建立词典时，必须用 89 篇输入的标题、H1、父子路径和其他确定性 metadata 生成 seed inventory，并记录 alias、冲突和待确认候选。模型只能提出候选，不能直接写正式词典；冻结运行中遇到未知产品/模块时，来源进入 `degraded`，同时在审计包中输出候选提案，不得静默扩展目录。匹配顺序、冲突规则和版本变更都要写入 manifest。

`TopicIndex` 保存稳定 topic key、产品、模块、对象/问题意图、来源成员、正式路径、旧路径映射和发布状态。

`digest_topic_id` 是 TopicIndex 的稳定托管身份：直接沿用 TopicIndex `topic_id` 字段；若旧库没有该字段，只能在一次显式迁移中由当前 `topic_key_v2` 的 canonical projection 生成并写入迁移映射。它不是输入顺序、page path、运行 hash 或 provider 输出；同一 TopicIndex 重放必须得到同一 `digest_topic_id`，旧 id 继续保留在 `old_path_mapping`/Audit 中。

主题 key 只有一个当前权威版本；旧 `topic_key_v1` 只作为历史迁移字段，不得被新编译器使用。当前权威 key 是 Task 1 已实际产出的版本化规范化元组：

```text
topic_key = topic_key_v2(normalize(knowledge_type,
                                   product_slug,
                                   module_slug,
                                   object_or_intent))
```

`knowledge_type` 是第一层身份；`products` 类型才继续使用 product/module/object-intent 轴。规范化规则必须固定并记录版本；key 不得使用 batch、输入顺序、来源集合 hash 或单一来源 hash。相同规范化 key 在同一知识库中必须只有一个主题；产品、模块或对象/问题意图缺失、冲突或无法规范化时，不能猜测合并，必须 `degraded` 并记录原因。第一次导入或显式 rebuild 才做全量 TopicPlan；普通 `digest(new_dir,kb_dir)` 只把新来源匹配到已有索引并局部重编译。任何旧 `topic_key_v1` 或三元组说明都只允许出现在迁移记录，不能作为实施依据。

非 `products` 类型不强行套用 product/module/object-intent；其 `topic_key_v2` 由 Task 1 已输出的类型内字段原样消费。Task 0/Task 1 exit manifest 必须列出 89 条来源的全部 `knowledge_type`，逐项标明正式映射或预期 `degraded`，不能把“当前语料都是 products”写成永久全库假设。

v1 Reader Package 只发布 `knowledge_type=products` 的三类正式 concept。其他类型即使在 inventory 中存在，也只进入 Audit/Archive 的 `degraded` 记录，不生成 Reader 路径、索引或 concept；要支持非产品类型，必须先做新的 PRD scope revision，补齐其目录和页面合同。

主目录轴固定为：

```text
产品/系统 → 模块/能力 → 页面
```

客户、研发、运营等领域只做 facet。没有可靠产品/模块归属的来源只能 `degraded`，不能进入正式主题目录。

原始方案中的 F1–F7 相似度规则在 v1 不重建为新的规则引擎。`TopicIndex` 是正式身份和合并依据；相似度只用于候选检索。若保留阈值，必须用固定语料和 calibration artifact 标定，不能凭一对空的相似分数自动生成正式主题。

### 6.4 v1 正式页面类型

v1 只支持三类正式页面：

| 类型 | 必须回答的问题 | 必需内容 |
|---|---|---|
| `product_overview` | 这是什么、适合什么、不适合什么 | 定位、适用场景、能力边界、入口、来源 |
| `module_or_capability` | 这个模块解决什么、如何进入、和谁关联 | 目的、能力、入口/前置、关系、限制、版本、来源 |
| `procedure_or_rule` | 具体怎么做、规则是什么、出错怎么办 | 前置、步骤/规则、异常、限制、版本、来源 |

案例、技术部署、版本历史、经验等内容先归入这三类中；只有真实样本证明需要稳定独立合同，才另开页面类型。原始文档档案不是正式页面类型。

主题内容超过单页上限时，先按产品、模块、能力、步骤或问题边界拆成多个正式页，再做行数分页；不能把一个主题硬切成读者无法理解的 `part-1` 主入口。每个页的正文最多 120 行，整页（含来源和引用）最多 300 行；同一主题族使用稳定的相关 key、总览页和 `prev/next` 导航，旧 part 不静默删除，当前导航只指向仍有效的页。每个有效 Claim 必须且只能进入一个正式 part，拆分后仍可从总览找到主题全貌。

`product_overview` 只有在存在真实子主题，且至少有可解析的定位、适用场景和边界证据时才生成；`module_or_capability` 只有在存在真实能力证据和入口/关系证据时才生成。证据不足时只生成索引记录和审计缺失项，不生成空壳页。

### 6.5 正文和证据的关系

Reader page 的正文必须是按页面类型编译的可读内容。Evidence/archive 保存完整 Claim、原文、表格、图片 URL、行定位和来源历史。

正文段落使用 `claim_id`、来源链接和必要定位回指，不要求 Claim 原文逐字出现在正文。`claim_id` 必须稳定且全局唯一，建议 v1 规范化后计算：

```text
claim_id = sha256(canonical(source_uri + content_fingerprint + fragment_locator))
```

正文中的每个引用都必须能解析到 source URI、内容 hash 和 locator；跨重跑保持稳定。忠实性通过 claim-id 可解析、数字/标识符/版本校验、固定 seed 的抽样蕴含和人工核验完成。抽样要记录样本数、seed、阈值和失败项。正文可以包含命令、步骤、表格解释和必要的原文短引，但不能把整段 Evidence 或无解释的原始表格连续复制成正文；复制比例只作按页面类型的诊断指标，不作全局硬阈值。继续使用“Claim 原文必须逐字包含在正文”的规则，会再次得到 Evidence dump。

必需 section 缺少证据时，页级状态必须是 `degraded`；可选 section 可以省略。正式正文不写“请阅读 Evidence”“来源未说明”“原始资料未载”“暂无已验证内容”等通用占位句，缺失原因只写在状态和审计记录中。

### 6.6 对外状态

页级和交付级状态分开：

- 页级 `published`：该页通过机器门，允许进入候选 Reader Package；页级 `degraded`：来源失败、冲突、无归属、缺必需证据、人工修改冲突或质量门失败，不进入正式导航。
- 交付级 `released`：本次 Reader Package 通过机器门、固定读者题集和一次性人工读者门，并完成可重放交付；`not_released`：任一交付门未通过，Reader Package 不得覆盖上一次已 released 的包。

Task 0–2-C 只能生成页级状态和 `not_released` 交付包。Task 3 才能在机器、读者和交付门全部通过后把整包标为 `released`。`machine_pass`、`agent_assisted`、`human_reviewed` 仍分别记录，不得把 agent 输出当作人工验收。

`draft` 可以是内部瞬时状态；不把没有处理人的永久 `candidate` 当成完成态。

本 PRD 的 Task 3 只定义首次 89 条全量发布。后续 `digest(new_dir,kb_dir)` 的增量运行必须对 affected set 重新执行机器门、读者题集和交付门后才能更新已 released 包；不得以“只改了局部页”为由绕过门禁。增量门的性能优化另立任务，不在本 PRD 临时发明第二套发布流程。

增量运行的读者门选择规则固定为：affected topic 的全部正向题 + 固定 sentinel 正向题 2 个 + 全部 3 个负向题；若 taxonomy、page type、模板、Concept Contract、题集或 release manifest 变化，或 affected topic 超过全库 20%，必须重跑完整 17+3 题集。该规则只减少不受影响的重复人工工作，不降低机器门、来源归因、失败隔离或发布状态门。

### 6.7 方案完成后的文档和仓库合同

方案全部实现后必须形成三份互补的长期入口：

- `AGENTS.md`：项目目标、真实文件结构、职责边界、开发规则、测试命令、质量门、发布状态、文档维护规则和禁止事项。它面向后续编码代理和维护者。
- `CONTEXT.md`：Claim、source snapshot、topic key、`claim_id`、ProductGazetteer、TopicIndex、page type、Reader/Audit Package、`published/degraded/released/not_released` 等术语和字段的唯一解释。它面向需要理解数据合同的人。
- 根 `README.md`：安装/环境、输入目录格式、离线和语义运行命令、批次恢复、结果阅读顺序、Reader/Audit 包区别、失败排查、凭据安全和项目结构。它面向第一次使用本项目的人；它与每个结果目录中的 Reader Package `README.md` 不同，后者只解释单次结果。

三份文档必须指向同一份实际命令和路径；任何 CLI、正式输出、状态、目录或质量门变化，都要同步更新文档和 acceptance 测试。README 不复制完整设计，AGENTS 不承担用户教程，CONTEXT 不承担运行步骤。

Task 3-Closeout 还要对全仓库做一次“保留、归档、删除、待确认”盘点：

- 保留原始方案、ADR、有效 acceptance fixture、`evidence/phase4`、仍被配置/脚本引用的校准和验收证据；
- 将已完成任务的 spec/plan/tasks/decision log、旧任务状态和已结束报告归入对应 `specs/archive/` 或 `docs/reports/archive/`，保留索引和来源 hash；
- 将 21 份本次研究和盲审材料在任务完成后归入带日期的研究归档目录，PRD 保留主结论和证据索引；
- 对 `.DS_Store`、`__pycache__`、`.pytest_cache`、`.venv`、`.opencode/node_modules`、`.agent_context`、`.omc`、`.multica`、`.worker-mode` 等生成物逐项确认是否有活跃任务或 Git 跟踪后再清理；补齐 `.gitignore` 中的缓存/本地环境规则；不得用宽泛递归删除；
- 根目录只保留当前用户入口和项目状态索引；`BLOCKED.md`、`PROGRESS.md` 等旧任务状态必须迁移、重命名为历史报告，或明确标注当前有效性。

清理后的仓库必须能通过“文档链接、配置引用、脚本引用、测试引用、Git 跟踪状态和目录 allowlist”检查；任何仍被引用的文件不得被删除，任何被归档的文件必须有新路径映射。

### 6.8 OKF-compatible Reader Bundle

Task 2-A 负责把 Reader Package 从“KnowledgeDigest 私有页面目录”升级为可被人、Agent 和普通 Markdown 工具直接消费的 OKF-compatible bundle。它不是把 `_digest`、`_archive` 或内部账本暴露给读者，也不是要求整个项目实现完整 OKF runtime。

Reader Bundle 的正式布局：

```text
reader-package/
├── README.md                 # 本次结果说明，不是项目根 README
├── Home.md                   # 兼容入口，只指向根 index.md
├── index.md                  # bundle 根入口，唯一 canonical 渐进式目录
├── log.md                    # 本次发布变更摘要
├── products/
│   ├── index.md
│   └── <product>/
│       ├── index.md
│       ├── overview.md
│       ├── <concept>.md       # 有 product 但无 module 的正式 concept
│       └── modules/
│           ├── index.md
│           └── <module>/
│               ├── index.md
│               └── <concept>.md
└── references/
    └── sources.md            # 必选的轻量来源投影，不放完整审计快照
```

`Home.md`、Reader `README.md` 和 `references/sources.md` 是本 profile 明确声明的入口/索引豁免文件，不是 concept，不放 concept frontmatter；validator 必须硬编码这份豁免清单。`Home.md` 只能指向根 `index.md`，Reader `README.md` 只说明本次结果，`references/sources.md` 只由同一 audit records 投影生成，三者都不能维护第二套目录事实。只有 parser smoke 通过并且 bundle 宣称 `OKF-compatible` 时，根 `index.md` 才能声明 `okf_version: "0.2"`；降级为 `OKF-inspired profile` 时必须省略该字段。嵌套 `index.md` 和 `log.md` 不放 frontmatter。`index.md` 和 `log.md` 是 OKF 保留文件名，不能被当成普通 concept 页。产品、模块和正式主题页都是 concept Markdown 文件；每个 concept 的 frontmatter 至少有 `type`，并按需使用 `title`、`description`、`tags`、`sources`、`generated`、`verified`、`status`、`stale_after`。未知扩展字段必须保留，不能因不认识而丢弃。无 module 归属但有明确 product 归属的 concept 直接放在 `products/<product>/`，不得臆造 module；无 product 归属或冲突时进入 `degraded`，不进正式导航。`modules/index.md` 只有在该产品至少有一个已发布 module concept 时才生成；只有产品级 concept 时不生成空的 `modules/` 目录或索引。

标题和描述不能由 provider 自由发挥：标题按“既有托管标题 → 来源 frontmatter/显式 metadata title → 可解析 H1 → 可读文件名”的顺序选择，并做固定空白、标点和 slug 归一；没有可读候选时页级 `degraded`。描述按“来源显式 description/summary → 确定性抽取的首个有意义句子”选择，不得写泛化占位语；目录索引只能投影 concept 的描述。由 ProductGazetteer/TopicIndex 直接产生的产品、模块和类型标签属于 metadata，不需要伪造正文事实归因；由来源事实生成的描述和标题补充句仍必须绑定 claim/source。

`degraded` 不属于 Reader Package 的导航树。候选包、样本包和失败运行的降级页统一写入对应 Audit/Archive 的 `_digest/degraded/<digest_topic_id>.md`（或同一目录下明确的 `source-<id>.md`），并在 manifest 记录原因、输入指纹和恢复路径；Reader Package 不生成 degraded concept、degraded index 条目或隐藏入口。只有页级 `published` 才能进入 Reader 导航。

KnowledgeDigest 自己的扩展字段统一使用 `digest_` 前缀，例如：

以下是最终 concept 的字段形状；Task 2-A/2-B/2-C 生成的样本包无论页级是否 `published`，包级 manifest 都必须是 `not_released`。`digest_release_status` 是包级字段，不写入 concept 页，避免 Task 3 在质量门之后变更页面字节。

```yaml
type: "KnowledgeDigest Procedure or Rule"
title: "配置设备告警规则"
description: "说明告警规则的前置条件、配置步骤和异常处理。"
tags: [product:goinsight, module:device, kind:procedure]
generated: {by: "knowledge_digest/1.x", at: "2026-08-06T00:00:00Z"}
verified: []
digest_machine_pass: []
status: stable
sources:
  - id: "src-<stable-source-fragment-id>"
    resource: "<source-uri>"
    title: "<source-title>"
    digest_content_fingerprint: "sha256:<content-hash>"
    digest_claims:
      - claim_id: "<stable-claim-id>"
        fragment_locator: "line:42-48"
digest_topic_key: "v2/<knowledge_type>/<product>/<module>/<object_intent>"
digest_topic_id: "<stable-topic-id>"
digest_page_type: "procedure_or_rule"
digest_page_status: published
digest_content_hash: "<sha256>"
---
```

五条 OKF 信号在本项目中的映射：

1. `sources` 记录来源 URI、标题、内容指纹、可用的 author/last_modified，以及逐 Claim 的 `digest_claims[].fragment_locator`；`sources[].id` 是稳定的 source-fragment key，每条正文归因必须只解析到一个 `claim_id + fragment_locator` 对，不复制完整原文，不生成不可比较的 credibility score。
2. `generated` 记录编译器/模型和正文生成时间；`verified` 只记录真实的来源/内容回查或独立人工核验。结构 lint 和机器发布门进入 `digest_machine_pass`/audit，不得用泛化的 `process:knowledge-digest-machine-gates` 自证内容。`agent_assisted` 不能写成 `human:` actor。
3. `status` 只表达 concept 生命周期：`stable`、`draft`、`deprecated`；KnowledgeDigest 的页级 `published/degraded` 和包级 `released/not_released` 继续放在 `digest_*` 字段，避免混义。
4. `stale_after` 只在来源明确提供可审计的有效期/复核日期时写入；没有证据就省略，不猜 TTL。过期不自动删除，读者过滤和审计报告分别处理。
5. OKF 的 `Attested Computation` 暂不进入 Task 2-A/2-B/2-C；KnowledgeDigest 的 provider、claim、写回和报告仍由 `_digest` audit manifest 记录。

TopicIndex 的 `knowledge_type` 到页面合同的映射必须是固定表，不允许按页面标题临时猜测：

| `knowledge_type`/证据 | `digest_page_type` | OKF `type` |
|---|---|---|
| `products` + 产品定位/边界 | `product_overview` | `KnowledgeDigest Product Overview` |
| `products` + 模块/能力/入口 | `module_or_capability` | `KnowledgeDigest Module or Capability` |
| `products` + 步骤/规则/异常 | `procedure_or_rule` | `KnowledgeDigest Procedure or Rule` |
| 非 `products`、未注册类型、无证据或冲突 | 不生成正式页 | `degraded`，仅进 Audit |

正文采用结构化 Markdown：页面类型对应的 `# Definition`、`# Scope`、`# Steps`、`# Limits`、`# Version` 等实际章节按证据生成；每个关键事实用标准 Markdown footnote（如 `[^src-abc]`）指向**同一页面 frontmatter 的** `sources[].id`。validator 只按页内 source-id 解析连通性，并检查每个归因最终只落到一个 `digest_claims[].claim_id` 和 locator；`references/sources.md` 是阅读投影，不是脚注的第二目标，也不维护另一套 source id。`claim_id` 继续是审计 Claim 身份；同一来源可有多个 source-fragment entry，但不复制正文。正文不再依赖页面底部孤立的 Evidence 列表。

目录索引只做渐进式披露：每个 `index.md` 列出真实子目录/概念的可读标题和一行 description，不生成空分类、不把 hash 作为标题、不把所有正文塞进索引。概念之间的标准 Markdown links 表达相关、前置、替代或依赖关系；关系类型写在链接附近的自然语言中，不能凭相似度臆造。

### 6.9 实施前合同修正（v1.7）

以下决定在 Task 2-A 开始前冻结，不允许由实现者临时解释：

1. **Concept Contract 生命周期**：Task 2-A 产出 `v1-draft`；Task 2-B 只允许一次有记录的正文/section 修订；Task 2-C 通过后冻结为 `v1`；Task 3 只能复用 `v1`。改变 section 集合、模板、必需/可选字段或页面类型映射都算 contract revision，计入这一次额度；只修复违反既有合同的行为 bug 才算 defect fix，不占额度。
2. **Topic key 版本**：沿用 Task 1 已实际产出的 `v2/<knowledge_type>/<product>/<module>/<object_intent>`。`knowledge_type` 是 TopicIndex 注册维度，不直接等同于 OKF `type`；必须在 compiler 中维护确定性映射，未映射即 `degraded`。
3. **单一入口事实源**：`index.md` 是 canonical navigation；`Home.md`、Reader `README.md`、`references/sources.md` 只能是明确的 profile projection/豁免文件，不能有第二套导航或来源事实。
4. **状态和 hash**：包级 `digest_release_status` 只存在于 manifest，是唯一权威；concept 页不写该字段。`digest_content_hash` 只覆盖受管 frontmatter 的业务字段（`type/title/description/tags/sources/status/stale_after/digest_topic_key/digest_topic_id/digest_page_type`）与正文；明确排除 `digest_content_hash` 自身、`generated.at`、`verified`、`digest_machine_pass`、`digest_page_status`、包级 release manifest 和 audit/runtime 字段。YAML key 顺序、Unicode、缩进、折行参数必须固定。
5. **机器与人工信号**：`digest_machine_pass`/audit 记录结构和发布机器门；`verified` 记录真实内容/来源核验；`human:<id>` 必须能回查人工记录。没有对应证据，禁止产生 `machine-confirmed` 或 `human-reviewed`。
6. **读者门归属**：Task 2-B 只做机器诊断和语义编译；Task 2-C 是唯一小语料人工读者门。题集派生规则、抽样 seed 和最低阈值在 Task 2-C 启动前冻结，exit manifest 只能记录结果，不能事后降低门槛。
7. **互操作声明**：Task 2-A 必须跑零网络的最小外部 OKF parser smoke；若无法提供固定版本的消费者验证，对外名称改为 `OKF-inspired profile`，不宣称兼容。
8. **OKF parser 可重放性**：Task 2-A exit manifest 必须记录 parser 的来源、固定版本或 commit、fixture bundle hash、允许的未知扩展/类型行为和预期结果。没有可固定的消费者版本时，必须在实现前把所有对外文字和字段命名降级为 `OKF-inspired profile`，不能在 Task 3 才临时决定。
9. **读者样本不可缩小**：Task 2-C 的 answerable 子集由 Task 0 冻结的来源标签和确定性规则派生，不由编译器或评审人临时挑选；最少 8 个正向问题，且覆盖至少 2 个产品/模块、2 类页面类型。Task 1 inventory 中存在的长文、表格/图片、双语、多源、失败/degraded 类别必须各自进入正向样本，或有单独的 machine fixture 和排除理由；不能以“样本中碰巧没有”为理由忽略。若可答正题不足 8 个，Task 2-C 直接 `not_released`，不能降低数量门槛；3 个负向问题必须全部保留。
10. **质量 oracle 可计算**：必需 section 的事实断言归因覆盖率必须为 100%；断言提取器必须是确定性规则，或使用固定 model、temperature、seed 并记录其 manifest。命令、端口、配置键、关键表格行和图片引用的规范化集合不得丢失或改变；连续逐字来源块最多 3 个句子或 240 个字符（代码块、表格、双语配对、公共模板段落和带 attribution 的短引除外）；同页 section 的 5-gram Jaccard ≥0.92 且正文长度超过 80 字符时视为近重复并阻断，公共模板、代码、表格和双语配对按 fixture 规则排除；golden-negative fixture 必须稳定失败并保持 `degraded/not_released`。每项记录分母、检测器版本、seed 和失败样本。
11. **verified 事件白名单**：机器 `verified` 只允许来自 `source_hash_match`、`locator_resolved`、`critical_token_recheck`、`sampled_entailment` 四类事件；actor 固定为 `process:knowledge-digest-<event>-<detector_version>`，工具事件使用 `<producer>/<version>`，均必须引用输入 fingerprint、检测器版本和审计记录。结构 lint、provider 成功、写回成功、agent 辅助都不能产生 `verified` 或 `human:` actor。
12. **验证失效**：任何受管正文、frontmatter 内容、sources/claims、分页归属或 page type 变化都使旧 `verified` 事件失效；旧事件只留在 Audit 历史，Reader 当前信号不再使用。仅追加不改变内容的审计记录不使内容 hash 变化，但不能恢复已失效的验证。
13. **Task 2-C 失败的受控修复**：失败后只允许以 defect record 重开 Task 2-A 的 profile/validator 或 Task 2-B 的 normalizer/compiler；必须更新受影响 fixture 并重跑受影响门。契约字段/模板/页面类型变化必须消耗唯一一次 contract revision；纯行为 bug 不得借 defect loop 偷改契约。禁止新增页面类型、词典轴、provider、降低题集阈值或改写历史 evidence；再次失败仍保持 `not_released`，直到新的 PRD scope revision 获得批准。
14. **版本 oracle**：固定为既有托管 metadata → 来源 frontmatter/显式 metadata → 明确的版本标题/字段；仅接受 semver、日期版本或来源明确的 release label。多个不一致版本、版本字段无法解析时页级 `degraded`；`product_overview` 可在来源确实没有版本信息时省略，`module_or_capability` 与 `procedure_or_rule` 若来源声明版本相关行为则必须有可回查版本证据；`stale_after` 只能由来源明确的有效期/复核日期产生。
15. **fallback 边界**：Jaccard 可作为显式离线基线，也可按既有合同作为语义模式的整次 fallback；fallback 结果可验证结构和保存完整性，但不能满足 Task 2-B 的 semantic exit，也不能把语义交付包标为 `released`。同一次运行不得混用 Jaccard 与 embedding 分数。

## 7. 任务路线图

### Task 0：诚实化与交付包

#### 背景

当前运行把 provider 成功、Claim 验证、写回成功和知识质量混成一个“成功”。失败来源可以进入导航，pending 入口可能是空壳，source-index、snapshot、batch 账本不一致，279MB 审计现场也混在默认阅读目录。继续做语义编译会把错误放大。

#### 参考

- 原始设计 S5/S6 和“失败即报错、归档不删除”原则；
- `20260804-output-audit.md`、`20260804-output-navigation.md`、`20260804-output-provenance-integrity.md`；
- 三方盲审报告中的 ledger closure、S6 pre-write、package split 建议。

#### 调研结论

- source-index 88 行 vs batch/snapshot 89 个来源；
- 31 个失败或 needs-review 来源没有被严格隔离；
- 90 个 written 报告中 quality 为空；
- duplicates 和 claim-history 存在重复；
- S6 在 writeback 后，来源索引在事务外覆盖；
- 读者包包含 `_digest`、`_archive` 和 provider 现场。

#### 方案

1. 建立唯一 `input manifest → source snapshots → audit ledger` 对账链；published index 只是投影，不是第二事实源。
2. 将 S6 provenance 和账本/交付包门移到写回前；Task 0 只检查 Claim、来源、路径、状态和交付包事实，不承担正文语义质量，正文质量由 Task 2-B/2-C/3 检查。
3. 分开记录 provider transport、claim verification、writeback、`machine_pass`、`agent_assisted`、`human_reviewed` 和最终发布状态。
4. 失败、JSON 破损、无正文、无产品归属的来源只生成 `degraded` 档案，不进正式导航；无关的已发布页不被整库回滚。显式 `--no-llm + Jaccard` 是合法离线基线；语义模式的 embedding 探测失败可以按既有合同整次回退 Jaccard，但必须在 manifest/status 显示 fallback，若本次要求语义发布则整包为 `not_released`，不得伪装成 embedding 成功。
5. Reader Package 和 Audit/Archive Package 使用 allowlist 生成；Home pending 只指向真实非空队列；空分类、断链和不可点击来源入口直接失败。
6. duplicates、claim-history、批次重跑必须幂等；重复运行不能产生重复来源关系或重复页面。
7. 冻结并落盘 v1 读者题集：17 个正向问题和 3 个负向问题的原文、入口、期望主题/产品、覆盖角色、负向设计原则、抽样 seed、评审人和题集 hash。Task 0 同时校验 12–20 篇代表样本至少能回答 8 个正向问题、至少包含 6 个预期可通过机器门的 source/concept 候选，并覆盖至少 2 个产品/模块和 2 类页面类型；三类 page type 都必须有真实候选，或在 Task 0 manifest 中登记对应 machine fixture。否则必须调整样本清单或把 Task 2-C 预置为 `not_released`，不能把不足的样本带入后续任务。Task 2-B/2-C 只能使用其中可由样本回答的派生子集，Task 3 使用完整题集。
8. 报告同一 snapshot/claim/duplicate 的重复运行和归档增长；只把异常增长作为监控与失败信号，不预设全局文件体积阈值。

#### 交付物和涉及范围

- 账本/状态/事务代码：`src/knowledge_digest/provenance.py`、`writeback.py`、`pipeline.py`、`batch_run.py`、`navigation.py`（按现有职责最小改动）；
- reader/audit 包生成器和 README；
- acceptance 测试：来源集合对账、写前失败、重复重跑、失败页隔离、包 allowlist、导航无空入口。

#### 依赖和不做什么

- 依赖：现有 S1–S6；
- 不做产品词典、页面正文编译和全量重新发布；
- 回滚：只回滚 Task 0 代码，保留原输出和审计证据，不删除基线。

#### 验收标准

1. `input_manifest`、snapshot、audit ledger 三者来源集合一致；缺失来源显式失败，不静默省略。
2. 同一批次重跑后 source/claim/duplicate/history 关系幂等，统计可重复。
3. S6、路径、Claim、状态和交付包事实在写回前通过；写前失败不会产生新的 formal 页面。
4. 页级 `published/degraded` 与交付级 `released/not_released` 可独立验证；`written` 不等价于任一发布状态，Task 0 不能把整包标为 `released`。
5. Reader Package 不含 `_digest`、`_archive`、provider 日志和运行比较报告；审计包可定位全部来源和失败原因。
6. Home、分类、来源入口无空页、断链和不可点击链接；pending 只在真实有待处理项时出现。
7. 旧 formal 页面未被失败运行覆盖；归档可恢复。
8. 读者题集 manifest 可重放，包含 17+3 题、2-B/2-C 派生样本规则和 hash；代表样本覆盖门已通过；89 条来源的 `knowledge_type` inventory 已逐项记录；`--no-llm` 运行网络调用数为 0。
9. 同一 snapshot 的重复运行不会产生异常 archive/duplicate 增长；异常可在 audit report 中定位。

### Task 1：产品、模块和稳定主题主轴

#### 背景

历史 Task2 的 `batch_size=1` 产生了 86 个主题，其中 85 个是单来源主题；`product_slug=0`，不同产品的 AE、iOS、GoInsight 等对象没有稳定的产品语义归属。批次和来源被错误地当成了主题边界。Task 1 已经修复稳定身份和 TopicPlan，但不负责正文发布。

#### 参考

- 原始设计 S2/S3、`20260804-design-s1-s3.md`；
- `20260804-companybrain-ia.md`、`20260804-companybrain-reader-journey.md`；
- 三方盲审的 ProductGazetteer、TopicIndex、batch invariance 和增量建议。

#### 调研结论

- 当前相似度和 complete-linkage 不能代替产品/模块/问题规划；
- CompanyBrain 的可读性首先来自产品→模块→场景/页面主轴；
- 全量规划与日常增量的身份规则没有写清；
- “单来源”不能自动等于错误，也不能自动等于正式高置信主题；需要看资料是否为完整独立手册、归属是否清楚、是否有冲突。

#### 方案

1. 在现有文件型 KB 约定内建立受管 `ProductGazetteer`，以产品/系统、模块、别名、对象、匹配优先级、owner、版本和冲突原因为最小字段；先用 89 篇来源的标题/H1/父子路径生成确定性 seed inventory。
2. 建立 `TopicIndex`，记录稳定 topic key、成员来源、产品、模块、对象/问题意图、路径、旧路径映射和状态。正式词典由结构文件声明；模型只能产生候选提案，未知项不能静默进入正式目录。
3. 先决定 TopicPlan，再调用 provider；批次只是传输边界。`batch_size=1` 和 `batch_size=20` 必须得到相同的主题集合和正式路径，正文可以因 provider 批次不同而不同。topic key 使用版本化规范化 tuple，不依赖 batch、输入顺序或来源 hash。
4. 规则固定为：同产品同对象/问题可合并；不同产品同名对象必须分开；产品或模块冲突进入 `degraded`；独立完整手册可单源发布，但单源比例只做监控，不作全局硬门。
5. 初次导入或显式 rebuild 才做全量 TopicPlan；正常增量只匹配已有索引并重编译受影响主题。正式路径稳定，改名必须生成旧路径映射。
6. 产品/模块是主目录轴；客户、研发、运营等是 facet；不生成空模块和空分类。没有足够真实实例或必需定位/边界证据时，只生成索引记录和缺失审计，不生成空壳 overview 页。
7. 定义 affected set：匹配主题、相关链接主题、受影响的产品/模块索引和 Home 统计；集合外页面正文和路径必须字节不变。路径变更必须有可点击 redirect/alias 或旧链接映射测试。
8. v1 关系类型只允许 `belongs_to`、`prerequisite`、`related_capability`、`procedure_for`、`supersedes`、`source_co_reference`；关系必须有来源证据，规定是否双向，以及关系新增/删除触发目标正文重编译、索引更新还是仅 Audit 修复。相关链接的 affected set 必须按此规则可重放。
9. 正式托管页保存 `last_published_hash`/`managed_content_hash`；发现页被人工改过时不静默覆盖，标记冲突并保留旧页，修复必须通过词典、来源或显式 override。

#### 交付物和涉及范围

- 扩展 `identity.py`、`kb_structure.py`、`page_layout.py` 或等价现有职责模块；
- 受管产品/模块词典和 TopicIndex 的文件格式及版本；
- 89 篇输入的结构特征 inventory（父子页、表格、FAQ、图片、双语、版本和噪声），作为归一化范围依据；
- 89 条来源完整 `knowledge_type` registry、每种类型的正式映射或预期 `degraded` 清单；
- 稳定路径、旧路径映射和批次不变性测试；
- 12–20 篇代表性样本的 TopicPlan fixture。

#### 依赖和不做什么

- 依赖：Task 0 的账本和失败状态；
- 不引入数据库、图谱、向量索引、通用 repository/service 层；
- 不一次建立十维实体本体，不让模型自动修改正式产品词典；
- 回滚：TopicIndex 是可重建投影，原始快照和旧 formal 页面不删除。

#### 验收标准

1. 同一输入分别以 batch size 1 和 20 运行，TopicIndex 成员、topic key、`digest_topic_id` 和正式路径一致。
2. TopicIndex 中产品、模块、对象/问题意图和规范化 key 不为空；无产品归属或冲突的来源为 `degraded`。正式 page type 和必需 section 在 Task 2-B/2-C/3 验收，不由 Task 1 提前伪造。
3. 主入口不使用 `topic-<hash>`、裸 `1.md`、`ae.md`、`ios.md` 等不可读路径；注册别名必须有词典记录。
4. 同产品同对象能进入同一主题计划，不同产品同名对象不会误合并。
5. 普通增量只重编译 affected set；集合外旧 formal 页面正文和路径字节不变，允许 Home/索引中明确列出的受影响计数和相关链接变化。
6. 不生成空分类、空模块或没有真实实例的目录。
7. 单源主题可以发布的前提是资料完整、产品/模块明确、结构有意义、必需证据存在且无事实冲突；单源比例作为报告监控项，不作为硬门。
8. 同一 topic key 在不同 batch size、输入顺序和重复运行中只有一个主题；旧路径映射可达，人工修改冲突不会被静默覆盖。

### Task 2-A：OKF-compatible Reader Bundle 基础

#### 背景

Task 1 已经能生成 `_digest/source-inventory.jsonl`、`topic-plan.json`、`topic-index.json` 和运行报告，但这些是编译控制面，不是读者知识产品。若直接进入 LLM 正文编译，仍会得到一批私有路径、重复 frontmatter、孤立索引和无法过滤信任/新鲜度的 Markdown。OKF v0.2 提供了一个更合适的文件层：Markdown + YAML frontmatter、渐进式 `index.md`、标准来源字段、生成/验证事件、生命周期和标准链接；OKF 的 `log.md` 可选，但本项目 profile 明确要求根 `log.md`，嵌套目录不生成。

Task 2-A 开始前必须先做一次入口验收：读取 Task 0/Task 1 的 exit manifest，核对冻结题集 manifest（17+3 题及 hash）、12–20 篇样本覆盖记录、answerability 派生规则、89 条来源的完整 `knowledge_type` inventory，以及 TopicIndex/ProductGazetteer 的版本和 hash。验收报告必须把实际文件相对路径、内容 hash 和生成 commit 写入 Task 2-A manifest；任何缺失、过期或 hash 不一致都先生成 backfill manifest 并保持 `not_released`，不得进入 Task 2-B。补齐后必须重新跑受影响的 Task 0/Task 1 机器门；不能把“代码存在”当成 exit artifact 已验证。

入口验收的 manifest base 必须显式声明为 `repo_root` 或 `bundle_root`，所有路径只能相对该 base；题集同时记录 JSON 文件 bytes 的 `file_sha256` 和规范内容的 `question_set_hash`。历史 receipt 与重新计算的 backfill 必须区分 `provenance_mode`，后者不能冒充原始退出凭证。逐项检查至少记录 `available`、`stale`、`hash_match`、`generated_by_commit`、实际命令和 `exit_code`；还要记录当前 `HEAD`/tree 身份、输入 source manifest/hash、Task0/Task1 状态、缺失项和回填动作。任何一项缺失，入口状态保持 `not_released`，正文编译命令必须被拒绝。

当前入口 backfill 证据固定保存在 `quality/evidence/task2-entry/`：`knowledge-publication-task2-entry-backfill.v1.json` 是总门禁，`task0-real-corpus-20260806.json` 和 `task1-real-corpus-20260806/` 是重算的 Task0/Task1 证据，`task2-entry-sample-coverage.v1.json` 是结构样本与来源证据预检。Task 2-A 入口只验证样本存在、来源证据可追溯和 answerability 派生规则已冻结，不把 TopicPlan examples 当作读者质量通过；逐题 `answerable`、source/topic/page-type/locator、section 完整性和人工读者门由 Task 2-B/2-C 完成。

#### 参考

- [OKF v0.2 SPEC.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)；
- [OKF v0.2 README](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/README.md)；
- [Google Cloud OKF v0.2 trust signals](https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals)；
- Task 1 的 `topic_axis.py`、TopicIndex、ProductGazetteer 和本 PRD §6.8。

#### 调研结论

- OKF 的核心不是固定本体，而是让每个 concept 能被人和 Agent 直接读取、被索引、被 diff，并在 frontmatter 中查询来源、生产者、验证者和生命周期。
- OKF v0.2 的 `type` 是唯一必需字段；`sources`、`generated`、`verified`、`status`、`stale_after` 都是可选但有语义的信号；格式记录信号，不写不可移植的信任总分。
- `index.md` 支持 progressive disclosure，标准 Markdown links 表达关系；`index.md`/`log.md` 是保留文件名，不能再被当成普通知识页。
- OKF 不规定固定 taxonomy、数据库、服务端或完整 attestation runtime；KnowledgeDigest 只采用格式层，不照搬外部运行时。

#### 方案

1. 定义 `KnowledgeDigest OKF v0.2-compatible profile`：Reader Package 使用 `README.md → index.md → products/<product>/...`，旧 `Home.md` 只保留短兼容入口；每个目录的 `index.md` 只列真实子项和 description，`log.md` 记录发布变更摘要。`README.md`、`Home.md`、`references/sources.md` 的非 concept 身份写入 profile 豁免清单并由 validator 强制校验。
2. KnowledgeDigest writer 固定三类正式 concept `type`：`KnowledgeDigest Product Overview`、`KnowledgeDigest Module or Capability`、`KnowledgeDigest Procedure or Rule`。validator 对外部 OKF bundle 的未知 type 只做兼容读取并保留，不把 OKF 的开放 type 规则误写成项目正式页可随意扩展。concept 页只保留 `digest_topic_key`、`digest_topic_id`、`digest_page_type`、`digest_page_status`、`digest_machine_pass` 等 `digest_*` 扩展字段；包级 `digest_release_status` 只在 manifest 中存在；产品级无 module concept 直接放 product 层，只有真实 module concept 才生成 `modules/index.md`。
3. 设计 frontmatter contract：`type/title/description/tags` 用于发现和阅读；`sources`、`generated`、`verified`、`status`、`stale_after` 用于来源、生产、验证和生命周期；未知扩展字段 round-trip 保留。由于现有项目只有 YAML-like 简单解析，Task 2-A 必须采用固定版本的安全 YAML 解析/序列化依赖 `PyYAML`，只使用 `safe_load/safe_dump`，禁止继续用手写行解析伪装嵌套 OKF frontmatter。
4. 将稳定 `claim_id` 作为 audit identity、稳定 `sources[].id` 作为正文 attribution key：fixture 正文用标准 Markdown footnote 引用 `sources[].id`，source entry 保存 source URI、content fingerprint 和逐 Claim 的 `digest_claims[].fragment_locator`；真实语义正文归 Task 2-B；完整 Claim/Evidence 继续留在 Audit Package。
5. 明确状态映射：`status` 只表达 OKF concept 生命周期；`digest_page_status` 表达 `published/degraded`；`digest_release_status` 只在包级 manifest 表达交付状态；`digest_machine_pass`/audit 记录机器门；`verified` 只记录真实来源/内容核验；不把 `agent_assisted` 写成 `human:` verification actor。
6. 为 bundle、正文和索引建立无 LLM 的结构验证器：frontmatter 可解析、type/豁免身份合法、title/description 可读、sources 引用可回查、index 无空入口、链接不逃逸、`index.md`/`log.md` 不被误当 concept、frontmatter 与 audit records 对账；Task 2-A 只使用人工编写的三类 fixture 正文验证 attribution，不声称语义质量。
7. 固定 PyYAML `safe_load/safe_dump` 的 key 排序、Unicode、缩进、折行和受管 hash 规则；增加零网络的最小外部 OKF parser smoke。若消费者 smoke 无法固定，则把名称降级为 `OKF-inspired profile`。
8. 明确未来边界：`Attested Computation`、executor、attester 和运行时 receipt 不进入本轮；需要时另开规格，不把“看起来结构化”变成重系统。

#### 交付物和涉及范围

- 现有 `navigation.py`、`publication.py`、`page_layout.py`、`provenance.py` 的最小 OKF profile writer/validator；受控 YAML parser/serializer 依赖和版本锁定；不新增通用 repository/service 层；
- Reader Bundle layout、frontmatter schema/version、source/claim footnote contract、状态映射文档；
- 三类 concept 的最小 fixture、`index.md`/`log.md` 示例和 OKF profile acceptance 测试；
- Task 1 TopicIndex → Reader Bundle 的确定性投影报告；
- 可选的 `config/knowledge-digest.okf.example.json`，只声明 profile 和输出规则，不写密钥。

#### 依赖和不做什么

- 依赖：Task 0、Task 1 的账本、TopicIndex、ProductGazetteer 和路径规则；
- 不做全量 89 篇、不调用 LLM、不重写正文、不引入 OKF runtime、Knowledge Catalog、数据库或图服务；
- 不删除旧 Reader/Audit 产物；只在隔离 fixture 中生成 OKF-compatible bundle；
- 回滚：profile 输出是可重建投影，失败只保留 audit/fixture，不覆盖旧正式结果。

#### 验收标准

1. Reader Bundle 有 `README.md`、`Home.md`、根 `index.md`、根 `log.md` 和产品/模块/主题层级；`log.md` 是必选根文件，至少包含状态和本次变更摘要；嵌套目录不生成 `log.md`。`index.md`、`log.md`、`README.md`、`Home.md`、`references/sources.md` 的身份符合 profile 清单，空目录不生成空 index。
2. Task 0/Task 1 exit manifest 的相对路径、hash、版本和覆盖记录通过入口验收；缺失项有 backfill manifest 且包保持 `not_released`。每个正式 concept 都有可解析 YAML frontmatter 和非空 `type`、可读 `title`、一行 `description`；三类 type、`digest_*` 字段、Task 1 `topic_key_v2`、`digest_topic_id` 和路径一致；重复 TopicIndex/replay 得到相同 `digest_topic_id`；产品级无 module concept 不被丢弃或塞入虚构 module，只有真实 module 才有 `modules/index.md`。该标题/description 要求适用于本项目 Reader fixture，不把 OKF 外部输入的可选字段误改成通用 OKF 硬要求。
3. fixture 正文中的每个关键事实 footnote 能解析到稳定 `sources[].id`，并经唯一的 `digest_claims[].claim_id + fragment_locator` 反查稳定 Claim、source URI 和 content fingerprint；真实正文归因由 Task 2-B 验收；审计包能反查完整 Claim/Evidence。
4. `generated`、`verified`、`digest_machine_pass`、`status`、`stale_after` 的语义和页/包状态分离；没有真实内容核验不能生成 `verified`；没有人工验收不能生成 `human:` actor；没有 freshness 证据不猜 `stale_after`。
5. Reader Bundle 不含 `_digest`、`_archive`、provider 原始响应和完整快照；标准 Markdown links 可达，关系没有由相似度臆造；失败、冲突、无归属或未通过质量门的页只出现在 Audit/Archive `_digest/degraded/`，不出现在 Reader 导航。
6. 同一 TopicIndex 和输入重复运行时，路径、index 内容和受管 frontmatter/hash 稳定；`generated.at`、verified 追加和 manifest release 状态按 §6.9 易变字段规则处理；未知扩展字段经过 YAML parse → write → parse 后语义不丢失，且 nested `sources/generated/verified` 不被扁平化。
7. `--no-llm`/Jaccard 运行网络调用数为 0；Task 2-A 只生成 `not_released` 的 bundle projection，不声称通过读者质量。
8. 固定版本的零网络外部 OKF parser 能读取 sample bundle；若该 smoke 不通过，产物名称和文档不得宣称 `OKF-compatible`。

### Task 2-B：小语料类型化正文编译闭环

#### 背景

历史 Task2 的 `publication_only` 路径禁止 `final_body`，同时旧合同要求 Claim 原文逐字出现在正文，于是最安全的实现变成把 Evidence 原文放进页面。`old_target_body` 没有真正进入 revise 上下文，所谓合并只是历史 Claim 拼接。Task 2-A 只解决了 bundle/frontmatter/index 结构，不能自动解决正文语义；没有 Task 2-B 小语料闭环，直接全量只能放大问题。

#### 参考

- `20260804-output-content-quality.md`、`20260804-companybrain-content.md`；
- `20260804-design-s4-s6.md`；
- `docs/plans/summary-evidence-output-design.md`（仅保留其无损证据原则）；
- `goinsight-loss-report.md`、`sc-cb-analysis.md`、`sleep-curator-report.md`；
- Opus 盲审关于 claim-id、抽样蕴含和 Evidence/body 分离的修正。
- Task 2-A 的 OKF-compatible Reader Bundle contract 和 source/claim footnote contract。
- 默认首层盲审关于正文归因、golden-negative fixture、命令/参数保真和读者门职责的修正。

#### 调研结论

- 58/120 页面出现 Summary/Why 占位，说明必填字段只是格式门，没有真实内容合同；
- Evidence 具备保存价值，但不适合作为读者正文；
- CompanyBrain 的正式页按产品、模块、场景和边界组织，而不是按原文顺序堆行；
- 规则性截断会丢 FAQ、参数、错误码、Why、版本和视觉引用，不能用短摘要替代完整证据；
- 读者质量必须在小语料就测，不能等到全量。

#### 方案

1. 交付并锁定 `Structure Normalizer → TopicIndex → PageDraft → OKF Concept Compiler → Publication Gate` 这条链，打通 12–20 篇代表样本；Normalizer 必须把父子页、标题/H1、FAQ、表格、图片引用、双语段落、版本标记和噪声块转成可追溯结构，不能只做文本清洗。冻结 inventory 中存在的多源同产品、单源完整手册、超长、表格、中英混排、provider 失败和无 body 类别必须覆盖；不存在的类别用 machine fixture 或排除理由显式记录。
2. 解除“禁止 final_body”和“逐字 Claim 包含”两个冲突合同；正文只编译可读答案，使用 OKF `sources[].id` footnote + `claim_id` 回指；Evidence/archive 保留完整 Claim、原文、表格和图片。
3. 实现三类页面：`product_overview`、`module_or_capability`、`procedure_or_rule`。每类只生成自己的必需 section；必需字段无证据则整页 `degraded`，可选字段省略；正式正文禁止“原始资料未载”等通用占位句，缺失原因写入状态和审计。
4. 真正把 `old_target_body` 放进 revise 上下文；更新时按语义重组，不把新旧 Claim 简单连接。
5. 保留 Claim 验证、数字/标识符/版本检查、稳定 `claim_id` 可解析和抽样蕴含；失败只能生成 `degraded`，不进入 formal 导航。每次抽样记录 seed、样本量、阈值和失败项。
6. 使用 Task 0 冻结的 17 个正向问题和 3 个负向问题；Task 2-B 只运行“样本中有答案”的派生子集做机器诊断，不能因语料没有答案而误判编译器；Task 2-C 才执行人工读者门，Task 3 才运行完整题集。题集派生规则、抽样种子和最低阈值在 Task 2-C 启动前冻结。
7. 主题超长时按语义边界拆分；同主题保留总览、相关 key 和 `prev/next`，每个 Claim 只落一个 part，不能让 `part-1` 代替主题主入口。
8. Task 2-B 只负责页内用途、边界、下一步和来源入口；2-A 在 fixture 上生成骨架 index，2-B/2-C 复用同一导航生成器在小语料包生成和验收产品/模块/主题 index，Task 3 只做全量投影，不维护第二套导航事实。
9. 语义样本运行继承统一的 provider allowlist、单请求硬超时、并发/输出 token/调用预算和有限重放；当前示例值不是永久 PRD 身份，Task 0 必须冻结实际值并写入 manifest，超限或硬超时只能 `degraded`，不能以截断 JSON 或 fallback 结果冒充成功。
10. 正文编译不得改写 OKF frontmatter 的来源/信任字段；内容更新必须同时更新 `generated`，重新验证后才能追加 `verified`，内容变化不能沿用旧 human verification。
11. 机器正文门必须检查必需 section 有真实内容、每个 section 的全部事实断言都有可解析归因（100%；“每 section 至少一条”只作为结构诊断）、命令/端口/配置项没有事实改写、重要表格/图片引用没有只落到 Audit；加入历史低质量输出的 golden-negative fixture 和同页/跨页近重复诊断。
12. Normalizer 的验收必须逐项对账：父子关系、FAQ 问答边界、表头/行、图片 alt/URL、双语配对、版本字段和噪声块均有输入→结构输出记录；无法识别的结构进入 Audit 缺失项，不得静默删除。
13. 语义运行只有在至少 6 个 machine-passing concept 成功生成、三类 page type 各至少 1 个（真实样本或 Task 0 已登记的 machine fixture），并覆盖 Task 1 inventory 中实际存在的长文、表格/图片、双语和多源类别时，才算 Task 2-B 语义 exit；多源类别在 inventory 中存在时必须覆盖，不存在时必须留下 machine fixture 和排除理由，不把不存在的类别变成无法满足的硬门。fallback、全是 `degraded` 或缺少已有类别覆盖只能 `not_released`。Jaccard 只能验证离线结构和回归，不能满足语义正文 exit。
14. 版本 oracle 固定为：既有托管 metadata → 来源 frontmatter/显式 metadata → 明确的版本标题/字段；仅接受 semver、日期版本或来源明确的 release label。多个不一致版本、版本字段无法解析时页级 `degraded`；`product_overview` 可在来源确实没有版本信息时省略，`module_or_capability` 与 `procedure_or_rule` 若来源声明版本相关行为则必须有可回查版本证据；`stale_after` 只能由来源明确的有效期/复核日期产生。

15. 小语料运行失败时只允许有限 defect loop：重试对象限于本次失败的 normalizer、compiler、validator、navigation 或 writeback；保留失败 manifest 和旧样本包，重复失败保持 `degraded/not_released`。若要改变 page type、section、字段、题集、阈值或 provider allowlist，必须走新的 scope revision，不能用重试掩盖合同变更。显式 `--no-llm + Jaccard` 只能作为离线结构基线，不能作为语义 package 的 release 证据。

#### 交付物和涉及范围

- `draft.py`、`publication.py`、`page_layout.py`、`faithfulness.py`、`llm.py` 的最小职责调整；
- 三类 page contract、PageDraft 和 claim-id 引用格式；
- OKF-compatible concept fixture、frontmatter/footnote 产物和 profile validator 报告；
- sample corpus、TopicPlan、编译结果和 reader scorecard；
- 必需/可选 section 矩阵、占位禁止规则、claim-id 算法和蕴含抽样合同；
- acceptance 测试：正文/Evidence 分离、无占位、多源合并、独立主题分离、provider 失败隔离、旧正文语义更新。

#### 依赖和不做什么

- 依赖：Task 1 的稳定 TopicIndex 和产品词典、Task 2-A 的 Reader Bundle contract；
- 不做全量 89 篇，不扩展为八类页面，不做永久 candidate 队列和无人维护的人工复核系统；
- 不使用“正文复制率 ≤20%”作为全局硬门；正文不得出现连续原文块，复制比例按 page type 监控，最终由读者门判断；
- 回滚：样本编译失败时只保留样本 audit/archive，旧 formal 不覆盖。

#### 验收标准

1. 三类 page contract 的必需 section 全部有真实内容；每个必需 section 的全部事实断言都必须有可解析归因（100%，section 至少一条只是结构性最低门）；导航文案、由 metadata 直接生成的标题、代码块、表格和带来源标识的短引按固定例外处理。必需证据缺失时页级为 `degraded`；正式正文不得出现“请阅读 Evidence”“来源未说明”“原始资料未载”“Missing”“暂无已验证的相关主题”等通用占位句。
2. 正文不再把 Evidence 区当主体，不出现连续大段原文、图片 URL 堆或原始表格无解释堆积；完整证据可从 claim-id 回查。
3. 每个正文 Claim 引用都能解析到唯一的 `claim_id`、source URI、content hash 和 fragment locator；一个 source entry 不得用同一个 locator 含糊覆盖多个 claim。数字、标识符、版本在编译后保持一致，跨重跑 claim id 不漂移。
4. 多源同产品同主题能合并，独立产品/模块/过程不会因相似词被误合并；同一来源不会重复计入。
5. `old_target_body` 真实影响 revise 结果；更新来源不会残留旧标题、旧正文或幽灵证据。
6. 预注册题集中的样本可答性只作为机器诊断，记录首次命中、证据回查、section 完整性和失败原因；不得在 Task 2-B 伪装成读者质量通过。3 个负向问题的人工读者门归 Task 2-C；完整题集的 15/17 门只在 Task 3 执行。Task 2-B 必须使用 Task 0 冻结的确定性 answerability 标签，不得临时删题。
7. 机器状态、agent 辅助状态和人工状态分别记录；没有人工记录不能声称“读者质量已通过”。
8. 超长主题按语义边界拆分，正文 ≤120 行、整页 ≤300 行；没有 Claim 丢失、重复或无入口 part。
9. 至少一次冻结 provider/model/预算的真实语义小语料运行完成并留存结果；provider 失败、截断 JSON 或 fallback 只能形成 `degraded/not_released`，不能进入正式导航。
10. 质量 oracle 的分母、检测器和阈值可重放：必需 section 事实断言归因 100%；关键命令/端口/配置/表格/图片集合保真率 100%；连续逐字来源块与近重复按 §6.9 固定规则检查；golden-negative 必须失败。
11. 语义 exit 证据满足方案中的最小成功页数和覆盖条件；Jaccard/offline 结果不能替代语义编译成功；版本字段和 stale 规则按固定 oracle 验证。

### Task 2-C：信任信号与读者质量门（小语料）

#### 背景

OKF v0.2 解决的是“读者/Agent 在打开正文前，能看到来源、生产者、验证和新鲜度信号”；它没有替 KnowledgeDigest 定义读者是否真的能完成任务。Task 2-B 即使能生成结构化正文，也可能出现标题可读但答案不完整、来源归因错、过期内容仍出现在默认入口等问题。因此信号接入和读者验收必须独立成门，不能由 frontmatter lint 或 provider 成功代替。

#### 参考

- [OKF v0.2 SPEC.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) 的 `sources`、`generated`、`verified`、`status`、`stale_after`；
- `20260806-okf-structure-research.md`、`20260806-task2-replan-okf-audit.md`；
- Task 0 冻结的 17 个正向问题和 3 个负向问题；
- `20260804-companybrain-reader-journey.md`、CompanyBrain 的真实阅读路径。

#### 调研结论

- OKF 的 trust tier 是 advisory signal，不是发布许可；`verified: human:*` 不能绕过本项目的人工读者门。
- `generated.at` 是正文最后一次有意义变化时间，不能拿来源 `last_modified` 或运行时间冒充；`stale_after` 没有证据就不能猜。
- 静态字段通过不代表正文能回答“是什么、怎么用、限制/异常、版本和来源”；必须保留人工评分和失败样本。
- Task 1 的 `topic-index.json` 是内部计划，不应被读者误认为已经通过知识质量验收。

#### 方案

1. 在 Reader Bundle 页头和产品/模块索引展示可查询信号：concept type、description、来源数、`generated.at`、derived trust tier、`status` 和 stale 提示；信号来自同一 audit records/frontmatter 的确定性投影，不另存第二份 trust 事实。
2. 统一信号归一：`verified` 的 mapping/list 两种输入得到相同结果；没有 `verified` 显示 `unverified`；结构 lint 只写 `digest_machine_pass`/audit，真实内容机器回查才可产生 machine-confirmed，真实人工事件才允许 `human-reviewed`。不生成 `trust_score`，不把 `usage_count` 当排序分数。
3. 用绝对日期比较 `stale_after`；stale 只提示复核，不自动删除、不自动降级为 `deprecated`，也不能改变 `released` 判定。`status=deprecated` 保留旧链接，但默认新入口隐藏。
4. 运行 Task 0 题集的可答样本子集，记录题目、入口、首次命中页、跳转、答案完整性、边界/版本准确性、来源归因、评审人、日期和失败原因。answerability 由冻结的来源标签和确定性规则决定；正向子集至少 8 题，覆盖至少 2 个产品/模块、2 类页面类型；Task 1 inventory 中存在的长文、表格/图片、双语、多源、失败/degraded 类别必须进入样本或 machine fixture 并给出排除理由；不足 8 题直接 `not_released`。人工门与 agent 辅助、机器门分开落盘；最低门槛在本任务启动前冻结，exit manifest 只能更严格不能放宽。
5. Task 2-C 的人工评审人不得是唯一正文编译实现者；若团队规模无法满足，必须显式记录 `non_independent`，该包不能作为 `released` 的读者证据。每条评分记录必须包含 reviewer identifier、角色、与实现的关系、独立性标记、日期、评分表 hash 和冲突说明；不写私有凭据或本机绝对路径。Task 2-C 失败只生成 `degraded`/`not_released` 样本包，不覆盖旧 formal；只能按 §6.9 的受控 defect loop 修复，不得偷偷改合同。通过后冻结 Concept Contract、模板、信号和评分表，Task 3 不得重新定义。

#### 交付物和涉及范围

- Reader Bundle 页头/索引的信号投影和 deterministic filter；
- trust/freshness/lifecycle validator、信号归一测试和 stale/deprecated fixture；
- 小语料 reader scorecard、逐题人工记录、失败样本、机器/agent/human 三类状态报告；
- Task 2-C exit manifest：Concept Contract、页面类型、信号字段、题集派生规则、评分表、seed、阈值和 commit hash。

#### 依赖和不做什么

- 依赖：Task 0 的题集和状态合同、Task 1 的 TopicIndex、Task 2-A 的 bundle contract、Task 2-B 的可读页面；
- 不做 89 条全量、不引入永久人工队列、不把 OKF reference agent/viewer、Attested Computation 或 trust score 引入运行时；
- 不改变 TopicIndex 身份、页面类型和 Evidence/Provenance 权威；
- 回滚：仅保留样本信号和评分证据，旧 Reader Package 不覆盖。

#### 验收标准

1. 不打开正文即可从根/产品/模块索引看到 type、description、来源数、生成时间、trust tier、status 和 stale 提示；根 `index.md` 与 `Home.md` 不产生两套事实。
2. `verified` mapping/list、缺失验证、机器内容验证和人工验证的 derived tier 结果一致且可重放；结构 lint 不得单独产生 machine-confirmed；没有真实人工记录不能出现 `human-reviewed`。
3. `stale_after` 采用绝对日期确定性判断；stale 不删页、不自动标 stable/deprecated，不伪造 released；deprecated 概念保留旧路径且默认入口隐藏。
4. 冻结的 answerable 正向子集至少 8 题且覆盖规则满足；固定要求为正向子集 100% 命中，3 个负向题误命中 0。每题有人工记录、独立性字段和失败原因，不能用 lint、Claim 数或 provider 成功代替；不足 8 题或评审人 `non_independent` 时包保持 `not_released`。
5. 正文关键事实仍能经 `sources[].id → digest_claims[].claim_id + fragment_locator → Claim/Evidence` 回查；信号投影不能新增第二份来源事实源。候选/失败页只存在 Audit/Archive `_digest/degraded/`，不进入 Reader 导航。
6. Task 2-C exit manifest 固定题集派生规则、评分表、信号字段、模板、provider/config、预算和 commit；Task 3 只能复用，不能在全量阶段临时改门。

### Task 3：全量导航、发布和对比验收

#### 背景

历史 Task2 的 Qwen 产物虽然写出了 89 篇来源对应的页面，但仍是 120 个低语义页面；此前另一轮全量分批实验还出现过只剩 7 个超大聚合页的情况。两种结果都说明全量任务在承担主题探索和正文设计，且失败来源、审计现场和读者页面混杂。全量任务不能再承担探索设计的责任，必须建立在 Task 0、Task 1、Task 2-A、Task 2-B、Task 2-C 的稳定合同上。

#### 参考

- `task2-qwen-final9-20260804`（历史结果证据 ID；本机路径只在研究附件中）；
- `companybrain-reference`（参考语料证据 ID；本机路径只在研究附件中）；
- `20260804-companybrain-reader-journey.md`、`20260804-output-audit.md`、`20260804-knowledge-publication-blind-review-synthesis.md`；
- Task2 的历史报告、Task 2-C exit manifest 和 89 篇输入 manifest。

#### 调研结论

- 原结果的目录可达，不等于可读；CompanyBrain 路径更深，但每一跳都提供用途和边界；
- 17 个 agent-assisted 样本不能代替全量人工读者验收；
- 机器通过、Claim 全保留、页面不超 300 行，都不能单独证明知识质量；
- 全量运行必须冻结输入、词典、模板、provider/model、参数和 commit，才能和 Task2/CompanyBrain 对比。

#### 方案

1. 冻结 89 篇输入 manifest、ProductGazetteer/TopicIndex 版本、Concept Contract v1、三类模板、provider/model、温度、批次和 commit hash。同步冻结 provider allowlist、请求超时、最大并发、输出 token、调用预算、重放次数和墙钟预算；单请求 180 秒、最多一次拆分重放、30 分钟目标/60 分钟硬上限只是当前运行示例，Task 3 manifest 必须记录实际值。语义含义不变时更换 provider/model 不需要修改本 PRD，但必须重跑样本门、更新 manifest 和对比基线；改变语义合同仍需 scope revision。
2. 先从同一 TopicIndex/records 产出 canonical 根 `index.md`、产品索引、产品总览、模块/能力索引、`log.md` 和页面导航；只为真实实例生成目录，不生成空分类，不维护 Home 的第二套事实。
3. 运行全量编译；无归属、失败或冲突的来源仍进入 Audit/Archive Package 的 `_digest/degraded/`，但不进入 Reader Package 或正式导航。
4. 生成结构性 Related links：只有同产品、同模块、共享来源或原文明确互引才产生双向链接；无关系就省略。
5. 生成固定对比报告：Task2 旧结果、CompanyBrain 和新结果分别报告保存完整性、机器质量、正文/导航可读性、信任/新鲜度、失败数量、耗时和调用成本；报告先声明每个指标的可比对象，并在表头标出 `comparable`/`N/A`。CompanyBrain 没有同等 OKF/题集字段的维度标为 `N/A`，不能用主观印象补齐；Task1 只作为内部 TopicPlan/身份基线，不冒充读者质量基线。
6. 对冻结的 17 个正题和 3 个负题做人审，记录评审人、日期、抽样种子、逐题结果、失败页面和修改建议。评审人不能是本次编译器的唯一实现者；若只能自审，必须标注为非独立审查，不能将整包标为 `released`。机器、agent、人工三类状态分开。
7. 根据 TopicIndex 的 `old_path_mapping` 生成旧 Home/index/page 路径的可点击 alias 或明确 deprecated 映射；旧文件若因归档规则保留，也必须在页头/映射文件中指向新 canonical 页面，不能让书签落到无说明的旧正文。

8. 全量失败或中断只允许重放未完成的 affected source/topic；成功批次的 manifest、旧 formal 和审计现场必须保留。重放次数、失败原因和是否因 contract change 终止都写入 audit；重复失败仍保持 `not_released`，不得以 fallback、离线基线或“写入成功”改写发布状态。若只完成 `--no-llm + Jaccard`，可交付为显式 offline baseline，但不能称为本 PRD 的 semantic Reader Package 或 `released`。

#### 交付物和涉及范围

- 89 篇输入对应的全量 OKF-compatible Reader Package 和 Audit/Archive Package（不是要求生成 89 个 Reader 页面）；
- `README.md`、兼容 `Home.md`、canonical `index.md`、产品/模块索引、主题页、`references/` 来源入口和 `log.md`；
- manifest、词典/模板/model/config/commit hash、机器验收报告、读者评分表和对比报告；
- `scripts/task2_publication_comparison.py` 或其后继只读对比工具；
- 全量 acceptance 和不调用 provider 的离线回归。

#### 依赖和不做什么

- 依赖：Task 0、Task 1、Task 2-A、Task 2-B、Task 2-C 全部通过；
- 不在全量阶段新增页面类型、重新定义主题身份或调整质量门；
- 不用“页数更多、Claim 更多、运行更快”替代读者质量；
- 回滚：全量失败只生成新的 degraded/audit 现场，保留旧 formal 和旧 Reader Package。

#### 验收标准

1. 机器门、读者门和交付门全部通过，且报告分别记录 `machine_pass`、`agent_assisted`、`human_reviewed`；页面可有页级 `published/degraded`，整包只有在全部门通过时才是 `released`，否则是 `not_released`，不能称正式发布。
2. Reader Package 只含 allowlist 内的阅读入口、OKF concept、`index.md`/`log.md` 和来源入口；每个 concept 的 frontmatter、source attribution、generated/verified/lifecycle 信号可解析；Audit/Archive Package 可重放全部 89 个来源和失败原因。
3. 17 个正向问题首次命中至少 15 个，3 个负向问题误命中 0 个；负向题覆盖跨产品同名、语料外产品、已不存在/已退休能力等误命中风险。标题脱离路径可理解率至少 90%，产品/模块归属人工准确率至少 90%，并记录抽样规则、评分人和评分量。
4. 页面正文最多 120 行，整页（含来源和引用）最多 300 行；旧分页不出现在当前导航，旧文件不静默删除。
5. 全量正式页无空 product/module/page type、无泛占位、无 hash 主路径、无断链、无空分类；根 `index.md` → 产品 → 模块 → concept 渐进可达；正文不依赖打开原文档案才能理解主答案。
6. 89 个输入来源在 manifest、snapshot、audit ledger 中均可定位；失败来源单独标记，不影响无关已发布页。
7. 与 Task2 和 CompanyBrain 的对比报告能同时说明：内容保留、正文/导航可读性、信任/新鲜度、错误/降级、成本和局限；不得只给一个“通过/失败”。超过调用/超时预算或出现 provider fallback 时，必须标为性能/语义限制，不能用“最终写入成功”掩盖；offline baseline 与 semantic release 的结论必须分栏，不得混为一个结果。
8. 每条旧 formal path 都能解析到新 canonical 页面，或显示 deprecated/alias 映射和原因；旧路径映射来自 TopicIndex，不由页面标题或输入顺序临时猜测。

### Task 3-Closeout：文档同步、项目清理与归档收口

#### 背景

当前项目缺少根 `README.md`；`AGENTS.md`、`CONTEXT.md` 仍主要描述旧的 S1–S6 和旧状态，尚未完整表达 ProductGazetteer、TopicIndex、类型化页面、Reader/Audit Package 及 `released/not_released`。仓库还混有旧任务状态、研究材料、生成缓存和工具运行目录。若不做最后收口，后续维护者会得到互相矛盾的入口，甚至误删仍被配置引用的证据。

#### 参考

- 本 PRD §§5.1、5.3、6.7、8.3；
- 当前 `AGENTS.md`、`CONTEXT.md`、`docs/plans/README.md`；
- `docs/plans/universal-knowledge-digest-design.md`、`docs/adr/`、`docs/decisions/`、`docs/reports/` 和 `evidence/` 的引用关系；
- Task 0–3 产生的 manifest、运行报告、Reader/Audit 包和回滚记录。

#### 调研结论

- 根目录没有面向使用者的 README；AGENTS 中的输出结构、状态和命令必须随实现更新；CONTEXT 中存在旧的 `pending`/“不提供人工复核流程”等表述，需要区分历史约束与新发布验收。
- `BLOCKED.md`、`PROGRESS.md`、`.omc/`、`.multica/`、`.worker-mode/`、`.agent_context/` 等可能是历史任务或工具状态，不能凭文件名直接删除。
- `evidence/phase4` 和配置存在真实引用；`docs/adr`、原始设计和验收 fixture 是长期证据，不属于垃圾。
- 本次 21 份研究/盲审材料应保留可追溯性，但不应永久和活跃计划混在同一层级。

#### 方案

1. **更新 `AGENTS.md`**：以最终仓库实际存在的源文件和目录为准，写入最终文件结构、三份文档职责、Task 0–3（含 2-A/2-B/2-C）+ Task 3-Closeout 边界、运行/测试命令、Reader/Audit 阅读顺序、OKF-compatible Reader Bundle、页级/交付级状态、质量门、凭据安全和文档同步规则；不得把尚未实现的计划模块名写成事实，删除已失效的路径和合同。
2. **更新 `CONTEXT.md`**：补齐 `ProductGazetteer`、`TopicIndex`、规范化 `topic_key`、稳定 `claim_id`、三类 page type、分页、Reader/Audit Package、`published/degraded/released/not_released`、人工修改冲突和 affected set；对仍保留的旧术语标注历史语境，不能出现互相矛盾的唯一解释。
3. **新增根 `README.md`**：提供第一次使用所需的最短路径：项目用途、依赖、输入目录示例、离线命令、语义命令、批次恢复、结果阅读顺序、失败/降级处理、凭据安全、对比脚本和文档入口。README 必须使用当前真实命令，不复制旧任务的绝对路径。
4. **建立仓库 inventory**：扫描 tracked、untracked、ignored 文件以及代码/配置/测试/文档引用，逐项记录 `path、分类、用途、引用、动作、目标路径、hash`。分类只允许 `active`、`archive`、`rebuildable`、`delete-after-confirmation`、`unknown`。
5. **安全归档**：已完成的 spec/plan/tasks/decision log 归入对应 `specs/archive/`；历史报告归入 `docs/reports/archive/`；本次研究归入带日期的 `docs/research/archive/knowledge-publication-20260804/`，保留索引和 hash。完成后更新 `docs/plans/README.md`，让 plans 只保留当前入口和必要开放问题。
6. **安全清理**：只清理经引用扫描确认可重建的 `.DS_Store`、`__pycache__`、`.pytest_cache`、构建元数据和已确认无活跃任务的工具缓存；`.venv`、`.opencode/node_modules`、`.omc`、`.multica`、`.worker-mode` 等先标注用途和归属，再决定删除或保留。禁止宽泛递归删除，禁止删除仍被 config/evidence/test 引用的文件。
7. **收口检查**：验证 README 命令、文档链接、配置引用、脚本引用、测试引用、Git 跟踪状态、目录 allowlist 和归档映射；清理后保留可恢复记录，不能用“目录变小”代替证据。
8. **便携性检查**：活跃配置和 README 不得依赖 `<本机绝对路径>`；`config/knowledge-digest.json` 的 calibration artifact 改为相对路径或 example 配置，历史报告中的绝对路径只作为历史证据保留并标注。
9. **归档恢复演练**：从最终研究/报告/spec 索引随机抽取至少 3 个归档项，按旧路径映射和新索引重新解析并读取，验证 hash、链接和恢复路径都有效；恢复演练失败时不得删除源文件。

#### 交付物和涉及范围

- 更新后的根 `AGENTS.md`、`CONTEXT.md`、新增根 `README.md`；
- `config/knowledge-digest.offline.example.json` 或等价的可复制离线配置样例；
- 更新后的 `docs/plans/README.md`；
- 在 `docs/research/`、`docs/reports/`、`specs/archive/` 存在多层历史材料时，新增或更新各目录的 README/index，列明 active、historical、archive 入口和旧路径映射；
- `docs/reports/knowledge-digest-publication-repository-hygiene.md`：完整 inventory、引用扫描、保留/归档/删除决策、目标路径、hash 和恢复说明；
- 研究、旧规格和历史报告的归档索引；
- `.gitignore` 或等价生成物规则（仅在确有缺口时补充）；
- 文档链接、命令 smoke、目录 allowlist 和清理回归测试。

#### 依赖和不做什么

- 依赖：Task 0–3 的最终代码合同、实际输出结构和最终状态定义；
- 不在 Task 3-Closeout 新增页面类型、修改主题身份、改变质量门或重写历史证据；
- 不把历史研究“压缩后删除”，不删除 `docs/adr/`、原始设计、有效 fixture、`evidence/phase4` 或仍有引用的脚本；
- 不把项目缓存清理误用于知识库 `_archive/`；来源快照、正式页旧版本和 provenance 历史仍按原始方案只增不删；
- 若某项无法确认是否可删，保留并标为 `unknown`，由后续明确决策处理；
- 回滚：文档改动和归档移动都保留 Git 可逆记录，任何删除前先形成清单和恢复副本。

#### 验收标准

1. `AGENTS.md` 能准确说明最终架构、实际文件结构、开发/测试/发布规则和文档同步规则；文件树来自最终仓库，不存在虚构的计划模块、已删除路径、旧状态或与 PRD 相冲突的合同。
2. `CONTEXT.md` 的术语和字段与代码、manifest、Reader/Audit 包一致；`topic_key`、`claim_id`、page type、状态和归档语义各有唯一解释。
3. 根 `README.md` 存在且新用户可按其完成一次离线运行、找到 Reader Package、定位 Audit Package 和理解失败状态；命令与路径经过 smoke 验证，离线配置可从 `config/knowledge-digest.offline.example.json` 复制。根 README 与每次生成的知识库 `README.md` 分别验收，不能用后者替代前者。
4. 三份入口文档互相链接但不重复维护事实；文档中的路径、命令和状态引用全部可解析，过时引用为 0。
5. 活跃 README、AGENTS、CONTEXT、config 和 docs index 不包含本机绝对路径、临时下载目录或凭据；历史报告中的绝对路径必须明确标为历史证据。
6. inventory 覆盖 tracked/untracked/ignored 目标，逐项有分类、理由、引用和动作；`active`、`archive`、`rebuildable`、`delete-after-confirmation`、`unknown` 五类没有遗漏。
7. 原始设计、ADR、有效验收 fixture、`evidence/phase4` 和仍被引用的配置/脚本均保留；归档文件有索引、旧路径映射和 hash；研究材料不再散落在活跃入口层，`docs/research/`、`docs/reports/`、`specs/archive/` 各有唯一可发现入口或明确指向已有等价索引。
8. 可重建缓存和确认无引用的临时产物才被清理；清理后没有未解释的生成物，`.venv` 等仍需保留的本地环境必须在 inventory 中说明。
9. `uv run pytest tests/ -q`、README 中的离线 smoke、文档链接检查和目录 allowlist 检查通过；Task 3-Closeout 不改变 Task 0–3 的行为验收结果。
10. 若 Task 3 是 `not_released`，README、AGENTS 和最终报告必须如实写明；文档收口不能把失败结果改写成 `released`。
11. 至少 3 个归档项完成恢复/链接解析演练，旧路径映射、索引入口和 hash 均可验证；演练失败的材料只能保留为 `unknown`，不能删除。

## 8. 全局质量门

### 8.1 机器门

- manifest、snapshot、ledger 来源集合闭合；Claim、duplicate、history 幂等；S6 在写回前完成；
- batch size 1/20、输入顺序和重复运行的 TopicIndex 成员、topic key 和正式路径一致；相同 key 不得出现多个主题；
- ProductGazetteer 有 seed、owner、版本、alias、匹配优先级和冲突记录；未知项只能进入 degraded/候选提案；
- 正式页有产品、模块、page type 和可读标题；禁止 hash、裸短名和通用占位；overview 不能是空壳；
- bundle 内所有非 `index.md`/`log.md` Markdown 必须有合法 concept `type` 或命中 profile 豁免清单（Reader `README.md`、`Home.md`、`references/sources.md`）；`sources[].id`、`generated`、`verified`、`digest_machine_pass`、`status`、`stale_after` 按 profile 语义校验，未知扩展字段 round-trip 不丢失；根 `index.md` 只声明 `okf_version`，嵌套 index/log 不被当成 concept；
- Reader Bundle 只有一套 canonical reader tree；`Home.md` 只能指向根 `index.md`，不能维护第二套导航事实；每个 index 条目有真实目标和一行 description；
- 每个正文引用都能解析 `sources[].id → digest_claims[].claim_id + fragment_locator → source_uri/content_hash/locator`；每个事实归因只对应一个 claim/locator；数字、标识符和版本不漂移；
- frontmatter 与 audit records 对账：`digest_content_hash`、sources/claims、generated 事件、TopicIndex tags 和 stale 日期均能从同一事实源重算；`human:<id>` 必须能回查人工记录；concept 页不承载包级 release 状态；
- YAML parser/serializer 参数固定，受管 hash 明确排除 `digest_content_hash` 自身、时间、verified 追加和 manifest release 状态等易变字段；同输入重复运行不产生假冲突；每个 `sources[].digest_claims` 按 Claim ID 字典序稳定排序且不得重复；
- 正文与 Evidence 分离，正文 section 按 page type 完整，正文 ≤120 行、整页 ≤300 行；
- 每个必需 section 的全部事实断言 100% 有可解析归因；“每个 section 至少一条”只作为结构性诊断，不可替代事实覆盖；关键命令、端口、配置项和重要表格/图片引用与 Evidence 对账；历史低质量 golden-negative fixture 和连续原文块/近重复检查必须通过；
- 超长主题按语义边界拆分，Claim 不丢失、不重复，主题总览和 `prev/next` 可达，`part-1` 不能代替主题入口；
- provider 失败、JSON 破损、事实冲突、无 body、无归属来源不得进入 formal 导航；其降级记录必须落在 Audit/Archive `_digest/degraded/` 并带原因、输入指纹和恢复路径；
- 显式 `--no-llm + Jaccard` 可作为离线基线；每次运行只使用一个 similarity backend。语义模式若按既有合同回退 Jaccard，manifest/status 必须显示 fallback，且语义发布整包不得标 released；
- 相关链接有结构证据且双向；无关系时省略；
- Home、分类、来源入口无空页和断链；旧 formal 路径稳定或有真实 redirect/alias 映射；
- 正式托管页的 hash 与上次生成 hash 不一致时不得静默覆盖，必须冲突/degraded；affected set 外正文和路径字节不变；
- Reader/Audit 包按 allowlist 分离；`--no-llm` 网络调用数为 0。

### 8.2 读者门

- Task 0 冻结的 17 个正向真实问题 + 3 个负向问题有原文、入口、期望主题/产品、覆盖角色、负向设计、seed、评审人和 hash；Task 2-B/2-C 只运行样本可答子集，Task 3 运行全量题集；
- Task 2-B 只做机器诊断，不形成读者质量通过；Task 2-C 是唯一小语料人工读者门，最低阈值在启动前冻结并写入 exit manifest；`≥15/17` 是 Task 3 全量读者门，不得把样本门伪装成全量门；
- 正向首次命中 ≥15/17，负向误命中 0/3；
- 每次跳转都说明当前页面的用途、边界和下一步；不把“最多四跳”作为硬指标；
- 标题脱离路径可理解 ≥90%；产品/模块归属准确率 ≥90%；评分规则、样本量和评审人可追溯；
- 页面不打开原始档案也能回答是什么、怎么用、限制/异常、版本和来源；
- 人工评分表记录题目、入口、首次命中页面、是否正确、错误原因、评审人、日期和抽样种子；
- `agent_assisted` 不能冒充 `human_reviewed`；人工门是一次性发布验收，不创建永久人工队列。
- Reader 页头可在不打开正文时展示 `generated`、derived trust tier、`status`、stale 和来源数；OKF advisory signal 不等于 `published` 或 `released`。

### 8.3 交付门

- Reader Package、Audit/Archive Package、manifest、词典/模板/model/config/commit hash 和报告齐全；
- 失败和未审内容都能定位，且不能覆盖旧 formal；
- 页级对外只发布 `published` 或 `degraded`；整包只在机器、读者和人工门全部通过时标 `released`，否则 `not_released`；不把“写入成功”当成“知识发布成功”；
- 语义运行的 provider/model/endpoint/dim/probe/calibration、timeout、replay、call budget、wall-clock 和凭据来源均可审计，凭据不在任何产物中；
- 对比报告同时包含机器结果、读者结果、保存完整性、性能和成本。

### 8.4 文档和仓库卫生门

- `AGENTS.md`、`CONTEXT.md`、根 `README.md` 和 `docs/plans/README.md` 与最终代码、命令、状态和目录一致；
- README 的离线 smoke 命令、文档链接、配置/脚本引用和目录 allowlist 可重放；
- inventory 覆盖 tracked、untracked、ignored 的目标文件，并为每项给出保留、归档、重建、删除或待确认决定；
- 原始设计、ADR、有效 fixture、`evidence/phase4` 和仍被引用的证据未被清理；归档文件有索引、hash 和旧路径映射；
- 未解释的缓存、任务状态和临时目录为 0；需要保留的本地环境必须在 inventory 中明确，不以“看起来像垃圾”为删除依据。

## 9. 任务依赖和退出物

```text
Task 0
  └─ 退出物：闭合账本、诚实状态、分离交付包、回归测试
       ↓
Task 1
  └─ 退出物：受管词典、TopicIndex、稳定路径、批次不变性证据
       ↓
Task 2-A
  └─ 退出物：Concept Contract v1-draft、OKF-compatible Reader Bundle 骨架、frontmatter/index validator
       ↓
Task 2-B
  └─ 退出物：一次受控的正文 contract 修订、三类正文编译器、12–20篇样本、claim/source attribution 和语义运行证据
       ↓
Task 2-C
  └─ 退出物：冻结 Concept Contract v1、信任/新鲜度投影、样本读者评分表、机器/agent/human 门证据
       ↓
Task 3
  └─ 退出物：89篇 Reader/Audit 包、全量对比报告、人工验收记录
       ↓
Task 3-Closeout
  └─ 退出物：AGENTS.md、CONTEXT.md、README.md、清理/归档 inventory、收口报告
```

任一任务未达到退出物，不得进入下一任务。每个任务必须同时保存代码、测试、输入 manifest、样本产物、审计报告和回滚说明。

Task 0 退出时必须额外冻结题集、状态定义、包 allowlist、语义/离线运行区分和预算字段；Task 1 退出时必须关闭词典存储位置、规范化规则、匹配优先级、`topic_key_v2` 和 affected set；Task 2-A 退出时必须关闭 Concept Contract v1-draft、OKF profile、canonical reader tree、豁免清单、frontmatter parser、YAML/hash 规则和 source attribution；Task 2-B 退出时只允许一次有记录的正文 contract 修订，并关闭三类 page contract、必需/可选 section、正文模板、claim-id、质量 oracle 和语义小语料合同；Task 2-C 退出时必须冻结 Concept Contract v1、信号投影、读者评分表、题集派生规则、最低阈值和发布门；Task 3 退出时必须冻结最终实际命令、输出目录和发布状态。Task 3-Closeout 只做文档同步、清理和归档，不重新打开前面任务的业务决策。

## 10. 需求追踪矩阵

| 需求 | 证据来源 | 实施任务 | 关键验收 |
|---|---|---|---|
| 不丢来源且可回查 | 原始设计 S1/S5/S6；provenance 调研 | Task 0/2-A/2-B/3 | manifest/Claim/locator 闭合 |
| 不把批次当主题 | S2/S3 调研；三方盲审 | Task 1 | batch 1/20 TopicIndex 一致 |
| 产品/模块语义主轴 | CompanyBrain IA/reader；盲审 | Task 1/3 | 产品归属 ≥90%，无空主轴 |
| 概念文件可读、可移植、可渐进导航 | OKF v0.2 官方 SPEC/README | Task 2-A/3 | type/frontmatter/index/log/links 合法 |
| 来源、生成、验证、新鲜度可见 | OKF v0.2 官方博客/SPEC | Task 2-A/2-C/3 | sources/generated/verified/status/stale 可重放 |
| 正文可读而非 Evidence dump | content 调研；Opus 盲审 | Task 2-B/2-C/3 | 三类 page contract、无占位、source-id/claim-id 回指 |
| 失败不伪装成功 | output audit/provenance；pi 盲审 | Task 0/3 | `degraded` 隔离、旧 formal 不覆盖 |
| 支持增量稳定更新 | 原始设计目标；盲审 | Task 1/3 | 只重编译受影响主题、路径稳定 |
| 读者能完成真实任务 | CompanyBrain reader；本 PRD | Task 2-C/3 | 15/17 正题命中、0/3 负题误命中 |
| 交付目录易懂 | navigation 调研；CompanyBrain/OKF progressive disclosure | Task 2-A/3 | canonical index、无空页断链 |
| 题集和发布状态可重放 | 三方盲审；本 PRD | Task 0/2-C/3 | 17+3 题集 hash、released/not_released 可验证 |
| 语义调用可控且安全 | 三方盲审；AGENTS.md | Task 0/3 | allowlist、预算、超时、凭据不落盘 |
| 人工修改不被覆盖 | 三方盲审；增量风险 | Task 1/3 | hash 冲突隔离、旧路径可达 |
| 项目可交接 | 用户新增要求；本 PRD §6.7 | Task 3-Closeout | 根 README/AGENTS/CONTEXT 与实现一致 |
| 仓库可维护且可恢复 | 项目清理审计；原始归档原则 | Task 3-Closeout | inventory、引用扫描、归档索引、无未解释生成物 |
| 不引入重设施 | 原始非目标；OSS 调研 | 全部 | 无 DB/图谱/调度器/AgentMemory |

## 11. 新任务启动规则

1. 新任务标题必须明确对应 `Task 0`、`Task 1`、`Task 2-A`、`Task 2-B`、`Task 2-C`、`Task 3` 或 `Task 3-Closeout`，不得把这些任务重新混成一个“全面重构”。
2. 新任务先读取本 PRD、对应研究文件和现有 `AGENTS.md`，再写任务自己的 spec/plan；不重新发明目标。
3. 任务开始前冻结输入范围、代码基线和不改动的旧产物；真实语料必须复制到新的 KB 目录。
4. 先写能复现问题的 acceptance 测试，再做最小代码修改；完成后先跑相关测试，再跑完整测试和对应读者验收。
5. 离线验证使用 `--no-llm + Jaccard`，必须证明没有网络调用；语义发布需要单独记录 provider/model/参数和失败，不把二者混为一类证据。
6. Task 2-A/2-B/2-C 只能生成 `not_released` 样本/候选包；只有 Task 3 的机器门、人工读者门和交付门都通过，才可以把整包标为 `released`；页级仍分别记录 `published/degraded`，整包未通过时明确写 `not_released`，保留失败证据。
7. `Task 3-Closeout` 必须在代码和最终输出稳定后执行；先完成文档一致性与仓库 inventory，再归档本 PRD、对应 spec/plan/tasks 和研究索引，并更新 `docs/plans/README.md`。

## 12. 本 PRD 明确禁止的“假修复”

- 只改文件名、slug、目录名或分页，不改变主题和正文语义；
- 只增加 Summary 字段，却继续把原文 Evidence 当正文；
- 继续要求每个 Claim 原文逐字出现在正文；
- 用 Claim 数、页数、测试通过、写入成功代替读者质量；
- 把所有单来源自动合并或自动视为高置信正式页；
- 让模型自动扩展正式产品词典；
- 在全量失败后删除失败证据、清空 pending 或覆盖旧 formal；
- 把 CompanyBrain 的文件规模和人工不确定模块全部复制进来；
- 为解决可读性引入数据库、知识图谱、调度框架或新的重型抽象。
- 看到旧文件名就直接删除；没有 inventory、引用扫描、归档目标和恢复说明的清理不算完成；
- 把根 README、结果目录 README、AGENTS.md 和 CONTEXT.md 复制成四份互相漂移的“说明书”；
- 把项目缓存清理误删来源快照、`_archive/`、`evidence/phase4`、ADR、fixture 或历史验收证据。

## 13. 实现前必须关闭的技术选择

本 PRD 已冻结业务方向。以下不是重新讨论产品范围，而是各任务启动前必须写入 spec/manifest 的技术决策：

- **Task 0**：题集文件和 hash、页级/交付级状态字段、Reader/Audit allowlist、离线与语义 fallback 规则、timeout/replay/call/wall-clock 预算。
- **Task 1**：`ProductGazetteer` 作为 `kb.structure.md` 的受管区段，或作为由结构文件明确声明的词典文件；topic key 的规范化版本、匹配优先级、alias/冲突规则和 affected set。
- **Task 2-A**：`v1-draft` OKF profile、canonical reader tree、三类 concept type、`README/Home/references` 豁免清单、Task 1 `topic_key_v2` 与 `knowledge_type → concept type` 映射、固定版本 `PyYAML` 的 `safe_load/safe_dump` 参数、frontmatter round-trip、受管 hash/易变字段、`sources[].id`/`digest_claims[].claim_id + fragment_locator` attribution、index/log/Home 唯一职责和外部 OKF parser smoke。
- **Task 2-B**：一次受控的正文 contract 修订、三类 page contract 的 frontmatter/section 字段、必需与可选 section、正文模板、`claim_id` canonical 算法、正文引用语法、section 归因、命令/表格/图片保真、golden-negative/近重复门、机器诊断和语义小语料运行；不执行人工读者质量判定。
- **Task 2-C**：`v1` Concept Contract 冻结、`generated/verified/digest_machine_pass/status/stale_after` 投影、trust tier 归一规则、预冻结题集派生和读者评分表、人工/agent/machine 状态及发布门；最低阈值只能在启动前确定。
- **Task 3**：完整题集评分表、标题/归属抽样规则、provider/model/config 固定值和对比报告字段。
- **Task 3-Closeout**：根 README 的命令 smoke、AGENTS/CONTEXT 的字段核对、inventory 分类、归档目标、`.gitignore` 补充和是否保留本机工具目录的最终决定。

Reader 来源入口固定为 `references/sources.md`；旧 `_digest/source-index.md` 只能作为同一事实源生成的兼容投影。所有选择必须保持“单一事实源、文件化、可回滚、可追溯”，不能重新打开产品范围。

## 14. 最终决策

本项目接下来不是继续修补历史 Task2 的文件命名，而是按 Task 0、Task 1、Task 2-A、Task 2-B、Task 2-C、Task 3 加 Task 3-Closeout 完成一个小型、可验证的知识发布层：

```text
先让系统诚实
→ 再让主题有主轴
→ 先固定 OKF-compatible 概念文件和读者入口
→ 再让正文能独立阅读
→ 再让信任/新鲜度和读者门可验证
→ 最后做全量发布和人工验收
→ 再完成文档同步、清理和可恢复归档
```

完成标准不是“生成了更多 Markdown”，而是：来源没有丢、失败没有伪装、页面有产品和模块语义、正文能回答真实问题、用户默认打开的目录干净，维护者能按三份文档接手项目，历史证据可追溯且没有未解释的仓库垃圾。
