# 功能规格：task8 入口与导航（K2：入口页 + 分类导航 + 结构自检）

> 本材料由 build-spec 阶段产出，消费方 = build-plan / build-code / verify-code。
> 输入权威 = `decision-log.md`（make-decision，approved 2026-09-13）。本材料不重新决定产品方向；
> 凡"如何验证"的展开以不降低 decision-log 已冻结门槛为限。
> 状态：**frozen**（review-frozen-spec 已执行：available-with-failures，11 条 finding 全部处置，见阶段执行记录）

## 材料导航

| 章节 / 材料锚点 | 职责与摘要 | M/S/B/P 读取时机 |
| --- | --- | --- |
| `## 速读卡` | 30 秒了解本规格 | M：开工前必读 |
| `## 来源与决策映射` | 决策↔需求↔验收的对应 | S：build-plan 投影时读 |
| `## 3. 用户场景与状态覆盖` | 运行时行为分支（SCN-K2-001…008） | M：写测试场景时读 |
| `## 5. 功能需求` | 每条功能需求的精确契约 | M：实现对应职责块时读 |
| `## 11. 验收标准` | 验收怎么执行（oracle 定义） | M：写 oracle 时读；B：CI 回归时读 |
| `## 10. 明确不做与默认必须成立` | 不做的事与红线 | M：越界判断时读；S：review 时读 |

## 速读卡（30 秒）

- **一句话需求**：K1 编译出 `products/` 页面后，K2 在同一批次内生成三层导航（Home.md → Index.md → 模块 Index.md），
  用模型为每页写一条不重复的描述句，跑两道门（零孤儿/描述不同质）+ N=10 路径抽查，全绿才落盘导航并增写
  manifest `navigation` 机读状态；任一红 = blocked，不产出导航。
- **核心输入**：`page-manifest.json`（批次状态/阻塞项/来源台账，K1 FR-AUD-004 已冻结）+
  `products/**/*.md` 页面文件 + 各页 frontmatter（16 字段，K1 FR-PUB-001 已冻结）。
  **页面集合的权威源 = products/ 目录 + frontmatter**（消除 RISK-K2-3：K1 manifest 页面条目子字段未冻结，
  K2 不依赖未冻结字段）；manifest 页面条目仅用于条数对账。
- **核心产物**：批次目录内 `Home.md` + `Index.md` + `products/<product>/<section>/Index.md`（模块总览），
  以及 manifest 增写的 `navigation` 节。
- **最大影响面**：`digest` 一次运行的批次产物（新增导航文件与 manifest 增写）；K1 产物字节零改动；
  CompanyBrain/gbrain 零写入。
- **验收信号**：覆盖判定三件套（条目⊆可达∧链接存在∧可达⊆条目）；描述四判据（重复=0/骨架≥3/问句模板/空即失败）；
  `navigation_status` 机读可验。

## 来源与决策映射

> 只存 ID 关系，不复制 decision-log 正文。Source = R-*；Decision = D-*；OI = outline v1；AC = 本文件第 11 节。

| Source | Decision / OI | FR / SCN / AC | 备注 |
| --- | --- | --- | --- |
| R-008/R-011 | D-001/D-002，OI-01/OI-12 | 全部 FR；SCN-001/006/007；AC-K2-1…7 | 范围与运行形态 |
| R-008，R2-Q1/R2-Q6 | D-003，OI-02 | FR-NAV-001/002/003；SCN-001；AC-K2-1/AC-K2-4 | 三层结构 |
| R-008/R-014，Q4 | D-004，OI-04 | FR-NAV-002；AC-K2-1 | product/section 挂载 |
| R-012/R-013，Q5 | D-005/D-009，OI-08 | FR-GEN-001/002/003；SCN-003/004；AC-K2-2/AC-K2-6 | 描述生成+缓存 |
| R2-Q7 | D-006 | FR-GEN-004；AC-K2-4 | 模块中文名机械推断 |
| Q6/R2-Q3 | D-007，OI-06 | FR-NAV-004；SCN-002；AC-K2-5 | Home 批次标注+查询建议 |
| Q7/Q8，R-009 | D-008，OI-07 | FR-CHK-001…004；SCN-003/004/005/007/008；AC-K2-1/2/3/5 | 自检与失败处置 |
| S1/R-015 | D-010 | FR-NAV-003/005；AC-K2-4 | 同构契约 |
| Q6/Q8，S3/R-016 | D-008，OI-05/OI-06 | FR-AUD-001/002；SCN-002/005；AC-K2-5 | 状态衔接与零页面 |
| R-017 | OI-11；DEF-K2-1…5 | 第 12 节 | 延期台账 |

## 1. 问题与紧迫性

母任务实测基线：上一版 release 99 页中 **87 页无任何入口可达**、**95/99 入口描述同质**。
没有导航的批次目录对读者等于半成品：页面编译得再正确，翻不到就不可用。K1（页面编译）已冻结设计、
尚未研发；K2 不依赖 K1 的实现进度即可冻结自身契约（输入契约全部引用 K1 已冻结部分），与 K1 并行推进。

## 2. 背景、目标与范围

### 背景

K1 把 89 份冻结语料编译为 `products/<product>/<section>/<slug>.md` 页面 + `_audit/` 五件审计文件，
批次目录定位 = 临时对照产物（不是语义层），上库归 K3。K1 明确不做入口导航（其 NG-003），该范围整体移交本卡。

### 目标

读者从批次入口 3 跳内到达任一页面（Home→Index→模块 Index→页面），且每页的描述句有区分度；
全部由机器自检判定，不靠人翻页。

### 范围内

- 三层导航文件的生成（Home.md / Index.md / 模块 Index.md）与批次目录内落盘。
- 描述句与 Home 查询建议的模型生成（走缓存）与模块中文名机械推断。
- 两道门（零孤儿覆盖判定/描述四判据）+ N=10 路径抽查的执行与失败处置。
- manifest `navigation` 节增写与 run-metrics 成本补记。
- 与 K1 同一次 `digest` 运行内衔接（K1 产物写出后、本卡生成导航、manifest 二次落盘）。

### 范围外

见 `## 10. 明确不做`（K1 编译、K3 发布通道、K4 删码、查询集验收、CB 既有页等，全部继承 decision-log NG）。

## 3. 用户场景与状态覆盖

### SCN-K2-001：正常批次（complete 有页面，全绿）

一次 digest 运行：K1 产物写出 → K2 读 manifest 状态与页面条目 → 生成三层导航到暂存区 → 模型写描述
（缓存命中免调）→ 两道门遍历+四判据+N=10 路径抽查全绿 → 导航落盘批次目录 → manifest 二次落盘增写
`navigation{navigation_status:generated_ok, success_pages:N, blocked_sources:0}` → run-metrics 补记 K2 成本 → 批次交付。

### SCN-K2-002：部分成功批次（complete，含阻塞来源）

同 SCN-001，导航只覆盖成功页；Home.md 批次状态行标注 success_pages=N、blocked_sources=M（M=K1 阻塞清单长度）；
manifest 对账两数一致。K1 侧失败来源（known_empty/duplicate_alias/audit_only）无页面、不进导航，不重复展示。

### SCN-K2-003：K1 批次 blocked / interrupted

K2 不生成导航、不产出任何导航文件。blocked 批次：manifest 可写则增写
`navigation{navigation_status:blocked, blocked_reasons:[K1-run-not-complete]}`；**interrupted 批次
（manifest 缺失/无效，K1 FR-AUD-004 已冻结该形态）：K2 无法也不写 manifest**，显式报告后退出——
中断批次凭"manifest 缺失/无效"本身被 K1 契约与 K3 拦截（review F-7 修复：不把不可写的中断 manifest
当作可写对象，不伪造状态）。

### SCN-K2-004：自检失败（孤儿/描述判据/路径抽查任一红）

导航不落盘（暂存区整体丢弃）；manifest `navigation{navigation_status:blocked, blocked_reasons:[...具体门与违例...]}`；
K1 产物状态零改动。

### SCN-K2-005：模型不可用或无缓存命中，或模型可用但任一描述/查询建议输出为空

产物生成失败：导航不落盘，manifest `navigation{navigation_status:blocked, blocked_reasons:[model-output-missing]}`。
（判据④：空描述即失败；不留空标注、不编造。）

### SCN-K2-006：run_status=complete 且零页面

K1 run_status 保持 complete 不动；K2 不产出导航；manifest `navigation{navigation_status:blocked,
blocked_reasons:[zero-page-batch]}`（两道门无对象不可判，不能空跑通过）。

### SCN-K2-007：同输入复跑

模型产物全部缓存命中 → 导航文件字节与上次一致；manifest `navigation` 节与运行级字段不参与字节比对
（比对范围 = 三个导航文件本身）。

### SCN-K2-008：K3 交接（下游消费）

K3 发布通道读取 manifest `navigation` 节：仅 `generated_ok` 批次允许进入发布；
`blocked`/缺字段一律拦截。K2 不读不写 K3 的任何产物。

### 状态覆盖清单

| 状态 | 载体 | 取值 | 覆盖场景 |
| --- | --- | --- | --- |
| 批次运行态 | manifest.run_status（K1 冻结） | complete/blocked/interrupted | 全场景 |
| 导航状态 | manifest.navigation 节 .navigation_status（本卡冻结） | generated_ok/blocked | 全场景 |
| 描述句状态 | 模块 Index.md 条目 | 非空文本（判据④保证） | SCN-001/002/007 |
| 缓存状态 | 任务级模型缓存（K1 机制） | hit/miss | SCN-001/005/007 |
| 加载态 | N/A（同 K1：单批内结构，无运行中可读中间态） | — | — |
| UI 状态 | N/A（non_ui） | — | — |

## 4. 产品事实与假设（PFACT-K2）

- **PFACT-K2-001**：K1 批次目录固定布局（FR-PUB-002）：`README.md` + `products/<product>/<section>/<slug>.md`
  + `_audit/{reference-blocks.jsonl, sources.jsonl, page-manifest.json, run-metrics.json, suspected-synonyms.md}`。
  本卡冻结完整写入白名单（review F-8 修复，六项，含暂存与清理语义）：
  ① `Home.md` ② `Index.md` ③ `products/**/Index.md` ④ `_audit/nav-staging/`（暂存，运行开始时整体重建、
  blocked 时整体删除）⑤ manifest `navigation` 节（二次落盘）⑥ `run-metrics.json` 的 K2 成本字段
  （FR-AUD-002）——其余路径零写入。
- **PFACT-K2-002**：K1 manifest 已冻结字段（FR-AUD-004）：`publish_status`/`run_status`/`attempt_id`/来源快照身份/
  阻塞项全集/页面条目/来源→页面反查表/来源台账；**页面条目的子字段名未冻结**（K1 spec 仅描述"含主题键、
  来源列表、claim/块计数"）。本卡的处置（build-spec review F-2 修复）：**量化域权威 = manifest 页面条目**；
  本卡冻结 K2 消费的条目字段名 `page_path`（批次内相对路径，如 `products/<product>/<section>/<slug>.md`），
  登记 DEF-K2-5 = K1 manifest 条目必须提供该字段（K1 侧对齐义务）。K2 用**双向路径对账**（非计数对账——
  计数相等不能证同一性）：每个条目的 `page_path` 在 products/ 存在且 frontmatter 可读；每个 products/
  页面（排除保留文件名）都有对应条目。任一向违例 → blocked（`nav-page-manifest-mismatch`）。
  保留文件名：`Index.md` 为导航保留——若发现 slug 为 `Index` 的 K1 页面 → blocked 显式报告
  （请求 K1 slug 排除，RISK-K2-3 跟踪）。
- **PFACT-K2-003**：页面 frontmatter 16 字段冻结（K1 FR-PUB-001），K2 消费其中 4 个：`title`（中文）、
  `product`（目录 slug）、`section`（模块目录 slug）、`generated_by`（本卡不校验其值，仅引用字段表）；
  导航页自身的 frontmatter 全集见 FR-NAV-005。
- **PFACT-K2-004**：CompanyBrain 入口参照（只读）：Home.md（tier 1，快速入口+查询建议）、分类索引
  （导语+分组入口）、产品/文档总览三层链；本卡三层结构与之同构体验但不复制其内容、不改其文件。
- **PFACT-K2-005**：模型缓存机制（K1 FR-CMP 系列冻结）：任务级固定位置，键 = 来源内容指纹+模型标识+
  提示模板版本+主题映射版本；命中不重调、缺则调用并写回。K2 复用该机制，键构成扩项见 FR-GEN-003。
- **PFACT-K2-006**：`tests/acceptance/` 现有 49 个测试文件、`tests/conftest.py` 不存在（基线 c5fb2b5 取证）；
  本卡新增验收测试挂入同目录同风格。
- **PFACT-K2-007**：旧 `src/knowledge_digest/navigation.py`（344 行）渲染旧分类轴导航记录交 writeback，
  属旧 digest 行为（K1 已降级为对照脚本）；其结构（分类轴/旧 KB）与本卡 product/section 三层不同，
  **不复用**（盘点事实成立；按 decision-log OPEN-K2-2 归 build-plan 正式关闭，review F-9 修正状态归属）。
- **PFACT-K2-008**：slug 规则（K1 OPEN-003，build-plan 冻结）：gbrain 归一化不动点、批内唯一、确定性。
  K2 不生成 slug，只消费（链接目标 = 页面文件名去 `.md`）。

## 5. 功能需求

### 导航生成（NAV）

- **FR-NAV-001 批次导航生成**：K1 产物写出后，K2 在批次目录暂存区生成三件导航文件：
  `Home.md`（入口）、`Index.md`（全局知识索引）、`products/<product>/<section>/Index.md`（每模块总览）。
  暂存区 = 批次目录内 `_audit/nav-staging/`（K1 未声明路径，本卡冻结此名；自检通过前导航不出该目录）。
  - 依据：D-002/D-003；OI-02
  - 场景：SCN-001/002
  - 验收：AC-K2-4
- **FR-NAV-002 挂载与页面集**：量化域 = manifest 页面条目（PFACT-K2-002）；经双向路径对账后的条目集合为
  挂载全集。逐条目读 `page_path` 对应文件的 frontmatter 取 `title/product/section`；`product` → Index.md
  分节（节内按 section 分组）；`section` → `products/<product>/<section>/Index.md` 条目（每页：wikilink +
  描述句）。
  - 范围边界：frontmatter 缺 `title/product/section` 任一字段 → blocked（`nav-frontmatter-incomplete`）；
    不读页面正文（正文仅 FR-GEN-001 只读输入）
  - 依据：D-004；OI-04；PFACT-K2-002
  - 场景：SCN-001/002
  - 验收：AC-K2-1
- **FR-NAV-003 Home.md 内容**：①批次状态行（机械模板：`nav: success_pages=N blocked_sources=M` 单行，
  对账 manifest navigation 节）；②快速入口（wikilink 列表 → Index.md + 各 product 分节锚）；③查询建议
  ≥3 条（模型写，FR-GEN-002）；④使用边界段（确定性模板：本目录为临时对照产物、正式入口归 K3）。
  时间戳/批次名/运行级计数不写进 Home.md（AC-K2-6）。
  - 依据：D-007；OI-06
  - 场景：SCN-001/002
  - 验收：AC-K2-4/AC-K2-5
- **FR-NAV-004 Index.md 内容**：frontmatter（FR-NAV-005 契约，tier=1）+ H1「知识索引」+ 按 product
  分节；每节：product 名（slug 原样）+ 该 product 全部模块总览页的 wikilink 列表（按 section slug 升序）。
  无模型内容。
  - 依据：D-003/D-004
  - 场景：SCN-001
  - 验收：AC-K2-4
- **FR-NAV-005 导航页 frontmatter 契约**：三件套均 16 字段（字段集合引用 K1 FR-PUB-001，不新增字段名）；
  本卡冻结取值差异：`tier`：Home/Index=1、模块 Index=2；`title`：Home="批次入口"、Index="知识索引"、
  模块 Index=FR-GEN-004 的机械推断中文名；`type: reference`、`page_model: derived`、`scope: company`、
  `trust: medium`、`source_status: compiled`、`quality_status: formal`、`tags: [company, navigation]`；
  `created/updated` = 批次内页面 frontmatter created/updated 的最早/最晚（继承 K1 归一化值，同输入恒定——
  **不取运行时刻、不直接 stat mtime**，review F-3 修复）；
  `product/section/module` = 所在目录 slug（Home/Index 写 `navigation`）；`generated_by` 值归 build-plan
  命名（DEF-K2-4，确认前相关 oracle 记 incomplete）；`source` 写固定值 `batch`（**不写批次目录名**——
  目录名含运行级序号，违反 AC-K2-6，review F-3 修复；根目录标注由使用边界段文字承担）。
  - 范围边界：不新增第 17 个字段；ADR 0013 的溯源字段授权本卡不消费（沿用 K1 G-001）
  - 依据：D-010；S1
  - 场景：SCN-001
  - 验收：AC-K2-4

### 描述与建议（GEN）

- **FR-GEN-001 描述句生成**：每页面恰好一条描述句（中文，陈述「这页帮你解决什么」），模型写；
  输入 = 该页 frontmatter `title/section/product` + **页面叙述正文前 N 行**（只读输入、不改页面；
  N 默认值归 build-plan，review F-10 扩——原只给三个元数据字段无法支撑"这页解决什么"的语义输出，
  易产生空泛描述或无依据断言）；输出逐句校验非空非空白（判据④前置：空即拒并判失败）。
  无重试：被拒/空输出即 blocked（review F-11——重试与预算上界 1.5× 数学冲突）；评价词过滤归
  DEF-K2-4 拒绝词表（命中即 blocked，词表 build-plan 冻结）。
  - 依据：D-005；OI-08
  - 场景：SCN-001/003/004
  - 验收：AC-K2-2
- **FR-GEN-002 查询建议生成**：Home.md 查询建议 ≥3 条，模型写，输入 = Index.md 分节结构；
  同样过拒绝词表与非空校验（空即 blocked）。
  - 依据：D-007（R2-Q3 用户选择）
  - 场景：SCN-001
  - 验收：AC-K2-4（非空≥3）
- **FR-GEN-003 缓存键**：复用 K1 缓存机制（PFACT-K2-005），**键构成与 K1 同构**（review F-6 修复）：
  sha256(任务标识(`page-desc`/`home-suggest`) + **输入内容指纹**（描述=页面文件字节 sha256；建议=Index
  分节结构摘要 sha256）+ 模型标识 + 提示模板版本 + 主题映射版本)。输入内容变→指纹变→缓存必失效
  （改一字节不重用的负例归 build-plan 测试）；批次目录名与运行时刻不进键（AC-K2-6）。
  - 依据：D-009
  - 场景：SCN-001/007
  - 验收：AC-K2-6
- **FR-GEN-004 模块中文名机械推断**：模块 Index 的 title = 该模块页面 title 集合的**确定性推断**
  （零模型调用、同输入同结果）；推断规则细节（切分/取词/并列处理）归 build-plan 冻结（DEF-K2-4，
  review F-9 修复——build-spec 不越权冻结 build-plan owned 参数）；零页面模块不存在（不产生模块 Index）。
  - 依据：D-006（R2-Q7）
  - 场景：SCN-001
  - 验收：AC-K2-4（人工可读性抽查不入 oracle——机器只验确定性：同输入同推断）

### 自检与失败处置（CHK）

- **FR-CHK-001 入口图遍历（覆盖判定三件套）**：从 Home.md 解析 wikilink，BFS 遍历导航图（节点 = 批次内
  md 文件）；判定：①页面集 ⊆ 可达集合；②每条链接目标存在；③可达页面 ⊆ 页面集（导航不得指向
  manifest 外页面）。**不用数量等式**（遍历集合含导航节点，数量恒大于页面集，等式必失败——detail R2-B1）。
  - 依据：D-008；OI-07
  - 场景：SCN-004
  - 验收：AC-K2-1
- **FR-CHK-002 描述四判据**：①规范化（去首尾空白/全半角归一/去标点/小写）后精确相等即重复，容忍=0；
  ②句式骨架（移除该页 title 与 product/section 词、去标点小写后的剩余串）重复 ≥3 句；
  ③疑问句式模板（"如何/什么是/怎么…？"骨架）≥3 句；④任一描述为空/空白即失败。命中任一 → blocked。
  - 依据：D-005；Talk R3 冻结；detail R2-B2/B3
  - 场景：SCN-004/005
  - 验收：AC-K2-2
- **FR-CHK-003 路径抽查**：读冻结题目清单（DEF-K2-2 收集、用户确认；每题 `{id, query, target_slug}`），
  对每题在导航图 BFS 最短路径，点击数（边数）≤3 为通过；任一路径 >3 或 target 不可达 → blocked。
  清单未确认前本 oracle 记 incomplete（诚实标注）。
  - 依据：D-008；OI-07
  - 场景：SCN-004
  - 验收：AC-K2-3
- **FR-CHK-004 失败处置与暂存清理**：任一自检红 → 暂存区整体删除、导航不落盘、manifest
  `navigation_status=blocked` + 具体 `blocked_reasons`（门名+违例摘要）；K1 产物与 manifest 其余节零改动。
  修复循环轮数=0（不修孤儿/同质，人工修输入或代码后重跑——decision-log D-008/Q8）。
  - 依据：D-008
  - 场景：SCN-004/005/006
  - 验收：AC-K2-5

### 审计衔接（AUD）

- **FR-AUD-001 manifest navigation 节**：自检通过后二次落盘 manifest，增写
  `navigation: {navigation_status, success_pages, blocked_sources, blocked_reasons: [...]}`；
  blocked 情形同样增写（status=blocked）。字段名/类型/公式本卡冻结（detail R2-B6）：
  `success_pages` == products 页面集大小；`blocked_sources` == K1 阻塞项清单长度；两数与 Home.md 状态行一致。
  - 依据：OI-12；detail R2-B6/R2-B7
  - 场景：全场景
  - 验收：AC-K2-5
- **FR-AUD-002 成本补记**：K2 模型调用（描述=页面数次、建议=每批 1 次，批量调用）计入 run-metrics
  （K1 FR-AUD-005 既有字段），成功与失败运行都记；K2 计划调用数 = 页面数+1，实际 ≤ 计划×1.5（继承 K1 约束）。
  - 依据：D-009；K1 FR-AUD-005
  - 场景：SCN-001/005
  - 验收：AC-K2-6 辅助（成本真实非 null）

## 6. 模块划分（产品职责）

| 模块（文件名归 build-plan） | 职责 | 来源 |
| --- | --- | --- |
| 批次导航编译器（新） | 页面集收集/挂载/三件套生成/模型产物生成与缓存/自检四件套/暂存清理/manifest 增写/成本补记 | 本卡全部 FR |
| digest 运行链路（K1 模块，本卡只挂接） | K1 产物写出后调用本卡入口；本卡返回后批次收尾 | K1 FR-CLI |

- 检查器不单列模块：与生成器同文件（K2 范围小，两职责强耦合于"批次导航"一个语义）；若 build-plan 发现
  文件超 500 行再拆（删除条件随模块登记）。
- 旧 `navigation.py` 不修改（DO NOT TOUCH 候选，build-plan 定边界）。

## 7. 关键实体

- **页面集**：本批 `products/**/*.md`（排除 Index.md）；成员身份 = 相对路径 + frontmatter 四字段。
- **导航图**：Home.md/Index.md/模块 Index.md 为内部节点，页面为叶子；边 = wikilink。
- **描述句**：页面 → 一句话（≤60 字）；载体 = 模块 Index.md 条目行。
- **题目清单**：N=10 条查询路径抽查的冻结 JSON（DEF-K2-2）。
- **navigation 节**：manifest 增写的机读状态块（FR-AUD-001）。
- **暂存区**：`_audit/nav-staging/`（FR-NAV-001）。

## 8. 数据和生命周期

- **粒度**：页面（挂载/描述）、模块（分节/总览）、批次（状态/标注）三级。
- **时效**：同输入产物字节一致（模型产物走缓存）；created/updated 取批次内页面值的最早/最晚，不取运行时刻。
- **缺失或迟到**：模型不可用 → SCN-K2-005；K1 状态非 complete → SCN-K2-003；零页面 → SCN-K2-006。
- **当前与历史**：批次间导航不增量、不合并；历史批次（无导航的 K1 批次）不追补（用户重跑生成）。
- **归属与清理**：暂存区每次运行重建（旧暂存先删）；导航文件只在自检通过后落盘。

## 9. 兼容性预留

- **K1 衔接**：K1 manifest 结构变化（新增/改名已冻结字段）→ K2 启动时校验必要字段存在
  （run_status/阻塞项/来源台账），缺即 blocked 并显式报告字段名（RISK-K2-3 的 fail-closed 化）。
- **K3 预留**：navigation 节即 K3 门禁接口；K3 需另决定 CB 入口合并（DEF-K2-3，非本卡）。
- **命名预留**：Index.md/模块 Index.md 不绑定 product 字眼；未来非产品语料同结构复用。

## 10. 明确不做与默认必须成立

### 明确不做（继承 decision-log NG，本卡不重新论证）

- 不改 K1 编译的任何环节；不读写 K1 产物正文/frontmatter。
- 不做发布通道/原子切换/回滚（K3）；不做真实查询集对照验收（K3）。
- 不删码（K4）；不引入向量库/图库/服务化/前端/多格式输入。
- 不修改 CompanyBrain 既有页/停摆流水线/gbrain。
- 不做机器自动修孤儿/同质（修复循环轮数=0）。
- 不做分批/中断续跑（K1 D-013 已冻结一次跑完）。

### 默认必须成立

- 写权受限：批次目录内仅 FR-NAV-001 列出的四项允许写入；其余路径零写入。
- 失败不伪装成功：blocked 情形必产 manifest navigation 记录，禁静默。
- K1 状态隔离：K2 不改写 K1 任何已写文件与 manifest 已冻结字段（OI-12 counterexample 成立即判衔接破坏）。
- 结构门≠可用性：本卡验收只证"找得到、分得清"；知识可用性归 K3 查询集（ADR 0014）。

## 11. 验收标准

| AC | 判据（可执行定义） | oracle | 出口 |
| --- | --- | --- | --- |
| AC-K2-1 零孤儿 | 覆盖判定三件套成立：①页面集⊆可达 ②全部链接目标存在 ③可达页面⊆页面集；量化域=products 页面集（manifest 条目数对账） | 遍历脚本 | 全绿 |
| AC-K2-2 描述区分度 | 四判据全过：①规范化相等=0 ②骨架重复<3 ③问句模板<3 ④无空描述 | 判据脚本 | 全绿 |
| AC-K2-3 路径抽查 | 题目清单 N=10（用户确认后冻结），逐题 BFS 边数≤3 | 路径脚本 | 清单确认前 incomplete |
| AC-K2-4 结构齐备 | 三件套齐备；frontmatter 16 字段契约（FR-NAV-005）；查询建议≥3 非空 | 结构脚本 | generated_by 子项确认前 incomplete |
| AC-K2-5 阻塞显式化 | 不产出导航的情形全集（SCN-K2-003/004/005/006）均产 manifest navigation_status=blocked+reasons；成功批次=generated_ok 且三数对账（Home 行/manifest/页面集） | 状态脚本 | 全绿 |
| AC-K2-6 可重复 | 同输入双跑：三导航文件字节一致；成本计数真实非 null | 双跑比对 | 全绿 |
| AC-K2-7 写权边界 | 批次目录外零写入；批次内仅四项允许写入 | 写路径审计 | 全绿 |

## 12. 风险、未决与交接

### 风险（继承 + 本阶段新增）

| risk_id | 内容 | 处置 |
| --- | --- | --- |
| RISK-K2-1 | 模型描述仍可能同质 | 四判据硬校验（已冻结） |
| RISK-K2-2 | 模块中文名推断不准 | 确定性规则 FR-GEN-004；影响导航体验不影响事实；人工修正通道=显式配置文件（build-plan 定） |
| RISK-K2-3 | K1 manifest 接口漂移 | PFACT-K2-002 输入解耦 + FR 9. 启动字段校验 fail-closed |
| RISK-K2-4 | 结构门误读为可用性 | 第 10 节默认必须成立固化 |
| RISK-K2-5（本阶段新增） | K1 研发未完成，联调时无真实 manifest 可用 | build-code 用冻结 schema 构造 fixture（本文件 FR-AUD-001 为准）；K1 合并后跑一轮真实联调（登记 build-plan） |

### 未决项（本阶段处置结果）

| id | 内容 | owner | 状态 |
| --- | --- | --- | --- |
| OPEN-K2-1 | K2 导航术语登记 CONTEXT.md | build-spec（本阶段） | 本文件发布后执行登记 |
| OPEN-K2-2 | 旧 navigation.py 复用盘点 | build-plan | 盘点事实已产出（PFACT-K2-007：不复用）；正式关闭动作归 build-plan |
| OPEN-K2-3 | 自检指标精确形态 | build-spec（本阶段） | 已冻结（FR-CHK-001/002/003 + AC 表） |
| DEF-K2-2 | 十条路径题目清单 | owner=用户确认（build-plan 期间收集表） | 触发=build-code 开工前 | handoff=用户 → tasks T014/T020 fixture | 关闭=用户确认冻结清单文件 |
| DEF-K2-4 | generated_by/拒绝词表/N=30/推断规则 | owner=build-plan（DEC-K2-004 已冻结关闭） | 触发=已完成 | handoff=plan → tasks 各卡 Knowledge | 关闭=DEC-K2-004 落 plan |
| DEF-K2-5 | K1 manifest 条目提供 `page_path` | owner=K1 侧 build-spec/plan | 触发=K1 冻结 manifest schema 时 | handoff=K1 → K2 P1 fixture 对账层 + K1 集成检查点 | 关闭=真实批次联调核验通过 |
| DEF-K2-3 | CB 入口合并/取代 | owner=K3 | 触发=发布通道写语义层时 | handoff=本卡 navigation 节 → K3 门禁 | 关闭=K3 发布决策记录 |

### 交接给 build-plan 的边界

- 不得重新决定产品方向；不得降低四判据/覆盖判定/navigation 机读契约的任何门槛。
- 需冻结的实现参数（DEF-K2-4）：模块文件名、generated_by 值、拒绝词表、正文行数 N、模块名推断规则。
- **build-code 开工 gate（review F-4）**：DEF-K2-2（十条题目用户确认）与 DEF-K2-4 关闭前，允许 build-plan
  完成，但 build-code 的第一个任务卡必须以"两 DEF 已关闭"为前置；tasks.md 须把 gate 写成显式 STOP 条件。
- 需补的验证 fixture：K1 manifest 冻结 schema 样例（按 FR-AUD-004 + FR-AUD-001 构造）。

## 13. 业务影响与回归范围

- `digest` 一次运行新增批次产物（三导航文件 + manifest 增写）；对 K1 产物字节零影响。
- 既有 49 个 acceptance 测试零改动预期；本卡新增测试挂 `tests/acceptance/test_task8_entry_navigation.py`。
- 与 K1 的联调依赖：K1 合并主干后可跑真实端到端（RISK-K2-5）。

## 阶段执行记录（build-spec）

### spec-clarify 执行记录（step 3）

trigger = false。本阶段负责的 OPEN-K2-1/2/3 与 DEF-K2-5 逐项核对均可由已批准决策与已核实事实唯一推导：
导航术语（decision-log D-003/005）、自检指标（AC-K2-1/2/3 判据已冻结）、manifest 对齐（K1 FR-AUD-004 全文可循）；
无用户裁决分叉。其余 OPEN/DEF 按 decision-log owner 列归属本阶段或 build-plan。十维 completeness 检查：
旅程=SCN-K2-001…008；页面范围=第 5/7 节；数据与状态=FR-AUD-001 + 状态覆盖清单；成功边界=SCN-001/007；
失败边界=SCN-003/004/005/006；权限=第 10 节默认必须成立；集成外部效果=K3 交接（SCN-008）；非目标=第 10 节；
延期=第 12 节；验收=第 11 节。无 unknown 维度。

### spec-specify（step 4）

本草稿第 1–13 节即本步骤产物：按 decision-log 展开 FR/SCN/PFACT/AC，不改任何已冻结方向；
新增内容仅限"如何验证"层（fixture/oracle/字段契约），均标注来源（决策/DEF/review finding）。

### conditional-spec-research 执行记录（step 2）

已执行一轮子代理只读取证（成功）：K1 manifest 冻结字段与页面条目子字段缺口（PFACT-K2-002）、
16 字段清单（PFACT-K2-003）、manifest 落盘顺序与 K2 挂接点（第 5 节）、旧 navigation.py 盘点（PFACT-K2-007，
OPEN-K2-2 关闭）、CONTEXT.md 术语区格式（登记用）、测试布局（PFACT-K2-006）。
正式 research receipt 无 build-spec 公共发布通道（同 K1），按合同记未供给，事实已固化进 PFACT。

### simplicity-guard 四阶梯执行记录（step 5）

- 分批/中断续跑/原子发布/向量库：P0 不成立（K1 D-013 / NG-004 / NG-007）。
- 旧 navigation.py：P1——结构不同且属旧行为，不复用不修改（PFACT-K2-007）。
- 模型缓存：P2——复用 K1 机制（PFACT-K2-005），键构成扩项最小（FR-GEN-003）。
- 导航生成/自检/navigation 节：P3——无既有覆盖，新增单模块（第 6 节，含 500 行拆分删除条件）。
- 查询建议：P3——用户 R2-Q3 显式选择，补最小 oracle（FR-GEN-002）；非发散新增。
- 结论：无范围膨胀；每处新增给出依据与删除条件。

### plan-ceo-review 执行记录（step 6）

- 问题与证据分离：问题=87/99 无入口、95/99 同质（PRD 基线）；证据=母任务 F-001 实测。
- 最窄范围：K2 一张卡（D-001）；既有杠杆=K1 冻结契约（manifest/frontmatter/缓存）。
- 可信备选对照：两层/一层导航、纯模板描述、确定性聚合描述（detail F-7）——均已在
  decision-log 拒绝方案留档，本阶段无新备选优于已选方向。
- 可否定前提：PFACT-K2-001/002/005（批次布局、manifest 契约、缓存机制）；若 K1 冻结契约被推翻回 make-decision。
- 时机/影响半径/最小缺口：影响半径=批次产物新增四项；最小缺口=单新模块+检查器（本文件第 5/6 节）。

### UI 条件路径记录（steps 7–9，non_ui 全部 N/A）

UI applicability = non_ui（继承 decision-log，三来源一致）。ui-project-init / design-source-readiness /
conditional-plan-design-review 均 N/A：CLI + Markdown 产物，无浏览器界面/路由/交互组件；不产生 UI contract facts。

### freeze-spec（step 10）

本草稿标 frozen（头部状态行）；冻结内容 = 第 1–13 节全部条款。

### review-frozen-spec 执行记录（step 11）

wh-review build-spec surface 真实调用一轮：公共结果 `available`（outcome=partial：kimi/antigravity
PUBLIC_RESULT_INVALID 身份降级，按合同不写成"没有问题"；有效 reviewer=codex/luna，11 条 finding，
3 blocking + 8 major，全部 actionable、direct 证据）。逐条处置，全部 `fixed`，零静默丢弃：

| finding | 处置落点 |
| --- | --- |
| F-1（blocking：navigation.status 与已冻结 navigation_status 命名不一致） | 全文统一 `navigation_status`（SCN/FR/AC/状态清单） |
| F-2（blocking：页面集权威源改为文件系统+计数对账，弱化量化域） | PFACT-K2-002/FR-NAV-002 重写：manifest 条目权威 + 双向路径对账 + 冻结消费字段 `page_path`（DEF-K2-5 升级为 K1 对齐义务）+ `Index.md` 保留名规则 |
| F-3（major：created/updated 与 source 含易变值，违反双跑字节一致） | FR-NAV-005：source=固定值 `batch`；created/updated 取自页面 frontmatter（不 stat mtime） |
| F-4（blocking：十条路径与 generated_by 未冻结即 freeze） | 保持诚实标注 incomplete + 增设 **build-code 开工 gate**（DEF-K2-2/4 关闭为前置，写进 tasks STOP）；F-4 的"先冻结再 freeze"以 gate 模式满足——规格 frozen 但实现与验证被 gate 拦截 |
| F-5（major：60 字/8 条/拒绝词表/重试为 spec 越权新增） | FR-GEN-001/002 收敛：删 60 字与 8 条上限；拒绝词表归 DEF-K2-4；删重试（见 F-11） |
| F-6（major：缓存键与 K1 冻结机制不同构） | FR-GEN-003：键与 K1 同构（任务标识+输入内容指纹+模型标识+提示模板版本+主题映射版本） |
| F-7（major：interrupted 批次 manifest 缺失时无法写 navigation） | SCN-K2-003 分态：blocked 可写则写；interrupted 不写、显式报告，凭 K1 契约被 K3 拦截 |
| F-8（major：写入白名单与 staging/run-metrics 矛盾） | PFACT-K2-001 白名单扩为完整六项（含暂存区重建/清理语义与 run-metrics K2 字段） |
| F-9（major：FR-GEN-004 越权冻结 build-plan 参数；OPEN-K2-2 关闭越权） | FR-GEN-004 降级为"确定性推断，规则归 build-plan"；OPEN-K2-2 状态回改（盘点事实保留，关闭归 build-plan） |
| F-10（major：描述输入仅三个元数据字段，语义输出不可靠） | FR-GEN-001 输入扩页面正文前 N 行（只读；N 归 build-plan）；缓存指纹随之覆盖（F-6） |
| F-11（major：重试与预算上界 1.5× 数学冲突） | 删重试：被拒/空输出即 blocked；预算公式不变 |

修复均在本阶段完成并回写本规格；无 finding 升级或降级；未引入 decision-log 之外的产品方向。

### 阶段末遗漏披露

（发布步骤输出时回填。）

### main-agent-disposes-findings（step 12）

11 条 finding 全部处置（处置表见 review-frozen-spec 小节）：3 fixed-as-blocking 修复（F-1 命名统一、
F-2 权威源+路径对账、F-4 gate 模式）、8 fixed（F-3/5/6/7/8/9/10/11）；零静默丢弃、零 rejected_invalid、
零 needs_human。处置已回写本文件（头部 frozen 状态 + 各处条款），本轮提交为发布前最后修订。

### stage-end-spec-analyze（step 13）

外部 spec-analyze 宿主不可用（同 stage_outcome 根因），主会话按"原始需求+决策 vs 完整 spec"做全量对账：

**R-001…R-017 对账**：

| 需求 | spec 落点 | 状态 |
| --- | --- | --- |
| R-001/R-002/R-003（流程约束） | 阶段执行记录 steps 1–15 逐步执行 | covered |
| R-004（六类边界） | SCN-K2-001…008 + 第 5/7/10/12 节 | covered |
| R-005（上下文控制） | 取证走子代理（step 2），主会话只收结论 | covered |
| R-006（大白话） | Talk/grill 在 decision-log；本材料为冻结条款 | covered |
| R-007（范围=K2 卡） | 第 2 节范围内/外 | covered |
| R-008（结果） | FR-NAV-001/003/004、FR-GEN-001 | covered |
| R-009（3 条 FR/AC） | 第 11 节 AC-K2-1/2/3 | covered |
| R-010（scope 表述） | 第 2 节 + PFACT-K2-002 页面类型映射声明（review D-M1） | covered |
| R-011（流程状态转换） | SCN-K2-001…008 + FR-CHK-004 + FR-AUD-001 | covered |
| R-012（基线 87/99、95/99） | 第 1 节 + FR-CHK-002 判据③正对 | covered |
| R-013（local risk 压制） | FR-CHK-002 四判据 | covered |
| R-014（依赖=K1 页面清单） | PFACT-K2-002 + FR 9. 兼容预留 | covered |
| R-015（S1 同构） | FR-NAV-005 | covered |
| R-016（S3 状态词表） | 状态覆盖清单 + SCN-K2-002/003/006 | covered |
| R-017（OPEN/DEF 归属） | 第 12 节未决项表 | covered |

**D-001…D-012 对账**：D-001→第 2/10 节；D-002→FR-NAV-001；D-003→FR-NAV-003/004；D-004→FR-NAV-002；
D-005→FR-GEN-001/FR-CHK-002；D-006→FR-GEN-004；D-007→FR-NAV-003；D-008→FR-CHK-004；D-009→FR-GEN-003/FR-AUD-002；
D-010→FR-NAV-005；D-011→第 12 节 DEF-K2-3；D-012→PFACT-K2-001。12/12 covered。

**OI-01…OI-12 对账**：OI-01→FR-NAV-001；OI-02→FR-NAV-001/SCN-001；OI-03→FR-NAV-005/第 6 节；OI-04→FR-NAV-002；
OI-05→状态覆盖清单；OI-06→SCN-K2-002/003/006；OI-07→FR-CHK-001/2/3；OI-08→FR-GEN-001/FR-CHK-002；
OI-09→第 10 节默认必须成立；OI-10→第 10 节；OI-11→第 12 节；OI-12→FR-AUD-001/SCN-K2-008。12/12 covered。

**AC-K2-1…7 对账**：逐条在第 11 节有可执行定义 + oracle；AC-K2-3/AC-K2-4 含诚实 incomplete 子项（gate 拦截）。
**六类边界对账**：流程=SCN 全链；页面范围=PFACT-K2-001 六项白名单+第 6 节；数据状态=状态覆盖清单；
成功/失败=SCN-K2-004/005/006 + FR-CHK-004；非目标=第 10 节；延期=第 12 节。无 empty 维度。

**结论**：无"做完仍不能交付"的缺口；两项 gate（DEF-K2-2/4）已以 STOP 条件形式前置拦截。

### publish-spec-result（step 14）

大白话交接（向用户/下游）：
- 这份 spec 做了什么：把 K2 导航从"想法"变成能开工的图纸——三层导航文件长什么样、描述怎么生成怎么查重、
  自检怎么跑、失败怎么办、K3 怎么读状态放行，全部写死成机器可验的条款。
- 关键流程：K1 产物写出 → 暂存区生成 → 模型写描述（缓存）→ 两道门+路径抽查 → 全绿落盘 + manifest
  增写 navigation 节；任一红 = 不落盘 + blocked 状态。
- 边界：只写批次目录内六个白名单路径；K1 状态一个字段都不动；CompanyBrain/gbrain 零触碰。
- 调研/澄清事实：K1 manifest 页面条目子字段未冻结 → 用"条目权威+路径对账+冻结 page_path 字段"解耦；
  旧 navigation.py 结构不同不复用。
- 审查结果：codex/luna 11 条 finding 全修（含 3 blocking）；kimi/antigravity 身份降级按事实记录，不写成通过。
- 风险：K1 未研发完（RISK-K2-5，fixture 先行）；题目清单与 generated_by 是 gate。
- 下一阶段：build-plan（步骤链 13 步，plan.md + tasks.md）。

### stage-reflection（step 15）

外部 reflect 宿主不可用：无 authenticated stage outcome 原件（step 13 的 stage_outcome 即 unavailable），
按合同记 `unavailable`（缺判断输入，不复盘、不伪造）；原 stage 状态保留，不阻断交接。
