# 功能规格：Task 2-A — OKF-compatible Reader Bundle 基础（Concept Contract v1-draft）

> 基于已接受的需求来源（PRD §6.8/§6.9 + decision-log D1–D3）。本文件只写产品问题、行为、边界和验收，不写实现符号、工程命令或代码路径。
> `content_profile: "spec-content.v3"`

- **功能名**：OKF-compatible Reader Bundle（结构合同阶段）
- **来源**：`docs/plans/knowledge-digest-knowledge-publication-prd.md` §6.8、§6.9、Task 2-A 章节；`specs/task2a-knowledge-publication-reader-bundle/decision-log.md`（accepted，用户回答 "A"×3 + 最终确认）
- **状态**：草稿（本阶段产出 v1-draft，经审查与工头接受后由下游冻结）

## 0. 当前材料修订说明

- 本版是 `build-spec` 首版起草，后经 D-004 scope revision 回到计划/实现阶段，补齐既有字段合同中的确定性正向机器信号；没有新增页面类型、provider、人工读者门或发布范围。
- 决策来源：D1（结构合同和离线边界）、D2（承诺 OKF-compatible，vendored 固定版本 parser，失败自动降级）、D3（三类 fixture 用 20 个真实样本挑片段人工整理）、D-004（补齐可由现有证据证明的正向信号）。
- 影响材料：`decision-log.md` 全部决定；`plan.md`、`tasks.md` 增加信号投影 Phase；现有结构 Phase 的历史证据只读保留。
- v1-draft（审查后）：wh-review 正式 pass（1/1 有效独立审查方，无 findings），spec 无需修改；finding 处置表见 `wh-review-disposition.md`。保持冻结态，等待工头接受后交 build-plan。

## 1. 速读卡（30 秒）

- **一句话需求**：把 Reader Package 升级为可被人、Agent 和普通 Markdown 工具直接消费的 OKF v0.2-compatible bundle，本轮交付结构合同及其可证实的正向机器信号（生成、机器门、来源/Claim 回查、新鲜度显式投影），不编译正文语义或人工读者门。
- **核心改动点**：
  - 定义 OKF-compatible Reader Bundle 布局与豁免文件清单。
  - 定义三类 concept type、frontmatter 合同、`digest_*` 扩展字段与三层状态映射。
  - 引入固定版本 PyYAML `safe_load/safe_dump` 与受管 hash 规则，未知扩展字段 round-trip 保留。
  - 建立无 LLM 结构验证器与零网络外部 OKF parser smoke。
- **最大影响面**：现有 `navigation.py`、`publication.py`、`page_layout.py`、`provenance.py` 的 Reader 输出形态；后续 Task 2-B/2-C/3 全部复用本 bundle 合同。
- **验收信号**：8 条验收标准全部可判真假；正向 machine signal 有对应 audit evidence；没有人工/语义核验时不生成 `human:`、`critical_token_recheck` 或 `sampled_entailment`；包级状态保持 `not_released`；parser smoke 不通过则对外名称自动降级为 `OKF-inspired profile`。

## 2. 来源与决策映射

| Source ID | Decision ID | FR / AC IDs | Status / affected scope | Unresolved / handoff |
| --- | --- | --- | --- | --- |
| R-001（只做结构合同） | D1 | FR-BUNDLE-001/002/003/005/006、FR-PROJ-001/002、FR-LLM-001、AC-01/05/07 | current / 全部产物形态 | 正文语义 → Task 2-B |
| R-002（type + 未知扩展字段） | D1 | FR-FRONT-001/003/004/006、AC-02/06 | current / frontmatter 合同 | 无 |
| R-003（PyYAML 安全解析） | D1 | FR-FRONT-002、AC-02/06 | current / 依赖与序列化 | 具体版本号 → build-plan/code |
| R-004（claim_id/sources[].id/footnote） | D3 | FR-ATTR-001/002、FR-FIX-001/002、AC-03 | current / 归因合同 | 具体样本片段 → build-code（OPEN-02） |
| R-005（三层状态映射） | D1 | FR-STATUS-001/002/003、AC-04 | current / 状态合同 | 无 |
| R-006（无 LLM 验证器 + 人工 fixture） | D1/D3 | FR-VALID-001/002、FR-FIX-001、AC-03/05/06 | current / validator 与 fixture | 无 |
| R-007（外部 parser smoke） | D2 | FR-SMOKE-001/002、AC-08 | current / 互操作承诺 | 具体 commit → build-code（OPEN-01） |
| R-008（8 条验收 + not_released） | D1 | AC-01–AC-08、FR-PROJ-002、FR-LLM-001 | current / 验收与交付状态 | 无 |
| R-009（不做全量/LLM/正文/OKF runtime） | D1 | §12 明确不做全部条目、AC-05/07 | non-goal / 边界 | 无 |
| F-001（OKF 官方结构调研） | D2 | PFACT-002、FR-SMOKE-001 | current / 外部事实 | 无 |
| F-002（入口 backfill 与样本） | D1/D3 | PFACT-001/003/004、FR-ENTRY-001、FR-FIX-001 | current / 入口事实 | RISK-04/05 |
| F-003（§6.9 冻结决定） | D1/D2 | FR-FRONT-004/005、FR-STATUS-001/002、FR-SMOKE-002、AC-02/04/06/08 | current / 合同修正 | RISK-03 |

## 3. 问题与紧迫性

Task 1 已产出 `_digest/source-inventory.jsonl`、`topic-plan.json`、`topic-index.json` 等编译控制面，但它们不是读者知识产品。若直接进入 LLM 正文编译，仍会得到私有路径、重复 frontmatter、孤立索引、无法过滤信任/新鲜度的 Markdown。OKF v0.2 提供了合适的文件层：Markdown + YAML frontmatter、渐进式 `index.md`、标准来源字段、生成/验证事件、生命周期和标准链接。本轮必须先固定文件合同，否则 2-B/2-C/3 全部输出形态无法一致，语义编译会在不稳定的结构上放大问题。

## 4. 背景、目标与范围

### 背景

- OKF 定位：可移植文件格式和元数据约定，不是运行时、固定本体或质量评分器；本项目只采用格式层。
- 现有底座：S1–S6 保真层、Task 0 诚实化与交付包、Task 1 稳定主题身份（TopicIndex/ProductGazetteer）已完成；入口 backfill 已通过（`task2a_entry_allowed=true`）。
- Reader Bundle 与 Reader Package 是同一产品线的两代形态：Bundle 是 Package 的 OKF-compatible 升级版，不是两套产品；旧 `indexes/sources.md` 不迁移、不重写（CONTEXT.md「Reader Bundle」）。

### 目标

- 交付一个可被外部固定版本 OKF parser 零网络读取的样本 bundle，含三类 concept fixture。
- 冻结 Concept Contract v1-draft：布局、frontmatter 合同、豁免清单、状态映射、hash 规则、归因合同。
- 产出 Task 1 TopicIndex → Reader Bundle 的确定性投影报告。
- 全部产物包级状态 `not_released`，零 LLM 调用。

### 范围内

- Reader Bundle 正式布局与豁免文件清单。
- 三类 concept type 与 `knowledge_type → digest_page_type → OKF type` 固定映射。
- frontmatter 合同、`digest_*` 扩展字段、三层状态映射、受管 hash 规则。
- 无 LLM 结构验证器需求。
- 三个手工 fixture（产品总览、模块能力、流程规则各一）的归因验证。
- 固定版本零网络外部 OKF parser smoke 与降级路径。
- Task 1 TopicIndex → Reader Bundle 确定性投影报告。
- 页面级 `generated`、`digest_machine_pass`、`source_hash_match`/`locator_resolved` 正向事件和有明确 freshness 证据时的 `stale_after` 投影；信号只来自同一 audit/Claim/source 输入，不新增事实源。

## 5. 用户场景与状态覆盖

### SCN-001：生成 OKF-compatible 样本 bundle

- **角色**：操作者（维护者）
- **Given**：入口验收通过（Task0/Task1 exit manifest 可用且 hash 一致），20 个真实样本可用
- **When**：用 `--no-llm` 在隔离 fixture 上运行 bundle 生成
- **Then**：产出 `README.md`、`Home.md`、根 `index.md`、根 `log.md`、`products/<product>/...` 层级和 `references/sources.md`；根 `log.md` 含状态与本次变更摘要；包级 manifest `not_released`；零网络调用

### SCN-002：fixture 正文归因可反查

- **角色**：读者/Agent（bundle 消费者）
- **Given**：一个已生成的概念页正文含标准 Markdown footnote `[^src-abc]`
- **When**：按 footnote 查找同页 frontmatter 的 `sources[].id`
- **Then**：经唯一的 `digest_claims[].claim_id + fragment_locator` 反查到稳定 Claim、source URI 和内容指纹；审计包可反查完整 Claim/Evidence

### SCN-003：无 module 归属但有 product 归属

- **角色**：操作者
- **Given**：某 concept 有明确 product 归属但没有 module 归属
- **When**：生成 bundle
- **Then**：concept 直接放在 `products/<product>/` 下，不臆造 module；该产品没有真实 module concept 时不生成 `modules/` 目录或 `modules/index.md`；无 product 归属或冲突的 concept 进入 `degraded`，不进正式导航

### SCN-004：外部 parser smoke 失败

- **角色**：操作者
- **Given**：vendored 固定版本 OKF parser 无法通过零网络读取样本 bundle
- **When**：执行 smoke
- **Then**：产物名称与文档自动降级为 `OKF-inspired profile`，根 `index.md` 省略 `okf_version` 字段，exit manifest 记录降级原因；不宣称 OKF-compatible

### SCN-005：入口 manifest 缺失或 hash 不一致

- **角色**：操作者
- **Given**：Task0/Task1 exit manifest 缺失、过期或 hash 不一致
- **When**：执行入口验收
- **Then**：生成 backfill manifest，包保持 `not_released`，不得进入正文编译；补齐后重跑受影响的 Task0/Task1 机器门

### SCN-006：未知扩展字段 round-trip

- **角色**：维护者（外部工具接入者）
- **Given**：concept frontmatter 含本项目不认识的自定义扩展字段
- **When**：经过 YAML parse → write → parse
- **Then**：扩展字段语义不丢失，`sources/generated/verified` 等嵌套结构不被扁平化

### SCN-007：同一输入重复运行

- **角色**：操作者
- **Given**：同一 TopicIndex 与输入
- **When**：重复运行两次
- **Then**：路径、index 内容和受管 frontmatter/hash 字节稳定；`generated.at`、verified 追加与 manifest release 状态按易变字段规则处理

### 状态覆盖清单

- [ ] **默认态**：SCN-001 / SCN-002
- [ ] **空态**：SCN-003（无 module 不生成 modules/）；空目录不生成空 index（FR-BUNDLE-001）
- [ ] **错误态**：SCN-004（smoke 失败降级）、SCN-005（入口缺失 backfill）
- [ ] **加载态**：N/A — 本地文件批处理，无用户可见加载
- [ ] **取消态**：N/A — 人工触发单次运行；失败只保留 audit/fixture，不覆盖旧正式结果
- [ ] **边界态**：SCN-006（未知扩展字段）、FR-FRONT-006（标题/描述无候选 → degraded）、FR-BUNDLE-005（非 products 类型只进 degraded）
- [ ] **权限态**：N/A — 本地单写者，无用户权限体系；凭据不进入产物
- [ ] **竞态**：SCN-007（重复运行幂等，单写者边界）

## 6. 产品事实与假设（PFACT）

- **PFACT-001**：Task 2-A 入口验收已通过（`task2a_entry_allowed=true`，`task2b_body_compilation_allowed=false`）
  - **status**：`verified`
  - **证据**：`quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json`（backfill，provenance_mode=recomputed_backfill，包状态 not_released）
  - **关联**：FR-ENTRY-001、AC-02
- **PFACT-002**：OKF 官方 bundle parser（document.py/index.py/paths.py）是纯 Python、Apache-2.0、可离线运行；官方仓库本次读取 commit `930b65fc3f5619d5d0591f88c72ebae8b848d60d`
  - **status**：`verified`
  - **证据**：`docs/research/20260806-okf-structure-research.md`（F-001）
  - **关联**：FR-SMOKE-001/002、AC-08
- **PFACT-003**：20 个真实样本可用（7 个 published、13 个 degraded，覆盖 2 个产品、7 个模块；含多源与失败/degraded 类别）
  - **status**：`verified`
  - **证据**：`quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`
  - **关联**：FR-FIX-001、AC-03
- **PFACT-004**：当前 89 条来源 `knowledge_type` 全部为 `products`
  - **status**：`verified`
  - **证据**：`task2-entry-sample-coverage.v1.json#inventory_coverage`（products: 89）
  - **关联**：FR-FRONT-003、FR-BUNDLE-005
- **PFACT-005**：Task 2-A 只生成 `not_released` 的 bundle projection；Task 0–2-C 均不能把整包标为 `released`
  - **status**：`verified`
  - **证据**：PRD §6.6、§6.8（冻结合同）
  - **关联**：FR-PROJ-002、FR-LLM-001、AC-07
- **PFACT-006**：现有项目只有 YAML-like 简单 frontmatter 解析，不满足嵌套 OKF frontmatter 的 round-trip 需求
  - **status**：`verified`
  - **证据**：PRD §6.8 实施要点 3（R-003）
  - **关联**：FR-FRONT-002、AC-06
- **PFACT-007**：具体固定的 OKF parser commit 尚未挑选
  - **status**：`unknown`
  - **owner/影响**：build-code 决定；影响 smoke 可重放性与命名承诺
  - **关联**：FR-SMOKE-001/002、AC-08、OPEN-01
- **PFACT-008**：三类 fixture 具体选取哪些真实样本片段尚未决定
  - **status**：`unknown`
  - **owner/影响**：build-code 决定并说明选样理由；影响 fixture 内容与归因验证真实性
  - **关联**：FR-FIX-001/002、AC-03、OPEN-02
- **PFACT-009**：Task1 历史 receipt 与重算 backfill 的冲突未最终关闭
  - **status**：`inferred`
  - **来源与限制**：`quality/evidence/task2-entry/task1-receipt-reconciliation.v1.json`；审计债，不影响本轮控制面投影（fresh backfill 为权威）
  - **关联**：FR-ENTRY-001、RISK-04
## 7. 功能需求

### Reader Bundle 布局（BUNDLE）

Reader Bundle 是读者打开知识产品的默认形态。布局固定为 `README.md → Home.md → 根 index.md → 根 log.md → products/<product>/... → references/sources.md`；Home、Reader README 与来源投影是明确声明的入口/索引豁免文件，只做渐进式披露，不维护第二套目录事实。

- **FR-BUNDLE-001**：Reader Bundle 必须包含 `README.md`、`Home.md`、根 `index.md`、根 `log.md` 和 `products/<product>/...` 层级；`log.md` 是必选根文件，至少包含状态和本次变更摘要；嵌套目录不生成 `log.md`；空目录不生成空 index
  - **范围边界**：`README.md` 是本次结果说明（不是项目根 README）；`Home.md` 只指向根 `index.md`；`index.md`/`log.md` 是 OKF 保留文件名，不能当普通 concept 页；嵌套 `index.md` 和 `log.md` 不放 frontmatter
  - **依据**：D1；PRD §6.8；PFACT-001
  - **场景**：SCN-001
  - **验收**：AC-01
- **FR-BUNDLE-002**：`Home.md`、Reader `README.md`、`references/sources.md` 是豁免文件，不是 concept，不放 concept frontmatter；validator 必须硬编码这份豁免清单并强制校验
  - **范围边界**：豁免只适用于这三个文件；其余 `.md` 均按 concept 或 index/log 规则处理
  - **依据**：D1；PRD §6.8；CONTEXT.md「Reader Bundle」
  - **场景**：SCN-001
  - **验收**：AC-01/AC-06
- **FR-BUNDLE-003**：`Home.md` 只能指向根 `index.md`；Reader `README.md` 只说明本次结果；`references/sources.md` 只由同一 audit records 投影生成；三者都不能维护第二套目录或来源事实；根 `index.md` 是唯一 canonical 渐进式目录
  - **范围边界**：来源全量状态唯一事实源是 audit manifest；`references/sources.md` 是轻量来源投影，不放完整审计快照
  - **依据**：D1；PRD §6.8/§6.9.3
  - **场景**：SCN-001
  - **验收**：AC-01/AC-05
- **FR-BUNDLE-004**：只有 parser smoke 通过并且 bundle 宣称 OKF-compatible 时，根 `index.md` 才能声明 `okf_version: "0.2"`；降级为 `OKF-inspired profile` 时必须省略该字段
  - **范围边界**：嵌套 `index.md` 不声明 `okf_version`；降级决定必须在实现前完成，不能在 Task 3 临时决定
  - **依据**：D2；PRD §6.8/§6.9.7/§6.9.8
  - **场景**：SCN-004
  - **验收**：AC-08
- **FR-BUNDLE-005**：无 module 归属但有明确 product 归属的 concept 直接放在 `products/<product>/`，不得臆造 module；无 product 归属或冲突时进入 `degraded`，不进正式导航；`modules/index.md` 只有在该产品至少有一个已发布 module concept 时才生成；只有产品级 concept 时不生成空的 `modules/` 目录或索引
  - **范围边界**：`knowledge_type=products` 之外的类型只进 Audit 的 degraded 记录，不生成 Reader 路径、索引或 concept
  - **依据**：D1；PRD §6.8
  - **场景**：SCN-003
  - **验收**：AC-02/AC-05
- **FR-BUNDLE-006**：目录索引只做渐进式披露：每个 `index.md` 列出真实子目录/概念的可读标题和一行 description，不生成空分类、不把 hash 作为标题、不把所有正文塞进索引
  - **范围边界**：概念间关系用标准 Markdown links 表达，关系类型写在链接附近自然语言中，不得凭相似度臆造
  - **依据**：D1；PRD §6.8
  - **场景**：SCN-001
  - **验收**：AC-01/AC-05

### frontmatter 合同（FRONT）

每个 concept 是带 YAML frontmatter 的 Markdown 文件；frontmatter 是读者/Agent 打开正文前先读的信号层。

- **FR-FRONT-001**：每个 concept 的 frontmatter 至少有 `type`，并按需使用 `title`、`description`、`tags`、`sources`、`generated`、`verified`、`status`、`stale_after`；未知扩展字段必须保留，不能因不认识而丢弃
  - **范围边界**：字段形状以 PRD §6.8 概念字段示例为准；本项目扩展字段统一 `digest_` 前缀
  - **依据**：D1；PRD §6.8；PFACT-006
  - **场景**：SCN-006
  - **验收**：AC-06
- **FR-FRONT-002**：必须采用固定版本的安全 YAML 解析/序列化依赖（PyYAML），只使用 `safe_load/safe_dump`，禁止用手写行解析伪装嵌套 OKF frontmatter；key 排序、Unicode、缩进、折行参数必须固定
  - **范围边界**：具体版本号与参数由 build-plan/code 冻结并在 manifest 记录；不影响产品行为
  - **依据**：D1；PRD §6.8 实施要点 3；PFACT-006
  - **场景**：SCN-006
  - **验收**：AC-02/AC-06
- **FR-FRONT-003**：固定三类正式 concept `type`：`KnowledgeDigest Product Overview`、`KnowledgeDigest Module or Capability`、`KnowledgeDigest Procedure or Rule`；`knowledge_type → digest_page_type → OKF type` 必须是固定映射表，不允许按页面标题临时猜测；未映射即 `degraded`
  - **范围边界**：validator 对外部 OKF bundle 的未知 type 只做兼容读取并保留，不把 OKF 开放 type 规则误写成项目正式页可随意扩展
  - **依据**：D1；PRD §6.8/§6.9.2
  - **场景**：SCN-003
  - **验收**：AC-02
- **FR-FRONT-004**：concept 页只保留 `digest_topic_key`、`digest_topic_id`、`digest_page_type`、`digest_page_status`、`digest_machine_pass`、`digest_content_hash` 等 `digest_*` 扩展字段；包级 `digest_release_status` 只在 manifest 存在，不写入 concept 页
  - **范围边界**：`digest_topic_key` 是 Task 1 已产出的 `v2/<knowledge_type>/<product>/<module>/<object_intent>`；`digest_topic_id` 重放稳定
  - **依据**：D1；PRD §6.8/§6.9.3/§6.9.4
  - **场景**：SCN-007
  - **验收**：AC-02/AC-04
- **FR-FRONT-005**：`digest_content_hash` 只覆盖受管 frontmatter 业务字段（`type/title/description/tags/sources/status/stale_after/digest_topic_key/digest_topic_id/digest_page_type`）与正文；明确排除 `digest_content_hash` 自身、`generated.at`、`verified`、`digest_machine_pass`、`digest_page_status`、包级 release manifest 和 audit/runtime 字段
  - **范围边界**：YAML key 顺序、Unicode、缩进、折行参数必须固定，保证 hash 可重放
  - **依据**：D1；PRD §6.9.4
  - **场景**：SCN-007
  - **验收**：AC-06
- **FR-FRONT-006**：标题按「既有托管标题 → 来源 frontmatter/显式 metadata title → 可解析 H1 → 可读文件名」的顺序选择，并做固定空白、标点和 slug 归一；没有可读候选时页级 `degraded`。描述按「来源显式 description/summary → 确定性抽取的首个有意义句子」选择，不得写泛化占位语；目录索引只能投影 concept 的描述
  - **范围边界**：标题/描述要求适用于本项目 Reader fixture，不把 OKF 外部输入的可选字段误改成通用 OKF 硬要求；ProductGazetteer/TopicIndex 直接产生的标签属于 metadata，不需要伪造正文事实归因
  - **依据**：D1；PRD §6.8
  - **场景**：SCN-003
  - **验收**：AC-02

### 状态映射（STATUS）

状态三层分开，不混义；每层各有合法取值与产出位置。

- **FR-STATUS-001**：`status` 只表达 OKF concept 生命周期（`stable`/`draft`/`deprecated`）；页级 `published/degraded` 只放在 `digest_page_status`；包级 `released/not_released` 只放在 manifest 的 `digest_release_status`
  - **范围边界**：`degraded` 不属于 Reader Bundle 导航树，只进 Audit/Archive 的 `_digest/degraded/`；`status=deprecated` 保留旧链接与历史，不作为新工作默认入口
  - **依据**：D1；PRD §6.8/§6.9.3
  - **场景**：SCN-001
  - **验收**：AC-04
- **FR-STATUS-002**：`verified` 只记录真实的来源/内容回查或独立人工核验；机器 `verified` 只允许 `source_hash_match`、`locator_resolved`、`critical_token_recheck`、`sampled_entailment` 四类事件，actor 固定为 `process:knowledge-digest-<event>-<detector_version>`，工具事件用 `<producer>/<version>`；`agent_assisted` 不能写成 `human:` actor；结构 lint、provider 成功、写回成功都不能产生 `verified`；任何受管内容/归因/page type 变化使旧 `verified` 失效
  - **范围边界**：`human:<id>` 必须能回查人工记录；没有对应证据禁止产生 `machine-confirmed` 或 `human-reviewed`
  - **本轮实现边界**：D-004 只实现 `source_hash_match`、`locator_resolved` 两类确定性机器事件，以及 `generated`/`digest_machine_pass` 投影；`critical_token_recheck`、`sampled_entailment`、`human:`、`agent_assisted` 和人工 reader gate 留到 Task 2-C。
  - **依据**：D1；PRD §6.8/§6.9.5/§6.9.11/§6.9.12
  - **场景**：SCN-002
  - **验收**：AC-04
- **FR-STATUS-003**：`stale_after` 只在来源明确提供可审计的有效期/复核日期时写入；没有证据就省略，不猜 TTL；过期不自动删除，读者过滤和审计报告分别处理
  - **范围边界**：版本 oracle 固定为「既有托管 metadata → 来源 frontmatter/显式 metadata → 明确的版本标题/字段」；多个不一致版本或无法解析时页级 `degraded`
  - **依据**：D1；PRD §6.8/§6.9.14
  - **场景**：SCN-001
  - **验收**：AC-04

### 来源归因合同（ATTR）

正文归因与审计身份分离，全部可反查。

- **FR-ATTR-001**：`sources[].id` 是正文 attribution key；fixture 正文用标准 Markdown footnote（如 `[^src-abc]`）指向同一页面 frontmatter 的 `sources[].id`；每个归因最终只解析到一个 `digest_claims[].claim_id` 和 `fragment_locator`
  - **范围边界**：`claim_id` 继续是 audit Claim 身份；同一来源可有多个 source-fragment entry，但不复制正文；正文不再依赖页面底部孤立的 Evidence 列表
  - **依据**：D3；PRD §6.8；PFACT-003
  - **场景**：SCN-002
  - **验收**：AC-03
- **FR-ATTR-002**：`references/sources.md` 是阅读投影，不是脚注的第二目标，也不维护另一套 source id；完整 Claim/Evidence 继续留在 Audit Package；fixture 保留真实 source URI、内容指纹和 claim 映射
  - **范围边界**：source entry 保存 source URI、标题、内容指纹和逐 Claim 的 `digest_claims[].fragment_locator`；`sources[].id` 是稳定 source-fragment key
  - **依据**：D3；PRD §6.8/§6.9.3
  - **场景**：SCN-002
  - **验收**：AC-03/AC-05

### 无 LLM 结构验证器（VALID）

验证器只做结构合同校验，不声称语义质量。

- **FR-VALID-001**：为 bundle、正文和索引建立无 LLM 的结构验证器：frontmatter 可解析、type/豁免身份合法、title/description 可读、sources 引用可回查、index 无空入口、链接不逃逸、`index.md`/`log.md` 不被误当 concept、frontmatter 与 audit records 对账
  - **范围边界**：验证器不校验正文语义质量；fixture 只验证 attribution 结构
  - **依据**：D1；PRD §6.8 方案 6
  - **场景**：SCN-001/SCN-002
  - **验收**：AC-02/AC-06
- **FR-VALID-002**：Reader Bundle 不含 `_digest`、`_archive`、provider 原始响应和完整快照；失败、冲突、无归属或未通过质量门的页只出现在 Audit/Archive `_digest/degraded/`，不出现在 Reader 导航；标准 Markdown links 可达，关系没有由相似度臆造
  - **范围边界**：Reader 导航只含页级 `published`；degraded 页在 manifest 记录原因、输入指纹和恢复路径
  - **依据**：D1；PRD §6.8
  - **场景**：SCN-003
  - **验收**：AC-05

### 外部 parser smoke（SMOKE）

- **FR-SMOKE-001**：必须跑零网络的最小外部 OKF parser smoke：固定 knowledge-catalog 一个 commit，把最小 bundle parser（document.py/index.py/paths.py）以固定版本 vendor 进测试；exit manifest 记录 parser 来源、固定 commit、fixture bundle hash、允许的未知扩展/类型行为和预期结果
  - **范围边界**：不引入 OKF runtime、Knowledge Catalog、数据库或图服务；只 vendor 最小读取面
  - **依据**：D2；PRD §6.9.7/§6.9.8；PFACT-002
  - **场景**：SCN-004
  - **验收**：AC-08
- **FR-SMOKE-002**：smoke 不通过时，产物名称和文档不得宣称 `OKF-compatible`，必须降级为 `OKF-inspired profile` 并省略 `okf_version` 字段；降级原因写入 exit manifest
  - **范围边界**：命名承诺延续到 2-B/2-C；降级必须在实现前完成
  - **依据**：D2；PRD §6.9.7/§6.9.8
  - **场景**：SCN-004
  - **验收**：AC-08

### 三类人工 fixture（FIX）

- **FR-FIX-001**：从 20 个真实样本里挑片段，人工整理三类 fixture（产品总览、模块能力、流程规则各一），保留真实 source URI、内容指纹和 claim 映射；选样理由必须说明
  - **范围边界**：fixture 只用人工编写正文验证 attribution，不声称语义质量；真实语义正文归 Task 2-B
  - **依据**：D3；PRD Task 2-A 方案 4/6；PFACT-003
  - **场景**：SCN-002
  - **验收**：AC-03
- **FR-FIX-002**：fixture 正文中的每个关键事实 footnote 能解析到稳定 `sources[].id`，并经唯一的 `digest_claims[].claim_id + fragment_locator` 反查稳定 Claim、source URI 和 content fingerprint
  - **范围边界**：attribution 反查链路在 fixture 上验证；真实正文归因由 Task 2-B 验收
  - **依据**：D3；PRD §6.8/§6.9.10
  - **场景**：SCN-002
  - **验收**：AC-03

### 确定性投影与运行边界（PROJ）

- **FR-PROJ-001**：产出 Task 1 TopicIndex → Reader Bundle 的确定性投影报告
  - **范围边界**：报告只记录投影事实（路径、hash、状态），不做语义判断
  - **依据**：D1；PRD Task 2-A 交付物
  - **场景**：SCN-007
  - **验收**：AC-02/AC-07
- **FR-PROJ-002**：同一 TopicIndex 和输入重复运行时，路径、index 内容和受管 frontmatter/hash 稳定；未知扩展字段经过 YAML parse → write → parse 后语义不丢失，且嵌套 `sources/generated/verified` 不被扁平化
  - **范围边界**：`generated.at`、verified 追加和 manifest release 状态按易变字段规则处理
  - **依据**：D1；PRD Task 2-A 验收 6
  - **场景**：SCN-006/SCN-007
  - **验收**：AC-06
- **FR-ENTRY-001**：执行入口验收：核对 Task0/Task1 exit manifest 的相对路径、hash、版本和覆盖记录；任何缺失、过期或 hash 不一致都先生成 backfill manifest 并保持 `not_released`，不得进入正文编译；补齐后重新跑受影响的 Task0/Task1 机器门
  - **范围边界**：入口只验证样本存在、来源证据可追溯和 answerability 派生规则已冻结；不把 TopicPlan examples 当作读者质量通过
  - **依据**：D1；PRD Task 2-A「启动前入口验收」；PFACT-001/009
  - **场景**：SCN-005
  - **验收**：AC-02
- **FR-LLM-001**：`--no-llm` 运行网络调用数为 0；Task 2-A 只生成 `not_released` 的 bundle projection，不声称通过读者质量
  - **范围边界**：不调用 LLM、不探测 embedding；Jaccard 只作显式离线基线
  - **依据**：D1；PRD §6.9.15
  - **场景**：SCN-001
  - **验收**：AC-07

## 8. 模块划分

> 只写产品职责，不写实现类名。

### bundle 生成器

- **负责什么**：把 TopicIndex/audit records 确定性投影为 Reader Bundle 布局（README/Home/index/log/products/references）
- **对外提供什么**：OKF-compatible（或降级 OKF-inspired）bundle 目录树
- **依赖谁**：Task 0/1 的 audit records、TopicIndex、ProductGazetteer
- **测试边界**：重复运行字节稳定；空目录不生成空 index；豁免文件身份正确

### frontmatter writer/reader

- **负责什么**：concept frontmatter 的生成、解析、round-trip 保留未知扩展字段
- **对外提供什么**：符合合同形状的 frontmatter 字节与受管 hash
- **依赖谁**：固定版本 PyYAML 依赖
- **测试边界**：parse → write → parse 语义不丢失；嵌套不扁平化；hash 排除易变字段

### 结构验证器

- **负责什么**：无 LLM 校验 frontmatter、type、豁免身份、title/description 可读性、sources 回查、index 空入口、链接逃逸、index/log 保留名、audit records 对账
- **对外提供什么**：可判真假的验证结果与报告
- **依赖谁**：bundle 生成器与 frontmatter writer/reader
- **测试边界**：8 条验收标准中结构类条目全部可判定

### 外部 parser smoke

- **负责什么**：零网络读取样本 bundle，验证固定版本消费者兼容
- **对外提供什么**：pass/fail 事实与 exit manifest 记录
- **依赖谁**：vendored 固定版本 OKF parser（最小读取面）
- **测试边界**：smoke 通过才能宣称 OKF-compatible

## 9. 关键实体

- **Concept（概念页）**：
  - **定义**：Reader Bundle 中的正式知识页，frontmatter + 结构化 Markdown 正文
  - **字段和约束**：`type` 必填（三类固定值之一）；`title/description/tags/sources/generated/verified/status/stale_after` 按需；`digest_topic_key`（v2）、`digest_topic_id`、`digest_page_type`、`digest_page_status`、`digest_machine_pass`、`digest_content_hash`；未知扩展字段保留
  - **关系**：`sources[].id` 供正文 footnote 归因；`digest_claims[].claim_id` 关联 Audit Claim；路径归属 products/<product>[/modules/<module>]
- **Source entry（来源条目）**：
  - **定义**：concept frontmatter 中一个来源的记录
  - **字段和约束**：`id`（稳定 source-fragment key）、`resource`（source URI）、`title`、`digest_content_fingerprint`、`digest_claims[].claim_id + fragment_locator`；不复制完整原文
  - **关系**：正文 footnote → `sources[].id` → 唯一 claim_id + locator → Audit Claim/Evidence
- **Reader Bundle（包）**：
  - **定义**：一次生成的 OKF-compatible 目录树
  - **字段和约束**：根 `index.md` 仅在 smoke 通过时声明 `okf_version: "0.2"`；包级 `digest_release_status` 只在 manifest；豁免文件（Home/README/references/sources.md）不含 concept frontmatter
  - **关系**：`index.md` 是唯一 canonical 导航；audit manifest 是来源全量事实源

## 10. 数据和生命周期

- **数据粒度**：一次 bundle 生成 = 一个样本包；每个 concept 一条记录
- **数据时效**：`generated.at` 记录本次生成；`stale_after` 仅在来源提供有效期时写入；verified 事件随内容变化失效
- **缺失或迟到**：入口 manifest 缺失 → backfill + `not_released`；标题/描述无候选 → 页级 `degraded`
- **预览与正式**：Task 2-A 全部样本包为 `not_released` 预览；Reader 导航只含页级 `published`
- **当前与历史**：重复运行不删除旧产物；只追加；旧 Reader/Audit 产物不删除；`_digest/degraded/` 保留恢复路径
- **归属与清理**：产物只在隔离 fixture 中生成；不写入正式知识库；profile 输出是可重建投影，失败只保留 audit/fixture

## 11. 兼容性预留

- **既有消费方**：旧 Reader Package 产物不迁移、不重写；旧 `indexes/sources.md` 保留，新投影路径为 `references/sources.md`
- **命名预留**：OKF-compatible 承诺延续 2-B/2-C；无法固定 parser 时降级 OKF-inspired，省略 `okf_version`
- **容器预留**：未知扩展字段 round-trip 保留，嵌套不扁平化；外部 OKF 未知 type 兼容读取
- **状态预留**：三层状态（status/digest_page_status/digest_release_status）独立取值，互不混义；`digest_release_status` 不写入 concept 页，避免 Task 3 质量门后变更页面字节
- **扩展边界**：本轮承诺结构合同和 D-004 已明确的页面级确定性机器信号；正文语义与语义验证（2-B）、人工读者门（2-C）、全量发布（3）仍不属于本轮

## 12. 明确不做与默认必须成立

### 明确不做

- 不做全量 89 篇正文编译（R-009，D1，阶段性质：归 Task 2-B）
- 不调用 LLM、不探测 embedding（R-009，D1，阶段性质：本轮全部运行）
- 不重写正文语义（R-009，D1，阶段性质：归 Task 2-B）
- 不引入 OKF runtime、Knowledge Catalog、数据库或图服务（R-009，D1，永久）
- 不删除旧 Reader/Audit 产物（R-009，D1，永久）
- 不在正式知识库写包，只在隔离 fixture 生成（R-009，D1，阶段性质：本轮）
- 不新增通用 repository/service 层（R-009，D1，永久）
- 不引入 Attested Computation（R-009/PRD §6.8 信号 5，D1，永久，另开规格）
- 不把包级状态标为 `released`（R-008，D1，阶段性质：Task 3 前所有包）
- 不把结构 lint、provider 成功、写回成功、agent 辅助或 fixture 生成本身伪装成 `verified`；只实现 D-004 明确的两个机器事件
- 不实现 `critical_token_recheck`、`sampled_entailment`、`human:` 记录、人工 reader gate、trust score 或 stale TTL 猜测

### 默认必须成立

- 全部产物包级 `not_released`，不伪装成已发布（关联 FR-LLM-001、AC-07）
- `--no-llm` 零网络调用（关联 FR-LLM-001、AC-07）
- 未知扩展字段不因不认识而丢弃（关联 FR-FRONT-001、AC-06）
- 没有对应 source/Claim fingerprint 与 locator evidence 不能生成 `verified`；本轮机器 `verified` 只允许 D-004 的 `source_hash_match`/`locator_resolved`，没有人工验收不能生成 `human:` actor；没有 freshness 证据不猜 `stale_after`（关联 FR-STATUS-002/003、AC-04）
- 只有 parser smoke 通过才宣称 OKF-compatible 并声明 `okf_version`（关联 FR-SMOKE-001/002、AC-08）
- 失败、冲突、无归属页只进 degraded，不出现在 Reader 导航（关联 FR-BUNDLE-005、FR-VALID-002、AC-05）
## 13. 验收标准

- [ ] **AC-01**：Reader Bundle 有 `README.md`、`Home.md`、根 `index.md`、根 `log.md` 和产品/模块/主题层级；`log.md` 是必选根文件且至少包含状态和本次变更摘要；嵌套目录不生成 `log.md`；`index.md`/`log.md`/`README.md`/`Home.md`/`references/sources.md` 的身份符合 profile 清单；空目录不生成空 index
  - **需求**：FR-BUNDLE-001/002/003
  - **验证方法**：`--no-llm` 生成 fixture bundle 后按豁免清单逐文件核验 + acceptance 测试
  - **通过条件**：五个身份文件全部按合同出现，嵌套无 log.md，无空 index
  - **失败条件**：任一身份文件缺失/身份错误，或嵌套生成 log.md，或出现空 index
  - **证据类型**：`test` + `evidence`
- [ ] **AC-02**：Task 0/Task 1 exit manifest 的相对路径、hash、版本和覆盖记录通过入口验收；缺失项有 backfill manifest 且包保持 `not_released`；每个正式 concept 都有可解析 YAML frontmatter、非空 `type`、可读 `title`、一行 `description`；三类 type、`digest_*` 字段、Task 1 `topic_key_v2`、`digest_topic_id` 和路径一致；重复 TopicIndex/replay 得到相同 `digest_topic_id`；产品级无 module concept 不被丢弃或塞入虚构 module，只有真实 module 才有 `modules/index.md`
  - **需求**：FR-ENTRY-001、FR-FRONT-002/003/004/006、FR-BUNDLE-005、FR-PROJ-001
  - **验证方法**：入口验收脚本 + fixture 生成 + validator + 重复运行对比
  - **通过条件**：入口验收全项通过或缺失项有 backfill；所有 concept frontmatter 可解析且字段合法；replay 的 digest_topic_id 一致；无虚构 module
  - **失败条件**：入口缺失无 backfill、包状态被标为 released、任一 concept 字段非法、replay 身份漂移或出现虚构 module
  - **证据类型**：`test` + `evidence`
- [ ] **AC-03**：fixture 正文中的每个关键事实 footnote 能解析到稳定 `sources[].id`，并经唯一的 `digest_claims[].claim_id + fragment_locator` 反查稳定 Claim、source URI 和 content fingerprint；审计包能反查完整 Claim/Evidence
  - **需求**：FR-ATTR-001/002、FR-FIX-001/002
  - **验证方法**：validator 解析每个 footnote → 页内 sources[].id → claim_id + locator → Audit 记录
  - **通过条件**：全部 fixture footnote 解析且唯一归因；审计反查完整
  - **失败条件**：任一 footnote 无法解析、归因不唯一或审计反查断裂
  - **证据类型**：`test`
- [ ] **AC-04**：`generated`、`verified`、`digest_machine_pass`、`status`、`stale_after` 的语义和页/包状态分离；本轮对已有 source/Claim fingerprint 与 locator 证据生成 `source_hash_match`/`locator_resolved` 正向机器事件并写入可回查 audit evidence；没有对应证据不能生成 `verified`；没有人工验收不能生成 `human:` actor；没有 freshness 证据不猜 `stale_after`；`agent_assisted` 不能写成 `human:` actor
  - **需求**：FR-STATUS-001/002/003
  - **验证方法**：生成 fixture 后检查各字段取值、actor 约定与审计记录对应关系
  - **通过条件**：三层状态各自合法取值且位置正确；支持的机器 verified 事件有输入 fingerprint、detector version、actor 和 audit evidence；没有人工/语义证据时不出现 human/critical_token_recheck/sampled_entailment；stale_after 只有在显式 freshness evidence 存在时出现
  - **失败条件**：状态混层、verified 无真实核验、出现无记录的 human: actor 或无证据的 stale_after
  - **证据类型**：`test` + `evidence`
- [ ] **AC-05**：Reader Bundle 不含 `_digest`、`_archive`、provider 原始响应和完整快照；标准 Markdown links 可达，关系没有由相似度臆造；失败、冲突、无归属或未通过质量门的页只出现在 Audit/Archive `_digest/degraded/`，不出现在 Reader 导航
  - **需求**：FR-BUNDLE-003/005/006、FR-VALID-002
  - **验证方法**：包 allowlist 检查 + 链接可达性检查 + degraded 页归属检查
  - **通过条件**：Reader 目录无 audit 现场；链接全部可达；degraded 页不进 Reader 导航
  - **失败条件**：出现 audit 现场文件、断链或 degraded 页出现在 Reader 导航
  - **证据类型**：`test` + `evidence`
- [ ] **AC-06**：同一 TopicIndex 和输入重复运行时，路径、index 内容和受管 frontmatter/hash 稳定；`generated.at`、verified 追加和 manifest release 状态按易变字段规则处理；未知扩展字段经过 YAML parse → write → parse 后语义不丢失，且 nested `sources/generated/verified` 不被扁平化
  - **需求**：FR-FRONT-001/002/005、FR-PROJ-002、FR-VALID-001
  - **验证方法**：同一输入两次运行，对比路径、index 字节、受管 hash 与 round-trip 结果
  - **通过条件**：两次运行受管部分字节一致；round-trip 后未知字段语义完整；嵌套未扁平化
  - **失败条件**：受管部分漂移、未知字段丢失或嵌套被扁平化
  - **证据类型**：`test`
- [ ] **AC-07**：`--no-llm`/Jaccard 运行网络调用数为 0；Task 2-A 只生成 `not_released` 的 bundle projection，不声称通过读者质量
  - **需求**：FR-LLM-001、FR-PROJ-001/002
  - **验证方法**：运行审计报告核对网络调用数与包状态
  - **通过条件**：网络调用数 0；包级 manifest `not_released`
  - **失败条件**：出现任何 LLM/embedding 网络调用，或包被标为 released
  - **证据类型**：`evidence`
- [ ] **AC-08**：固定版本的零网络外部 OKF parser 能读取 sample bundle；若该 smoke 不通过，产物名称和文档不得宣称 `OKF-compatible`
  - **需求**：FR-SMOKE-001/002、FR-BUNDLE-004
  - **验证方法**：运行 vendored parser smoke + 检查命名与 exit manifest
  - **通过条件**：smoke 通过且宣称 OKF-compatible（含 okf_version）；或 smoke 失败且命名降级 OKF-inspired、省略 okf_version、记录原因
  - **失败条件**：smoke 失败仍宣称 OKF-compatible，或 smoke 通过但省略 okf_version 且无降级记录
  - **证据类型**：`test` + `evidence`

## 14. 风险、未决与交接

- **RISK-01**：vendored OKF parser 的固定 commit 义务延续到 2-B/2-C
  - **受影响 ID**：FR-SMOKE-001/002、AC-08
  - **触发条件**：外部代码升级或维护
  - **后果**：smoke 不可重放或兼容性漂移
  - **缓解或 STOP**：build-code 固定 commit 并写入 exit manifest；2-B/2-C 沿用同一固定版本
  - **处理 Stage**：`build-code`
  - **验证**：exit manifest 记录 parser 来源/commit/bundle hash
- **RISK-02**：fixture 与真实语料耦合
  - **受影响 ID**：FR-FIX-001/002、AC-03
  - **触发条件**：选样片段无法获得或与样本记录不一致
  - **后果**：attribution 验证失真
  - **缓解或 STOP**：build-code 说明选样理由，基于 20 个已验证样本并保留真实 URI/指纹/claim 映射
  - **处理 Stage**：`build-code`
  - **验证**：fixture 选样说明与样本记录一致
- **RISK-03**：Concept Contract 单次修订预算（v1-draft→v1）
  - **受影响 ID**：FR-FRONT-001/003/005、FR-BUNDLE-004
  - **触发条件**：后续任务改变 section/模板/字段/映射
  - **后果**：消耗唯一一次 contract revision 额度，超预算需 PRD scope revision
  - **缓解或 STOP**：本轮只冻结 v1-draft；2-B 只允许一次有记录修订；2-C 通过后冻结 v1
  - **处理 Stage**：`build-spec`（冻结）→ `build-code` → `verify-code`
  - **验证**：contract revision 记录存在且唯一
- **RISK-04**：Task1 历史 receipt 与当前结果冲突未关闭
  - **受影响 ID**：FR-ENTRY-001、AC-02
  - **触发条件**：审计复核时发现历史 receipt 矛盾
  - **后果**：审计债保留，不影响本轮 fresh backfill 权威
  - **缓解或 STOP**：已记录于 task1-receipt-reconciliation.v1.json；Task 3 前人工确认
  - **处理 Stage**：Task 3 前人工
  - **验证**：人工确认记录
- **RISK-05**：入口 backfill 是重算而非历史 exit receipt
  - **受影响 ID**：FR-ENTRY-001、AC-02
  - **触发条件**：需要历史退出凭证时
  - **后果**：provenance_mode=recomputed_backfill 不能冒充原始退出凭证
  - **缓解或 STOP**：已披露于 backfill manifest；不影响 2-A 进入
  - **处理 Stage**：`build-spec`（已披露）
  - **验证**：backfill manifest 的 provenance_mode 字段

- **OPEN-01**：具体固定的 OKF parser commit
  - **受影响 ID**：FR-SMOKE-001/002、AC-08
  - **owner**：build-code
  - **影响**：smoke 可重放性与 OKF-compatible 承诺
  - **处理 Stage**：`build-code`
  - **关闭条件或 STOP**：实现时挑选并在 exit manifest 记录；无法固定则按 PRD 降级 OKF-inspired
- **OPEN-02**：三个 fixture 具体选哪些真实样本片段
  - **受影响 ID**：FR-FIX-001/002、AC-03
  - **owner**：build-code
  - **影响**：fixture 内容与 attribution 验证真实性
  - **处理 Stage**：`build-code`
  - **关闭条件或 STOP**：基于 20 个已验证样本选样并说明理由；无可用片段时不得虚构（按 D3 拒绝方案）
- **OPEN-03**：Task1 历史 receipt 冲突的最终关闭
  - **受影响 ID**：FR-ENTRY-001
  - **owner**：产品维护者（人工）
  - **影响**：审计债，不影响本轮交付
  - **处理 Stage**：Task 3 前人工确认
  - **关闭条件或 STOP**：产品维护者给出 canonical 确认

## 15. 业务影响与回归范围

### Reader Package 输出形态

- **既有行为**：Reader Package 是私有页面目录（README/Home/分类索引/主题页/`indexes/sources.md`）
- **本需求影响**：新增 OKF-compatible Reader Bundle 形态（README/Home/根 index.md/根 log.md/products/references/sources.md）；旧产物不迁移、不重写
- **回归路径**：既有 `--no-llm` digest 全流程（S1–S6）不受影响；本轮 bundle 生成只在隔离 fixture 中进行
- **验收**：AC-01/AC-05

### frontmatter 与状态

- **既有行为**：现有 frontmatter 为 YAML-like 简单解析；页头保留 `managed_by/digest_kind/digest_topic_id/digest_published_path`
- **本需求影响**：正式 concept 引入 OKF 字段与 `digest_*` 扩展字段；状态三层分离；未知扩展字段 round-trip 保留
- **回归路径**：既有主题页的稳定身份与托管标记必须继续满足「正式主题页」定义（CONTEXT.md）
- **验收**：AC-02/AC-04/AC-06

- **可能受冲击的业务规则**：`kb.structure.md` 声明路径 allowlist、单写者原子发布、归档先于写入、不删除旧页、claim 唯一 target_path 等既有不变量在 Task 2-A 保持不变
- **明确无影响**：正文语义编译（Task 2-B）、人工读者门（Task 2-C）、全量发布与 released（Task 3）在本轮不触碰；仅按 D-004 补齐页面级确定性机器信号；`--no-llm` 与 Jaccard 离线基线行为不变
