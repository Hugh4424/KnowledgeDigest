# KnowledgeDigest 知识发布架构 PRD

**版本**：v1.2
**日期**：2026-08-04
**状态**：三方盲审修订版，任务启动前的统一需求基线
**适用范围**：Task 0–Task 3 的知识发布架构，以及 Task 3-Closeout 的文档和仓库收口

## 0. 这份 PRD 怎么用

这份文档是后续新任务的唯一业务需求入口。它把今天的原始方案、Task2 结果审查、CompanyBrain 对照、17 份本地调研和 3 路盲审压成一套可执行的需求、方案和验收合同。

今天的原始报告不删除。它们是证据附件；本 PRD 是决策和任务入口。报告与本 PRD 冲突时，以本 PRD 的冻结决策和验收标准为准，原始报告只用于追溯证据。

本 PRD 不推翻原来的 S1–S6 保存、安全和溯源底座，而是在其上补齐“知识编译与读者发布层”。目标不是把 Markdown 重新排版，而是让用户能从一个产品、模块或实际问题出发，快速找到能独立阅读、能判断边界、能追溯来源的知识。

本版吸收 `pi/k3`、`cursor/grok`、`claude-code/opus` 的盲审意见。三方都认可四个核心实现任务的路线和轻量架构，但原稿还缺少最终文档同步、使用入口和仓库卫生；本版增加一个只在实现完成后执行的 Task 3-Closeout，不改变核心编译架构。

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
  → Task 2 小语料正文编译闭环
  → Task 3 全量发布与读者验收
  → Task 3-Closeout 文档同步、清理与归档收口
```

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

结果目录：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804`

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

`/Users/Hugh/Hugh/Knowledge/CompanyBrain` 的可借鉴点不是文件多，而是它先定义了读者如何理解知识：

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
3. [`/Users/Hugh/Hugh/Knowledge/CompanyBrain`](/Users/Hugh/Hugh/Knowledge/CompanyBrain)：读者体验和信息架构参照。
4. [`docs/plans/summary-evidence-output-design.md`](./summary-evidence-output-design.md)：Summary/Evidence 历史输出合同；其中“正文逐字包含 Claim”的部分被本 PRD 明确替代。

### 3.2 今天新增的研究文件

以下 17 份文件在 Task 3-Closeout 前保留在 `docs/research/`，其核心结论已经写入本 PRD；Closeout 后统一迁入带日期的研究归档目录，并由研究索引和本 PRD 保留可追溯入口：

| 研究文件 | 已吸收的核心结论 |
|---|---|
| `20260804-knowledge-publication-fix-direction.md` | 保存层已成形，知识产品层缺失；提出两层架构和问题总诊断 |
| `20260804-knowledge-publication-blind-review-synthesis.md` | 三方盲审综合；冻结三类页面、两态发布和四任务顺序 |
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

### 3.3 历史调研的保留结论

`docs/research/` 中的以下历史文件在 Task 3-Closeout 前作为方法依据继续保留；归档后只改变路径，不改变内容和证据身份：

- `goinsight-loss-report.md`：硬编码截断会丢 FAQ、参数、错误码、Why、版本、视觉引用；归档不能是假来源。
- `sc-cb-analysis.md`、`sleep-curator-report.md`：可借鉴 claim 级验证、revise/merge、可恢复写回和产品/模块页面体系，但不照搬外部运行时。
- `ovmc-analysis.md`：完整链接聚类、阈值需按目标语料标定、不能默认引入重型依赖。
- `oss-knowledge-curation.md`：只借鉴增量 upsert、实体/关系和文件化治理，不引 GraphRAG、数据库或调度框架。
- `ov_find_maxstore_retrieval_report.md`：OpenViking 检索背景，不进入正式架构依赖。

## 4. 原始方案实现度和缺口

| 原方案部分 | 当前结论 | 本 PRD 的处理 |
|---|---|---|
| S1 采集、快照、内容指纹 | 基本成立，但父子页、表格、图片、双语归一不足 | Task 0 对账；Task 2 补结构归一化 |
| S2 聚类、complete-linkage | 有工程形态，但没有完整 F1–F7 和产品/模块语义 | Task 1 建 TopicIndex；批次不再生成主题 |
| S3 top-k 检索和 new/revise/merge | 代码存在，语义页面规划未真正实现 | Task 1 冻结主题计划；Task 2 实现编译上下文 |
| S4 Claim/faithfulness | 保留和验证较强，但正文仍是 Evidence 堆积；`old_target_body` 未真正参与 | Task 2 引入 Typed Page Compiler |
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
- `machine_pass`、`agent_assisted`、`human_reviewed` 是独立证据字段，不能互相替代；Task 0–2 可以生成页级结果，但不能把整包标为 `released`。
- 主题 key、`claim_id`、词典版本、编译参数都必须可重算、可重放，不能依赖批次、输入顺序或单一来源 hash。
- 语义运行必须记录 provider、model、endpoint、embedding 维度、probe/calibration hash、超时、重放次数和调用预算；凭据只从环境变量读取，绝不写入日志、报告或知识库。
- 当前语义发布 allowlist 沿用项目约定的 `qwen3.6`（`https://dashscope.in.whatspos.cn/v1`）和 `jina-embeddings`（`https://llm.paxszapp.com/v1`）；更换 provider/model/endpoint 必须先更新任务 manifest 和验收基线。
- 成功运行也不得静默覆盖人工修改：若正式托管页与上次生成 hash 不一致，必须标为冲突/`degraded`，保留旧页并要求显式处理。
- 方案完成后必须同步更新 `AGENTS.md`、`CONTEXT.md` 和根 `README.md`；README 是使用入口，AGENTS 是维护入口，CONTEXT 是术语/字段入口。
- 清理结果必须有 inventory、分类、引用扫描、归档清单和恢复路径；删除只允许针对可重建缓存或经确认无引用的临时产物。

## 6. 目标产品和架构

### 6.1 两个交付包

每次发布生成两个职责不同的包：

**Reader Package**：用户默认打开的知识产品，只包含 `README.md`、`Home.md`、产品/模块索引、正式主题页和读者可见来源入口。不包含 `_digest`、`_archive`、provider 日志、模型原始响应和审计现场。

**Audit/Archive Package**：完整输入 manifest、快照、Claim、Evidence、原始文档、失败原因、归档快照、运行报告和模型/配置 hash，用于审计和恢复。

全量来源状态的唯一事实源是 audit manifest，例如 `_digest/source-manifest.json`；读者侧的 `indexes/sources.md` 是它的投影。若为兼容保留 `_digest/source-index.md`，必须由同一 records 原子生成，不能维护第二份独立事实。

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
Publication Gate
  ├─ page published/degraded
  ├─ released reader package
  └─ not_released audit/candidate package
```

### 6.3 受管产品词典和主题索引

`ProductGazetteer` 是小而受管的词典。v1 至少记录：产品/系统 slug、模块 slug、别名、对象/功能名、置信度、匹配优先级、冲突原因、词典版本、owner 和变更说明。优先作为 `kb.structure.md` 的受管区段，或作为由该结构文件明确声明的词典文件；不得形成第二个未声明的事实源。

Task 1 首次建立词典时，必须用 89 篇输入的标题、H1、父子路径和其他确定性 metadata 生成 seed inventory，并记录 alias、冲突和待确认候选。模型只能提出候选，不能直接写正式词典；冻结运行中遇到未知产品/模块时，来源进入 `degraded`，同时在审计包中输出候选提案，不得静默扩展目录。匹配顺序、冲突规则和版本变更都要写入 manifest。

`TopicIndex` 保存稳定 topic key、产品、模块、对象/问题意图、来源成员、正式路径、旧路径映射和发布状态。

主题 key 是版本化的规范化元组：

```text
topic_key = topic_key_v1(normalize(product_slug,
                                   module_slug,
                                   object_or_intent))
```

规范化规则必须固定并记录版本；key 不得使用 batch、输入顺序、来源集合 hash 或单一来源 hash。相同规范化 key 在同一知识库中必须只有一个主题；产品、模块或对象/问题意图缺失、冲突或无法规范化时，不能猜测合并，必须 `degraded` 并记录原因。第一次导入或显式 rebuild 才做全量 TopicPlan；普通 `digest(new_dir,kb_dir)` 只把新来源匹配到已有索引并局部重编译。

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

Task 0–2 只能生成页级状态和 `not_released` 交付包。Task 3 才能在机器、读者和交付门全部通过后把整包标为 `released`。`machine_pass`、`agent_assisted`、`human_reviewed` 仍分别记录，不得把 agent 输出当作人工验收。

`draft` 可以是内部瞬时状态；不把没有处理人的永久 `candidate` 当成完成态。

### 6.7 方案完成后的文档和仓库合同

方案全部实现后必须形成三份互补的长期入口：

- `AGENTS.md`：项目目标、真实文件结构、职责边界、开发规则、测试命令、质量门、发布状态、文档维护规则和禁止事项。它面向后续编码代理和维护者。
- `CONTEXT.md`：Claim、source snapshot、topic key、`claim_id`、ProductGazetteer、TopicIndex、page type、Reader/Audit Package、`published/degraded/released/not_released` 等术语和字段的唯一解释。它面向需要理解数据合同的人。
- 根 `README.md`：安装/环境、输入目录格式、离线和语义运行命令、批次恢复、结果阅读顺序、Reader/Audit 包区别、失败排查、凭据安全和项目结构。它面向第一次使用本项目的人；它与每个结果目录中的 Reader Package `README.md` 不同，后者只解释单次结果。

三份文档必须指向同一份实际命令和路径；任何 CLI、正式输出、状态、目录或质量门变化，都要同步更新文档和 acceptance 测试。README 不复制完整设计，AGENTS 不承担用户教程，CONTEXT 不承担运行步骤。

Task 3-Closeout 还要对全仓库做一次“保留、归档、删除、待确认”盘点：

- 保留原始方案、ADR、有效 acceptance fixture、`evidence/phase4`、仍被配置/脚本引用的校准和验收证据；
- 将已完成任务的 spec/plan/tasks/decision log、旧任务状态和已结束报告归入对应 `specs/archive/` 或 `docs/reports/archive/`，保留索引和来源 hash；
- 将 17 份本次研究和盲审材料在任务完成后归入带日期的研究归档目录，PRD 保留主结论和证据索引；
- 对 `.DS_Store`、`__pycache__`、`.pytest_cache`、`.venv`、`.opencode/node_modules`、`.agent_context`、`.omc`、`.multica`、`.worker-mode` 等生成物逐项确认是否有活跃任务或 Git 跟踪后再清理；补齐 `.gitignore` 中的缓存/本地环境规则；不得用宽泛递归删除；
- 根目录只保留当前用户入口和项目状态索引；`BLOCKED.md`、`PROGRESS.md` 等旧任务状态必须迁移、重命名为历史报告，或明确标注当前有效性。

清理后的仓库必须能通过“文档链接、配置引用、脚本引用、测试引用、Git 跟踪状态和目录 allowlist”检查；任何仍被引用的文件不得被删除，任何被归档的文件必须有新路径映射。

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
2. 将 S6 provenance 和账本/交付包门移到写回前；Task 0 只检查 Claim、来源、路径、状态和交付包事实，不承担正文语义质量，正文质量由 Task 2/3 检查。
3. 分开记录 provider transport、claim verification、writeback、`machine_pass`、`agent_assisted`、`human_reviewed` 和最终发布状态。
4. 失败、JSON 破损、无正文、无产品归属的来源只生成 `degraded` 档案，不进正式导航；无关的已发布页不被整库回滚。显式 `--no-llm + Jaccard` 是合法离线基线；语义模式的 embedding 探测失败可以按既有合同整次回退 Jaccard，但必须在 manifest/status 显示 fallback，若本次要求语义发布则整包为 `not_released`，不得伪装成 embedding 成功。
5. Reader Package 和 Audit/Archive Package 使用 allowlist 生成；Home pending 只指向真实非空队列；空分类、断链和不可点击来源入口直接失败。
6. duplicates、claim-history、批次重跑必须幂等；重复运行不能产生重复来源关系或重复页面。
7. 冻结并落盘 v1 读者题集：17 个正向问题和 3 个负向问题的原文、入口、期望主题/产品、覆盖角色、负向设计原则、抽样 seed、评审人和题集 hash。Task 2 只能使用其中可由样本回答的派生子集，Task 3 使用完整题集。
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
8. 读者题集 manifest 可重放，包含 17+3 题、派生样本规则和 hash；`--no-llm` 运行网络调用数为 0。
9. 同一 snapshot 的重复运行不会产生异常 archive/duplicate 增长；异常可在 audit report 中定位。

### Task 1：产品、模块和稳定主题主轴

#### 背景

Task2 的 `batch_size=1` 产生了 86 个主题，其中 85 个是单来源主题；`product_slug=0`，不同产品的 AE、iOS、GoInsight 等对象没有稳定的产品语义归属。批次和来源被错误地当成了主题边界。

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
8. 正式托管页保存 `last_published_hash`/`managed_content_hash`；发现页被人工改过时不静默覆盖，标记冲突并保留旧页，修复必须通过词典、来源或显式 override。

#### 交付物和涉及范围

- 扩展 `identity.py`、`kb_structure.py`、`page_layout.py` 或等价现有职责模块；
- 受管产品/模块词典和 TopicIndex 的文件格式及版本；
- 89 篇输入的结构特征 inventory（父子页、表格、FAQ、图片、双语、版本和噪声），作为归一化范围依据；
- 稳定路径、旧路径映射和批次不变性测试；
- 12–20 篇代表性样本的 TopicPlan fixture。

#### 依赖和不做什么

- 依赖：Task 0 的账本和失败状态；
- 不引入数据库、图谱、向量索引、通用 repository/service 层；
- 不一次建立十维实体本体，不让模型自动修改正式产品词典；
- 回滚：TopicIndex 是可重建投影，原始快照和旧 formal 页面不删除。

#### 验收标准

1. 同一输入分别以 batch size 1 和 20 运行，TopicIndex 成员、topic key 和正式路径一致。
2. TopicIndex 中产品、模块、对象/问题意图和规范化 key 不为空；无产品归属或冲突的来源为 `degraded`。正式 page type 和必需 section 在 Task 2/3 验收，不由 Task 1 提前伪造。
3. 主入口不使用 `topic-<hash>`、裸 `1.md`、`ae.md`、`ios.md` 等不可读路径；注册别名必须有词典记录。
4. 同产品同对象能进入同一主题计划，不同产品同名对象不会误合并。
5. 普通增量只重编译 affected set；集合外旧 formal 页面正文和路径字节不变，允许 Home/索引中明确列出的受影响计数和相关链接变化。
6. 不生成空分类、空模块或没有真实实例的目录。
7. 单源主题可以发布的前提是资料完整、产品/模块明确、结构有意义、必需证据存在且无事实冲突；单源比例作为报告监控项，不作为硬门。
8. 同一 topic key 在不同 batch size、输入顺序和重复运行中只有一个主题；旧路径映射可达，人工修改冲突不会被静默覆盖。

### Task 2：小语料类型化正文编译闭环

#### 背景

Task2 的 `publication_only` 路径禁止 `final_body`，同时旧合同要求 Claim 原文逐字出现在正文，于是最安全的实现变成把 Evidence 原文放进页面。`old_target_body` 没有真正进入 revise 上下文，所谓合并只是历史 Claim 拼接。没有小语料闭环，直接全量只能放大问题。

#### 参考

- `20260804-output-content-quality.md`、`20260804-companybrain-content.md`；
- `20260804-design-s4-s6.md`；
- `docs/plans/summary-evidence-output-design.md`（仅保留其无损证据原则）；
- `goinsight-loss-report.md`、`sc-cb-analysis.md`、`sleep-curator-report.md`；
- Opus 盲审关于 claim-id、抽样蕴含和 Evidence/body 分离的修正。

#### 调研结论

- 58/120 页面出现 Summary/Why 占位，说明必填字段只是格式门，没有真实内容合同；
- Evidence 具备保存价值，但不适合作为读者正文；
- CompanyBrain 的正式页按产品、模块、场景和边界组织，而不是按原文顺序堆行；
- 规则性截断会丢 FAQ、参数、错误码、Why、版本和视觉引用，不能用短摘要替代完整证据；
- 读者质量必须在小语料就测，不能等到全量。

#### 方案

1. 用 `Structure Normalizer → TopicIndex → PageDraft → Publication Gate` 打通 12–20 篇代表样本；样本必须覆盖多源同产品、单源完整手册、超长、表格、中英混排、provider 失败和无 body。
2. 解除“禁止 final_body”和“逐字 Claim 包含”两个冲突合同；正文只引用 `claim_id`、来源和必要定位，Evidence/archive 保留完整 Claim、原文、表格和图片。
3. 实现三类页面：`product_overview`、`module_or_capability`、`procedure_or_rule`。每类只生成自己的必需 section；必需字段无证据则整页 `degraded`，可选字段省略；正式正文禁止“原始资料未载”等通用占位句，缺失原因写入状态和审计。
4. 真正把 `old_target_body` 放进 revise 上下文；更新时按语义重组，不把新旧 Claim 简单连接。
5. 保留 Claim 验证、数字/标识符/版本检查、稳定 `claim_id` 可解析和抽样蕴含；失败只能生成 `degraded`，不进入 formal 导航。每次抽样记录 seed、样本量、阈值和失败项。
6. 使用 Task 0 冻结的 17 个正向问题和 3 个负向问题；小语料只运行“样本中有答案”的派生子集，不能因语料没有答案而误判编译器；Task 3 才运行完整题集。固定评分表、抽样种子和评审记录。
7. 主题超长时按语义边界拆分；同主题保留总览、相关 key 和 `prev/next`，每个 Claim 只落一个 part，不能让 `part-1` 代替主题主入口。
8. Task 2 只负责页内用途、边界、下一步和来源入口；产品级 Home、产品索引、模块索引由 Task 3 统一生成，避免样本编译器各自维护导航事实。
9. 语义样本运行继承统一的 provider allowlist、单请求硬超时、并发/输出 token/调用预算和有限重放；当前默认值由 Task 0 冻结并写入 manifest，超限或硬超时只能 `degraded`，不能以截断 JSON 或 fallback 结果冒充成功。

#### 交付物和涉及范围

- `draft.py`、`publication.py`、`page_layout.py`、`faithfulness.py`、`llm.py` 的最小职责调整；
- 三类 page contract、PageDraft 和 claim-id 引用格式；
- sample corpus、TopicPlan、编译结果和 reader scorecard；
- 必需/可选 section 矩阵、占位禁止规则、claim-id 算法和蕴含抽样合同；
- acceptance 测试：正文/Evidence 分离、无占位、多源合并、独立主题分离、provider 失败隔离、旧正文语义更新。

#### 依赖和不做什么

- 依赖：Task 1 的稳定 TopicIndex 和产品词典；
- 不做全量 89 篇，不扩展为八类页面，不做永久 candidate 队列和无人维护的人工复核系统；
- 不使用“正文复制率 ≤20%”作为全局硬门；正文不得出现连续原文块，复制比例按 page type 监控，最终由读者门判断；
- 回滚：样本编译失败时只保留样本 audit/archive，旧 formal 不覆盖。

#### 验收标准

1. 三类 page contract 的必需 section 全部有真实内容；必需证据缺失时页级为 `degraded`；正式正文不得出现“请阅读 Evidence”“来源未说明”“原始资料未载”“Missing”“暂无已验证的相关主题”等通用占位句。
2. 正文不再把 Evidence 区当主体，不出现连续大段原文、图片 URL 堆或原始表格无解释堆积；完整证据可从 claim-id 回查。
3. 每个正文 Claim 引用都能解析到稳定 `claim_id`、source URI、content hash 和 locator；数字、标识符、版本在编译后保持一致，跨重跑 claim id 不漂移。
4. 多源同产品同主题能合并，独立产品/模块/过程不会因相似词被误合并；同一来源不会重复计入。
5. `old_target_body` 真实影响 revise 结果；更新来源不会残留旧标题、旧正文或幽灵证据。
6. 预注册题集中的样本可答正向问题全部通过；3 个负向问题误命中为 0。每个样本题记录是否可答，不能把“语料没有答案”计为编译失败；完整题集的 15/17 门只在 Task 3 执行；页面不打开原文档案也能回答主问题。
7. 机器状态、agent 辅助状态和人工状态分别记录；没有人工记录不能声称“读者质量已通过”。
8. 超长主题按语义边界拆分，正文 ≤120 行、整页 ≤300 行；没有 Claim 丢失、重复或无入口 part。

### Task 3：全量导航、发布和对比验收

#### 背景

Task2 的 Qwen 产物虽然写出了 89 篇来源对应的页面，但仍是 120 个低语义页面；此前另一轮全量分批实验还出现过只剩 7 个超大聚合页的情况。两种结果都说明全量任务在承担主题探索和正文设计，且失败来源、审计现场和读者页面混杂。全量任务不能再承担探索设计的责任，必须建立在 Task 0–2 的稳定合同上。

#### 参考

- `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804`；
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain`；
- `20260804-companybrain-reader-journey.md`、`20260804-output-audit.md`、`20260804-knowledge-publication-blind-review-synthesis.md`；
- Task2 的历史报告和 89 篇输入 manifest。

#### 调研结论

- 原结果的目录可达，不等于可读；CompanyBrain 路径更深，但每一跳都提供用途和边界；
- 17 个 agent-assisted 样本不能代替全量人工读者验收；
- 机器通过、Claim 全保留、页面不超 300 行，都不能单独证明知识质量；
- 全量运行必须冻结输入、词典、模板、provider/model、参数和 commit，才能和 Task2/CompanyBrain 对比。

#### 方案

1. 冻结 89 篇输入 manifest、ProductGazetteer/TopicIndex 版本、三类模板、provider/model、温度、批次和 commit hash。同步冻结 provider allowlist、请求超时、最大并发、输出 token、调用预算、重放次数和墙钟预算；当前基线默认单请求 180 秒、最多一次拆分重放、30 分钟目标/60 分钟硬上限，若要改变必须先改 PRD 并写入 manifest。
2. 先产出产品索引、产品总览、模块/能力索引和页面导航；只为真实实例生成目录，不生成空分类。
3. 运行全量编译；无归属、失败或冲突的来源仍进入 Audit/Archive Package，但不进入正式导航。
4. 生成结构性 Related links：只有同产品、同模块、共享来源或原文明确互引才产生双向链接；无关系就省略。
5. 生成固定对比报告：Task2 旧结果、CompanyBrain 和新结果分别报告保存完整性、机器质量、读者质量、失败数量、耗时和调用成本；Task1 只作为内部 TopicPlan/身份基线，不冒充读者质量基线。
6. 对冻结的 17 个正题和 3 个负题做人审，记录评审人、日期、抽样种子、逐题结果、失败页面和修改建议。评审人不能是本次编译器的唯一实现者；若只能自审，必须标注为非独立审查，不能将整包标为 `released`。机器、agent、人工三类状态分开。

#### 交付物和涉及范围

- 89 篇输入对应的全量 Reader Package 和 Audit/Archive Package（不是要求生成 89 个 Reader 页面）；
- `README.md`、`Home.md`、产品/模块索引、主题页、读者来源入口；
- manifest、词典/模板/model/config/commit hash、机器验收报告、读者评分表和对比报告；
- `scripts/task2_publication_comparison.py` 或其后继只读对比工具；
- 全量 acceptance 和不调用 provider 的离线回归。

#### 依赖和不做什么

- 依赖：Task 0、Task 1、Task 2 全部通过；
- 不在全量阶段新增页面类型、重新定义主题身份或调整质量门；
- 不用“页数更多、Claim 更多、运行更快”替代读者质量；
- 回滚：全量失败只生成新的 degraded/audit 现场，保留旧 formal 和旧 Reader Package。

#### 验收标准

1. 机器门、读者门和交付门全部通过，且报告分别记录 `machine_pass`、`agent_assisted`、`human_reviewed`；页面可有页级 `published/degraded`，整包只有在全部门通过时才是 `released`，否则是 `not_released`，不能称正式发布。
2. Reader Package 只含 allowlist 内的阅读入口、索引、正式页和来源入口；Audit/Archive Package 可重放全部 89 个来源和失败原因。
3. 17 个正向问题首次命中至少 15 个，3 个负向问题误命中 0 个；负向题覆盖跨产品同名、语料外产品、已不存在/已退休能力等误命中风险。标题脱离路径可理解率至少 90%，产品/模块归属人工准确率至少 90%，并记录抽样规则、评分人和评分量。
4. 页面正文最多 120 行，整页（含来源和引用）最多 300 行；旧分页不出现在当前导航，旧文件不静默删除。
5. 全量正式页无空 product/module/page type、无泛占位、无 hash 主路径、无断链、无空分类；正文不依赖打开原文档案才能理解主答案。
6. 89 个输入来源在 manifest、snapshot、audit ledger 中均可定位；失败来源单独标记，不影响无关已发布页。
7. 与 Task2 和 CompanyBrain 的对比报告能同时说明：内容保留、可读性、导航、错误/降级、成本和局限；不得只给一个“通过/失败”。超过调用/超时预算或出现 provider fallback 时，必须标为性能/语义限制，不能用“最终写入成功”掩盖。

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
- 本次 17 份研究/盲审材料应保留可追溯性，但不应永久和活跃计划混在同一层级。

#### 方案

1. **更新 `AGENTS.md`**：以最终仓库实际存在的源文件和目录为准，写入最终文件结构、三份文档职责、Task 0–3 + Task 3-Closeout 边界、运行/测试命令、Reader/Audit 阅读顺序、页级/交付级状态、质量门、凭据安全和文档同步规则；不得把尚未实现的计划模块名写成事实，删除已失效的路径和合同。
2. **更新 `CONTEXT.md`**：补齐 `ProductGazetteer`、`TopicIndex`、规范化 `topic_key`、稳定 `claim_id`、三类 page type、分页、Reader/Audit Package、`published/degraded/released/not_released`、人工修改冲突和 affected set；对仍保留的旧术语标注历史语境，不能出现互相矛盾的唯一解释。
3. **新增根 `README.md`**：提供第一次使用所需的最短路径：项目用途、依赖、输入目录示例、离线命令、语义命令、批次恢复、结果阅读顺序、失败/降级处理、凭据安全、对比脚本和文档入口。README 必须使用当前真实命令，不复制旧任务的绝对路径。
4. **建立仓库 inventory**：扫描 tracked、untracked、ignored 文件以及代码/配置/测试/文档引用，逐项记录 `path、分类、用途、引用、动作、目标路径、hash`。分类只允许 `active`、`archive`、`rebuildable`、`delete-after-confirmation`、`unknown`。
5. **安全归档**：已完成的 spec/plan/tasks/decision log 归入对应 `specs/archive/`；历史报告归入 `docs/reports/archive/`；本次研究归入带日期的 `docs/research/archive/knowledge-publication-20260804/`，保留索引和 hash。完成后更新 `docs/plans/README.md`，让 plans 只保留当前入口和必要开放问题。
6. **安全清理**：只清理经引用扫描确认可重建的 `.DS_Store`、`__pycache__`、`.pytest_cache`、构建元数据和已确认无活跃任务的工具缓存；`.venv`、`.opencode/node_modules`、`.omc`、`.multica`、`.worker-mode` 等先标注用途和归属，再决定删除或保留。禁止宽泛递归删除，禁止删除仍被 config/evidence/test 引用的文件。
7. **收口检查**：验证 README 命令、文档链接、配置引用、脚本引用、测试引用、Git 跟踪状态、目录 allowlist 和归档映射；清理后保留可恢复记录，不能用“目录变小”代替证据。
8. **便携性检查**：活跃配置和 README 不得依赖 `/Users/Hugh` 等本机绝对路径；`config/knowledge-digest.json` 的 calibration artifact 改为相对路径或 example 配置，历史报告中的绝对路径只作为历史证据保留并标注。

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
5. 活跃 README、AGENTS、CONTEXT、config 和 docs index 不包含 `/Users/Hugh`、临时下载目录或凭据；历史报告中的绝对路径必须明确标为历史证据。
6. inventory 覆盖 tracked/untracked/ignored 目标，逐项有分类、理由、引用和动作；`active`、`archive`、`rebuildable`、`delete-after-confirmation`、`unknown` 五类没有遗漏。
7. 原始设计、ADR、有效验收 fixture、`evidence/phase4` 和仍被引用的配置/脚本均保留；归档文件有索引、旧路径映射和 hash；研究材料不再散落在活跃入口层，`docs/research/`、`docs/reports/`、`specs/archive/` 各有唯一可发现入口或明确指向已有等价索引。
8. 可重建缓存和确认无引用的临时产物才被清理；清理后没有未解释的生成物，`.venv` 等仍需保留的本地环境必须在 inventory 中说明。
9. `uv run pytest tests/ -q`、README 中的离线 smoke、文档链接检查和目录 allowlist 检查通过；Task 3-Closeout 不改变 Task 0–3 的行为验收结果。
10. 若 Task 3 是 `not_released`，README、AGENTS 和最终报告必须如实写明；文档收口不能把失败结果改写成 `released`。

## 8. 全局质量门

### 8.1 机器门

- manifest、snapshot、ledger 来源集合闭合；Claim、duplicate、history 幂等；S6 在写回前完成；
- batch size 1/20、输入顺序和重复运行的 TopicIndex 成员、topic key 和正式路径一致；相同 key 不得出现多个主题；
- ProductGazetteer 有 seed、owner、版本、alias、匹配优先级和冲突记录；未知项只能进入 degraded/候选提案；
- 正式页有产品、模块、page type 和可读标题；禁止 hash、裸短名和通用占位；overview 不能是空壳；
- 每个正文引用都能解析稳定 `claim_id → source_uri/content_hash/locator`；数字、标识符和版本不漂移；
- 正文与 Evidence 分离，正文 section 按 page type 完整，正文 ≤120 行、整页 ≤300 行；
- 超长主题按语义边界拆分，Claim 不丢失、不重复，主题总览和 `prev/next` 可达，`part-1` 不能代替主题入口；
- provider 失败、JSON 破损、事实冲突、无 body、无归属来源不得进入 formal 导航；
- 显式 `--no-llm + Jaccard` 可作为离线基线；每次运行只使用一个 similarity backend。语义模式若按既有合同回退 Jaccard，manifest/status 必须显示 fallback，且语义发布整包不得标 released；
- 相关链接有结构证据且双向；无关系时省略；
- Home、分类、来源入口无空页和断链；旧 formal 路径稳定或有真实 redirect/alias 映射；
- 正式托管页的 hash 与上次生成 hash 不一致时不得静默覆盖，必须冲突/degraded；affected set 外正文和路径字节不变；
- Reader/Audit 包按 allowlist 分离；`--no-llm` 网络调用数为 0。

### 8.2 读者门

- Task 0 冻结的 17 个正向真实问题 + 3 个负向问题有原文、入口、期望主题/产品、覆盖角色、负向设计、seed、评审人和 hash；Task 2 只运行样本可答子集，Task 3 运行全量题集；
- 正向首次命中 ≥15/17，负向误命中 0/3；
- 每次跳转都说明当前页面的用途、边界和下一步；不把“最多四跳”作为硬指标；
- 标题脱离路径可理解 ≥90%；产品/模块归属准确率 ≥90%；评分规则、样本量和评审人可追溯；
- 页面不打开原始档案也能回答是什么、怎么用、限制/异常、版本和来源；
- 人工评分表记录题目、入口、首次命中页面、是否正确、错误原因、评审人、日期和抽样种子；
- `agent_assisted` 不能冒充 `human_reviewed`；人工门是一次性发布验收，不创建永久人工队列。

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
Task 2
  └─ 退出物：三类编译器、12–20篇样本、读者评分表、机器门证据
       ↓
Task 3
  └─ 退出物：89篇 Reader/Audit 包、全量对比报告、人工验收记录
       ↓
Task 3-Closeout
  └─ 退出物：AGENTS.md、CONTEXT.md、README.md、清理/归档 inventory、收口报告
```

任一任务未达到退出物，不得进入下一任务。每个任务必须同时保存代码、测试、输入 manifest、样本产物、审计报告和回滚说明。

Task 0 退出时必须额外冻结题集、状态定义、包 allowlist、语义/离线运行区分和预算字段；Task 1 退出时必须关闭词典存储位置、规范化规则、匹配优先级和 affected set；Task 2 退出时必须关闭三类 page contract、必需/可选 section、claim-id 和抽样蕴含合同；Task 3 退出时必须冻结最终实际命令、输出目录和发布状态。Task 3-Closeout 只做文档同步、清理和归档，不重新打开前面任务的业务决策。

## 10. 需求追踪矩阵

| 需求 | 证据来源 | 实施任务 | 关键验收 |
|---|---|---|---|
| 不丢来源且可回查 | 原始设计 S1/S5/S6；provenance 调研 | Task 0/2/3 | manifest/Claim/locator 闭合 |
| 不把批次当主题 | S2/S3 调研；三方盲审 | Task 1 | batch 1/20 TopicIndex 一致 |
| 产品/模块语义主轴 | CompanyBrain IA/reader；盲审 | Task 1/3 | 产品归属 ≥90%，无空主轴 |
| 正文可读而非 Evidence dump | content 调研；Opus 盲审 | Task 2 | 三类 page contract、无占位、claim-id 回指 |
| 失败不伪装成功 | output audit/provenance；pi 盲审 | Task 0/3 | `degraded` 隔离、旧 formal 不覆盖 |
| 支持增量稳定更新 | 原始设计目标；盲审 | Task 1/3 | 只重编译受影响主题、路径稳定 |
| 读者能完成真实任务 | CompanyBrain reader；本 PRD | Task 2/3 | 15/17 正题命中、0/3 负题误命中 |
| 交付目录易懂 | navigation 调研；CompanyBrain | Task 0/3 | Reader/Audit 分包、无空页断链 |
| 题集和发布状态可重放 | 三方盲审；本 PRD | Task 0/3 | 17+3 题集 hash、released/not_released 可验证 |
| 语义调用可控且安全 | 三方盲审；AGENTS.md | Task 0/3 | allowlist、预算、超时、凭据不落盘 |
| 人工修改不被覆盖 | 三方盲审；增量风险 | Task 1/3 | hash 冲突隔离、旧路径可达 |
| 项目可交接 | 用户新增要求；本 PRD §6.7 | Task 3-Closeout | 根 README/AGENTS/CONTEXT 与实现一致 |
| 仓库可维护且可恢复 | 项目清理审计；原始归档原则 | Task 3-Closeout | inventory、引用扫描、归档索引、无未解释生成物 |
| 不引入重设施 | 原始非目标；OSS 调研 | 全部 | 无 DB/图谱/调度器/AgentMemory |

## 11. 新任务启动规则

1. 新任务标题必须明确对应 `Task 0`、`Task 1`、`Task 2`、`Task 3` 或 `Task 3-Closeout`，不得把四个核心任务重新混成一个“全面重构”。
2. 新任务先读取本 PRD、对应研究文件和现有 `AGENTS.md`，再写任务自己的 spec/plan；不重新发明目标。
3. 任务开始前冻结输入范围、代码基线和不改动的旧产物；真实语料必须复制到新的 KB 目录。
4. 先写能复现问题的 acceptance 测试，再做最小代码修改；完成后先跑相关测试，再跑完整测试和对应读者验收。
5. 离线验证使用 `--no-llm + Jaccard`，必须证明没有网络调用；语义发布需要单独记录 provider/model/参数和失败，不把二者混为一类证据。
6. 只有 Task 3 的机器门、人工读者门和交付门都通过，才可以把整包标为 `released`；页级仍分别记录 `published/degraded`，整包未通过时明确写 `not_released`，保留失败证据。
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
- **Task 2**：三类 page contract 的 frontmatter/section 字段、必需与可选 section、`claim_id` canonical 算法、正文引用语法、蕴含抽样 seed/阈值和语义分页边界。
- **Task 3**：完整题集评分表、标题/归属抽样规则、provider/model/config 固定值和对比报告字段。
- **Task 3-Closeout**：根 README 的命令 smoke、AGENTS/CONTEXT 的字段核对、inventory 分类、归档目标、`.gitignore` 补充和是否保留本机工具目录的最终决定。

reader 来源入口固定为 `indexes/sources.md`；旧 `_digest/source-index.md` 只能作为同一事实源生成的兼容投影。所有选择必须保持“单一事实源、文件化、可回滚、可追溯”，不能重新打开产品范围。

## 14. 最终决策

本项目接下来不是继续修补 Task2 的文件命名，而是按 Task 0–3 加 Task 3-Closeout 完成一个小型、可验证的知识发布层：

```text
先让系统诚实
→ 再让主题有主轴
→ 再让正文能独立阅读
→ 最后做全量发布和人工验收
→ 再完成文档同步、清理和可恢复归档
```

完成标准不是“生成了更多 Markdown”，而是：来源没有丢、失败没有伪装、页面有产品和模块语义、正文能回答真实问题、用户默认打开的目录干净，维护者能按三份文档接手项目，历史证据可追溯且没有未解释的仓库垃圾。
