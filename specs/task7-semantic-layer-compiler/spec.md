# 功能规格：task7 语义层页面编译器（K1：参考保真 + 语义层页面编译）

> 本文件是 build-spec 阶段唯一权威材料，基于已批准的 decision-log.md（make-decision，approved 2026-09-13）。
> 本文件只写产品问题、行为、边界和验收；实现文件清单、代码符号、工程命令归 plan.md / tasks.md。
> 产品面名词（批次目录、`_audit/` 文件、`digest` 命令）是用户可观察契约，按决策日志原样继承，不属实现细节。

- **功能名**：K1 语义层页面编译器（89 份冻结 Confluence Markdown → 参考保真、逐条可溯、结构同构的语义层知识页）
- **来源**：decision-log.md（task7-semantic-layer-compiler，approved 2026-09-13）；母任务 PRD K1 卡
- **状态**：已接受（build-spec 冻结）

## 材料导航

> 可再生辅助节，非第五份材料；M=必须逐字读，S=速读，B=回查，P=计划阶段读。

| 章节 | 摘要 | 读取时机 |
| --- | --- | --- |
| 速读卡 | 30 秒抓住需求 | S |
| 来源与决策映射 | 每条 FR/AC 回 decision-log 的桥 | B |
| 1–2 问题与范围 | 为什么做、做什么 | M |
| 3 用户场景与状态覆盖 | J1–J9 旅程与边界态 | M |
| 4 PFACT | 已核实产品事实层 | B |
| 5 功能需求 | FR 行为契约 | M |
| 6–9 模块/实体/数据/兼容 | 产品边界结构 | P |
| 10 明确不做与默认必须成立 | 非目标唯一权威表 | M |
| 11 验收标准 | AC-01…AC-13 判定卡 | M |
| 12 风险、未决与交接 | 风险台账与 OPEN 归属 | B |
| 13 业务影响与回归 | 受影响面 | P |

## 速读卡（30 秒）

- **一句话需求**：投料人运行一次 `digest`，把 89 份冻结 Confluence Markdown 编译成一整个批次目录——里面是参考内容逐字零丢失、每条叙述可回原文、结构与 CompanyBrain 同构的知识页，加上五份机读审计文件，交给 K3 发布通道。
- **核心改动点**：
  - `digest` 命令换成新的语义编译行为（旧行为降为 `scripts/` 下一次性对照脚本）。
  - 批次目录 = `README.md` + `products/<产品>/<模块>/<页面>.md` + `_audit/` 五件（参考块清单、旁路溯源、页面清单、运行指标、疑似同义报告）。
  - 拆块保真（整张表为一块、字节从不改写）+ 按标题名确定性归组 + 模型只写标题/导读且结果冻结缓存。
- **最大影响面**：`digest` 命令行为的切换（AC-09）与旧 `digest` 行为绑定的测试口径（AC-10）；CompanyBrain 与 gbrain 零写入。
- **验收信号**：同批输入连跑两次产物字节一致（AC-06）；参考块与原文逐字节零差异（AC-02）；13 条 AC 全部满足。

## 来源与决策映射

> 只存 ID 关系，不复制 decision-log 正文。Source = decision-log 原始需求 R-*；Decision = D-*。

| Source ID | Decision ID | FR / AC IDs | Status | Unresolved / handoff |
| --- | --- | --- | --- | --- |
| R-009 / R-010 | D-001 | 全部 FR、AC-01…AC-13 | current | — |
| R-011 / R-026 | D-011 / D-012 | FR-SRC-001 | current | — |
| R-018 / R-031 / R-040 | D-002 / D-017 | FR-PUB-002 | current | — |
| R-021 / R-015 | D-003 | FR-GRP-001 | current | OPEN-008 本阶段冻结 |
| R-022 / R-023 | D-007 | FR-CMP-003 / FR-GRP-002 | current | OPEN-002 归 build-plan |
| R-035 / R-039 | D-015 / D-006 | FR-PUB-001 | current | OPEN-003 归 build-plan |
| R-013 / R-020 / R-036 | D-005 / D-006 | FR-AUD-002 / FR-PUB-001 | current | OPEN-006 本阶段登记 CONTEXT.md |
| R-014 / R-025 | D-009 | FR-AUD-003 | current | OPEN-009 本阶段冻结 |
| R-015 / R-019 | D-004 | FR-AUD-002 | current | OPEN-012 本阶段冻结 |
| R-024 | D-008 | FR-AUD-004 / FR-BLK-002 | current | — |
| R-016 / R-041 | D-013 / D-018 | FR-PUB-003 / FR-CLI-001 | current | OPEN-005 归 build-code |
| R-028 / R-029 | D-010 | FR-BLK-001 / FR-CMP-001 | current | — |
| R-034 | D-011 | FR-AUD-001 | current | — |
| R-027 | D-015 | FR-PUB-001 | current | DEF-002 未验证 |
| R-030 / R-017 | D-001 / D-014 | 第 10 节非目标 | current | NG-001…NG-008 |
| R-033 | D-014 | 第 12 节交接 | current | DEF-001…DEF-008 |
| R-037 | D-016 | FR-REG-001 | current | OPEN-001 / DEF-006 归 build-plan |
| 母任务成本硬约束 / F-8 | OI-20 | FR-AUD-005 | current | — |
| F-7 | OI-21 | FR-AUD-001 | current | — |
| 用户 Q21 | D-012 | FR-SRC-002 | current | — |
| 用户 Q14 / Q17 | D-007 | FR-CMP-003 / FR-CMP-004 | current | — |
| OPEN-011 触发 | D-006 | FR-PUB-001（created/updated） | current | 本阶段冻结取值来源 |
| OPEN-006 触发 | D-004 / D-005 | FR-AUD-002 | current | 本阶段登记 CONTEXT.md |

每条 FR/AC 均可经本表回到 decision-log；本阶段未新增任何 decision-log 之外的产品方向。

## 1. 问题与紧迫性

KnowledgeDigest 现有管线产出的是「文档的场景化摘要索引」：固定窗口拆块会切断表格、会改写文本，参考型内容（表格/参数/枚举/字段字典/URL/报错文案）在产物中大面积消失，下游读者与 Agent 拿不到可直接引用的事实。母任务已把方向定为直接产出与 CompanyBrain 同构的语义层页面；K1 负责这条新编译链路的内容正确性与保真性。不做的代价：K2/K3/K4 全部建立在一个无法证明「没丢内容」的底座上，验收无从谈起。

## 2. 背景、目标与范围

### 背景

- 冻结语料：`/Users/Hugh/Downloads/confluence 原始数据` 下 4 个顶层目录（`GoInsight` 22 份、`emm for android ` 27 份（目录名有尾随空格）、`emm for ios` 20 份、`merchant system` 20 份）共 89 份 `.md`，无 Confluence 宏 XML。
- 冻结清单：`config/task4-source-coverage-89-input.v1.json`（`input_manifest_id = confluence-raw-89-20260818-v1`；条目字段 `source_uri / source_id / content_hash / byte_count`）；task5 侧 `config/task5-source-page-manifest-v2.json` 的 `source_snapshot` 台账含 `line_count / expected_status`。磁盘 89/89 与清单一致（已核实，RISK-001 已降级）。
- gbrain slug 规则删除全部非 ASCII 字符，且同 slug 按导入覆盖——中文文件名必然碰撞，这是命名契约的硬约束。
- CompanyBrain 正式页契约 = 15 字段 frontmatter 块 + `[[wikilink]]` 双链 + `products/<产品>/<模块>/<页面>.md` 目录；正式块 555 页（口径基准，方言页不作基准也不作反例）。

### 目标

- 89 份冻结语料 → 参考保真（参考型内容逐字零丢失、结构同原文）、逐条可溯（读者见「原始文件+标题」，机器验「指纹+行区间」）、结构同构（16 字段、双链、英文 slug）的语义层知识页，一次运行产出一整个批次目录。
- 同输入重复运行产物字节一致；模型结果冻结成缓存，命中不重调。
- 批次目录带机读批次状态与五份审计文件，K3 可直接区分「完整待发布」与「半成品」。

### 范围内

- 来源读取与冻结清单对账、保真拆块（含整张表聚合）、参考块清单与独立第二方法交叉验证。
- 按标题名确定性主题归组（含显式主题映射机械输入）、页面拼装、同构 frontmatter 与双链、英文 slug 命名。
- 叙述内容逐条带出处组织、模型起标题/写导读（走缓存、逐句可回溯）、五类数据状态的程序化推导。
- 批次目录写入、`_audit/` 五件、机读批次状态、`digest` 命令行为切换、旧行为降级为 `scripts/` 一次性对照脚本。

> 非目标只在第 10 节维护。

## 3. 用户场景与状态覆盖

角色（继承 decision-log J 表）：投料人、读者、下游消费者、维护者。

### SCN-001：正常编译运行（J1→J6 成功路径）

- **角色**：投料人 / 系统
- **Given**：语料目录 89 份与冻结清单一致；provider 配置可用或缓存已冻结
- **When**：运行 `digest`（打印计划后直接执行，不等人确认）
- **Then**：产出一个批次目录：`README.md` + `products/**.md` + `_audit/` 五件；`page-manifest.json` 显示 `publish_status=not_released` + `run_status=complete`；阻塞清单可为空数组

### SCN-002：语料与冻结清单不一致（J1 失败）

- **角色**：系统
- **Given**：语料缺失/多出/任一 `content_hash` 不一致
- **When**：启动对账
- **Then**：本次尝试仍新建批次目录骨架（D-002「每次尝试新建批次」）：写 `README.md`（说明对账失败与差异）、`_audit/run-metrics.json`（真实 0 次 provider 调用，附 `reason=no_provider_call_yet`）、`_audit/page-manifest.json`（`publish_status=not_released`、`run_status=blocked`、阻塞项 = 对账差异全集、页面条目为空）；**不写 `products/`**；显式报告差异后停止；该骨架不得表现为可发布或已完成

### SCN-003：坏表格坏行（J2 边界）

- **角色**：系统
- **Given**：表格粘在 bullet 后、存在 `| | Reseller User Log` 类坏行
- **When**：拆块
- **Then**：坏行原样保留在整块内，不「修正」原文；整块进入参考块清单并可在页面中逐字节对上

### SCN-004：无法解析的结构（J2 失败）

- **角色**：系统
- **Given**：出现拆块器无法归类的结构
- **When**：拆块
- **Then**：该结构原样保留原文字节并进入显式阻塞清单（文件、位置、原因、影响）；不允许静默降级为散文

### SCN-005：跨文件同主题合并与一来源拆多页（J3）

- **角色**：系统
- **Given**：不同文件存在归一化后相同的标题名；某文件含多个互不相关主题
- **When**：主题归组
- **Then**：前者合入同一页（可跨目录同 product 内多来源）；后者拆到多页；`page-manifest.json` 可按任一来源反查它进入了哪些页面

### SCN-006：同义不同名主题（J3/RISK-004 缓解）

- **角色**：系统
- **Given**：「激活&停用」与「Terminal 激活」语义相近但标题名不同
- **When**：归组与建议生成
- **Then**：不自动合并（页面成员由标题名规则单方决定）；疑似对进入 `_audit/suspected-synonyms.md` 供人工处置；人工若采纳，通过显式主题映射机械重算，模型输出永不直接改变页面成员

### SCN-007：模型不可用或缓存缺失（J4 失败/退化）

- **角色**：系统
- **Given**：provider 不可达，或所需模型结果无缓存
- **When**：编译
- **Then**（确定性矩阵，无开放措辞）：① 缓存命中 → 使用冻结缓存产物，行为与 provider 可用时一致；② 缓存缺失且 provider 可用 → 调用并把结果写回缓存（FR-CMP-003）；③ 缓存缺失且 provider 不可用 → 受影响页面标题回退为规范主题标题名（机械值）、导读留空并标注「原文未明确」、该页的同义主题建议缺席，页面其余内容（参考块、叙述 claim）正常产出；阻塞清单记录一项 `model_unavailable_no_cache`（位置=该页主题键，原因=缓存缺失且 provider 不可用，影响=该页标题/导读为回退值）；运行继续，若仅此类降级则 `run_status=complete`；运行指标记录真实调用数（含真实 0，附 `reason=provider_unavailable` 或 `cache_hit`）

### SCN-008：导读句无原文依据（J4/RISK-003）

- **角色**：系统
- **Given**：模型写的某导读句在原文找不到依据
- **When**：导读逐句回溯检查
- **Then**：该页导读整体留空并显式标注；该句在 `_audit/sources.jsonl` 记为 `资料未明确` 状态并附检索证据；不写成结论、不进事实分母

### SCN-009：重复来源（AC-05）

- **角色**：系统
- **Given**：两份来源内容指纹相同
- **When**：去重
- **Then**：canonical 来源正常成页；重复来源记 `duplicate_alias`、单页化、登记别名关系，不发成两页

### SCN-010：known_empty 来源（AC-05 空态）

- **角色**：系统
- **Given**：某来源读得到但拆不出参考块也无叙述内容
- **When**：状态推导
- **Then**：记 `known_empty`；该来源不进任何页面；登记在页面清单的来源台账中

### SCN-011：写入中断（J6 失败）

- **角色**：系统
- **Given**：写入批次目录中途失败（断电/磁盘满/进程被杀）
- **When**：恢复后查看
- **Then**：无有效 `page-manifest.json` 或其中 `run_status=interrupted|blocked`；该批次不得表现为可发布；不删除半成品但也不标完成

### SCN-012：复跑与缓存失效（J8）

- **角色**：用户 / 系统
- **Given**：同一批输入再跑一次；或改动任一来源一个字节后重跑
- **When**：比对
- **Then**：前者产物在 AC-06 比对范围内字节一致；后者受影响页面缓存失效并重算、产物相应变化

### SCN-013：K3 机读交接（J7 下游）

- **角色**：下游消费者（K3 发布通道）
- **Given**：一个批次目录
- **When**：读取 `_audit/page-manifest.json`
- **Then**：可直接区分 `not_released+complete`（完整待发布）与 `interrupted|blocked`（半成品），以及来源快照身份与阻塞项全集

### 状态覆盖清单

- [x] **默认态**：SCN-001
- [x] **空态**：SCN-010（known_empty）；语料目录为空 = SCN-002 的极端情形
- [x] **错误态**：SCN-002 / SCN-004 / SCN-007 / SCN-011
- [x] **加载态**：N/A — 一次运行的 CLI 无中间可观察加载界面；不声明任何本卡之外的运行态写位置
- [x] **取消态**：N/A — 无交互取消；中断语义由 SCN-011 覆盖
- [x] **边界态**：SCN-003 / SCN-005 / SCN-012
- [x] **权限态**：写权边界（只写本次批次目录与仓库内既定路径；CompanyBrain/gbrain/停摆流水线零写入）——默认必须成立，见第 10 节
- [x] **竞态**：N/A — 单写者、一次运行、无并发设计；分批复跑并发不在本卡（D-013）

## 4. 产品事实与假设（PFACT）

- **PFACT-001**：冻结语料为 4 个顶层目录共 89 份 `.md`（目录直下无更深嵌套），13,050 行，无 Confluence 宏 XML，残留仅为 atlassian 绝对 URL/附件 URL/图片引用。
  - **status**：`verified`
  - **证据或来源**：decision-log `## 调研` 取证一（子代理只读，2026-09-13）；本阶段复核目录深度
  - **关联**：FR-SRC-001、FR-GRP-001、FR-PUB-001
- **PFACT-002**：冻结清单身份 = `config/task4-source-coverage-89-input.v1.json`（`input_manifest_id=confluence-raw-89-20260818-v1`）；条目字段 `source_uri/source_id/content_hash/byte_count`；task5 侧台账含 `line_count/expected_status`。磁盘 89/89 与两清单 `content_hash` 一致。
  - **status**：`verified`
  - **证据或来源**：decision-log `## 调研` 取证二；本阶段只读取证复核字段名
  - **关联**：FR-SRC-001、FR-AUD-001、AC-01
- **PFACT-003**：gbrain 的 slug 规则删除全部非 ASCII 字符、空格与 `._-` 保留、同 slug 按导入覆盖；本语料中文名只得 37 个唯一 slug（10 组碰撞覆盖 62 文件）。
  - **status**：`verified`
  - **证据或来源**：decision-log `## 调研` 取证二（gbrain 源码行级核实）
  - **关联**：FR-PUB-001、AC-03
- **PFACT-004**：CompanyBrain 正式页 = 15 字段 frontmatter 块 + `[[wikilink]]` + `products/<产品>/<模块>/<页面>.md`；555 页用正式块（基准）；真实取值样例：`type: reference`、`scope: company`、`tier: 2`、`trust: medium`、`source_status: compiled`、`quality_status: formal`、`created/updated: "YYYY-MM-DD"`、`tags: [company, <product>, <section>]`。
  - **status**：`verified`
  - **证据或来源**：decision-log 字段普查；本阶段只读取证抽样正式页 frontmatter
  - **关联**：FR-PUB-001、AC-03
- **PFACT-005**：外部元数据脚本的 `page_model_for()` 推导规则：`generated_by` 以 `clean_`/`sync_` 开头 → `source`；有 `generated_by` 且非该前缀 → `derived`；文件名以 `总览/索引` 结尾 → `derived`；其余 → `curated`。
  - **status**：`verified`
  - **证据或来源**：decision-log `## 调研`（仓库外脚本行级核实）
  - **关联**：FR-PUB-001、AC-03
- **PFACT-006**：仓库已存在保真取向拆块实现（标题/列表项/表格行/代码块各自成块、字节从不改写），但它把表格拆成单行；本任务必须在其上追加「连续表格行聚合为整张表一块」的步骤，不可原样复用。另已有标题树提取（带 `lines:start-end` 定位）可复用。
  - **status**：`verified`
  - **证据或来源**：decision-log OI-03 / `## 调研`（file:line 级）
  - **关联**：FR-BLK-001、AC-01/AC-02
- **PFACT-007**：旧 reader 路径的固定 240 行窗口拆块与文本改写（清洗/链接重写）必须绕开。
  - **status**：`verified`
  - **证据或来源**：decision-log OI-03 / `## 调研`
  - **关联**：FR-BLK-001、AC-02
- **PFACT-008**：基线测试 `16 failed, 892 passed, 3 skipped`（退出码 1），16 个失败全部挂在旧 reader bundle 路径（`test_task2a_reader_bundle.py`）。
  - **status**：`verified`
  - **证据或来源**：decision-log `## 调研` 取证二
  - **关联**：FR-REG-001、AC-10
- **PFACT-009**：K1 对 CompanyBrain 的 1347 个页面完全不读、不合并、不比对；CompanyBrain 已有同主题正式页（RISK-011），取代关系归 K3（DEF-008）。
  - **status**：`verified`
  - **证据或来源**：decision-log OI-17 / D-014 / RISK-011
  - **关联**：第 10 节、第 12 节
- **PFACT-010**：冻结的 89 案例 oracle（task5 清单 entries）`page_type` 全为 `procedure`、`criticality` 全为 `non_critical`、无 product/module/topic_key 字段、`companybrain_entry_path` 全为 null——不能充当主题归组或页面期望清单的基准。
  - **status**：`verified`
  - **证据或来源**：decision-log `## 调研` 取证二
  - **关联**：FR-GRP-001（解释为何归组基准只能是标题名）
- **PFACT-011**：语料 89 份中 0 份有 frontmatter，仅 3 份含 H1；产品/模块分层无法从 frontmatter 取得。
  - **status**：`verified`
  - **证据或来源**：decision-log `## 调研` 取证一
  - **关联**：FR-PUB-001（product/module 推导契约）
- **PFACT-012**：`digest` 当前注册入口为 `simple_cli:main`，位置参数 `new_dir/kb_dir`（均可缺省），`--no-llm` 转调旧离线 main；旧行为与 518 个测试绑定。
  - **status**：`verified`
  - **证据或来源**：本阶段只读取证（pyproject 注册行、simple_cli 签名）
  - **关联**：FR-CLI-001、AC-09/AC-10
- **PFACT-013**：语料内源文件 mtime 是当前唯一可得的「来源时间」确定性事实（语料无 git 无 frontmatter）。
  - **status**：`inferred`
  - **证据或来源**：本阶段只读取证（目录形态推断）；限制：mtime 是文件系统元数据，语料整体被重新拷贝/导出时可能变化——已登记 RISK-015
  - **关联**：FR-PUB-001（created/updated 契约）

## 5. 功能需求

### 投料与运行（SRC）

投料阶段把「冻结清单对账 + 计划预告」做成一个无人值守的入口：对账不过就显式停止，对账通过就打印计划直接跑完。

- **FR-SRC-001**：启动时以 `config/task4-source-coverage-89-input.v1.json`（`input_manifest_id=confluence-raw-89-20260818-v1`）为对账基准，逐份核对语料目录的存在性与 `content_hash`；对账失败的处置（SCN-002）：本次尝试仍新建批次目录骨架——`README.md`（失败说明与差异）、`_audit/run-metrics.json`（真实 0 调用，附 `reason=no_provider_call_yet`）、`_audit/page-manifest.json`（`publish_status=not_released`、`run_status=blocked`、阻塞项 = 对账差异全集、页面条目为空）；不写 `products/`；显式报告差异后停止。
  - **范围边界**：只核对清单内 89 份；不重新采样、不核对语料内容之外的状态；对账失败也不得跳过批次状态与成本记账（AC-08/AC-12 同样约束失败运行）
  - **依据**：R-026 / R-011；PFACT-002；decision-log J1；D-002「每次尝试新建批次」
  - **场景**：SCN-001 / SCN-002
  - **验收**：AC-01（基准一致性）、AC-08、AC-12
- **FR-SRC-002**：对账通过后、编译开始前，打印本次运行计划（来源数、合并后主题数、预计页面数、预计 provider 调用数），不等待人工确认直接执行。
  - **范围边界**：计划数由主题数机械推导（上界见 FR-AUD-005）；不打印、不记录任何凭据
  - **依据**：用户 Q21；D-012；OI-16
  - **场景**：SCN-001
  - **验收**：AC-12

### 拆块（BLK）

拆块以保真为第一目标：整块单元、字节从不改写、坏行原样保留；解析不了就进阻塞清单。

- **FR-BLK-001**：逐份解析 Markdown，标题、列表项、代码块各自成块；**连续表格行必须聚合为整张表一块**（不得按行成块）；整张表/整个参数列表/整段报错文案 = 一个逻辑单元；块带来源路径、块内容 sha256、行区间、块类型。字节从不改写；坏表格坏行原样保留而不是「修正」原文。块边界与类型判定是主方法与独立第二方法共享的同一份契约：判定优先级从高到低为 `table`（连续表格行序列，含表头与分隔行；以 `|` 起止的坏行归属该表；表格可与前导 bullet 粘连，但边界不含前导 bullet）→ `list`（同列表类型的连续项，含缩进子项）→ `code`（fenced 或缩进代码段）→ `attachment_refs`（仅由图片/附件 URL 行构成的连续行组）→ `error_text`（含报错特征的连续行段：异常类名/错误码/堆栈行）→ 其余为叙述内容；无法判类的行原样保留、就近归属或进阻塞清单（FR-BLK-002），每类边界各配 fixture（测试层归 plan/tasks）。
  - **范围边界**：参考型单元整块化；叙述型段落按原文切片进入 claim 管道（FR-AUD-002），两者都不经模型
  - **依据**：R-028；D-010；OI-09；PFACT-006/007
  - **场景**：SCN-001 / SCN-003
  - **验收**：AC-01、AC-02
- **FR-BLK-002**：解析不了的结构显式标注并进入阻塞清单（文件、位置、原因、影响），原样保留其原文字节；不允许静默跳过、不允许静默降级为散文。
  - **范围边界**：阻塞清单是解析失败的唯一去处；写入侧失败语义另见 FR-AUD-004
  - **依据**：R-024；D-008；OI-15
  - **场景**：SCN-004
  - **验收**：AC-08

### 主题归组（GRP）

页面成员由确定性规则单方决定：标题名归一化后在 product 作用域内精确匹配；模型只产建议，永不改变成员。

- **FR-GRP-001**：在 product 作用域内按标题名做确定性归组：归一化规则 = Unicode NFC → 去除首尾空白 → 内部连续空白压为单空格 → ASCII 大小写归一（小写）；归一化后标题名相同的章节合入同一主题组，每组合为一页；同一输入每次运行得到完全相同的页面划分。一份文件的不同主题可拆到多页。product = 语料顶层目录名（slug 化）；模块 = 该主题组成员章节标题路径的公共 H2 级祖先（无公共 H2 时为 `_general`），slug 化。显式主题映射存于仓库内固定配置文件（确定性输入）：文件中的 `别名 → 规范主题` 机械合并，文件缺失或为空 = 纯标题名归组。
  - **范围边界**：归组不跨 product；归一化只含上述四步，不引入语义相似度；配置文件由人编辑、机器读取，模型不可写
  - **依据**：R-021 / R-015；D-003；OI-05；PFACT-010/011
  - **场景**：SCN-005
  - **验收**：AC-06（划分一致）、AC-05（fixture）
- **FR-GRP-002**：模型对主题相似性的判断只作为建议输出到 `_audit/suspected-synonyms.md`；建议不改变页面成员。人工采纳建议的唯一路径是编辑显式主题映射后整体重跑（机械重算）。
  - **范围边界**：报告由确定性模板承载；建议内容本身经缓存冻结，同输入两次运行报告字节一致
  - **依据**：D-007（detail-advice D-F2/D-F16 澄清）；RISK-004/013
  - **场景**：SCN-006
  - **验收**：AC-06

### 语义编译（CMP）

编译阶段搬运参考内容（逐字）、组织叙述内容（逐条带出处）、让模型只做标题与导读且全程走缓存。

- **FR-CMP-001**：参考块内容在页面中逐字节搬运，表格/列表结构保留；图片与附件 URL 原样保留并显式标注为外部资源链接（不下载、不改写、不删除）。
  - **范围边界**：标注文案为固定模板句；URL 语义不变
  - **依据**：R-028 / R-029；D-010
  - **场景**：SCN-001 / SCN-003
  - **验收**：AC-02
- **FR-CMP-002**：叙述型内容按原文切片组织进页面，字节不改写；每条叙述显示「原始文件名 + 文件内标题路径」，不显示行号；机器侧逐 claim 登记「文件 + 内容指纹 + 行区间 + 页内锚点」到 `_audit/sources.jsonl`，页面正文 claim 与旁路记录可一对一交叉核对（零无锚点 claim）。
  - **范围边界**：双轨出处的读者面与机器面分工固定；行号只存在于旁路文件
  - **依据**：R-015 / R-019 / R-020；D-004 / D-005；OI-10/12
  - **场景**：SCN-001
  - **验收**：AC-04、AC-11
- **FR-CMP-003**：模型只用于起页面标题与写导读（及对主题的「建议」，见 FR-GRP-002）；禁止改写参考型内容与叙述型正文；模型结果冻结成任务级缓存，键 = 模型标识 + 提示模板版本 + 主题映射版本 + 页面复合输入指纹；页面复合输入指纹 = 该页全部成员来源的 `content_hash` 按确定性顺序（规范主题键升序）拼接后取 sha256，与页面主题键绑定——成员来源的增删、任一成员内容变化、主题映射版本变化都使键变化；命中不重调，缺缓存必须重新调用并把结果写回缓存，不得静默产出不同内容。provider 不可用与缓存缺失的确定性处置矩阵见 SCN-007。
  - **范围边界**：缓存持久化位置与生命周期归 build-plan 实现（OPEN-002）；键构成、复合输入指纹与「缺缓存必须写回」是产品契约
  - **依据**：R-022 / R-023；D-007；OI-07/20
  - **场景**：SCN-001 / SCN-007 / SCN-012
  - **验收**：AC-06、AC-12
- **FR-CMP-004**：导读逐句可回溯原文；任一句无依据则该页导读整体留空并显式标注（「原文未明确」），该句记为 claim 级 `资料未明确` 并附检索证据，不写成结论、不进事实分母。
  - **范围边界**：导读是模型唯一可写的正文；留空页的其余部分不受影响
  - **依据**：RISK-003；D-007；AC-04/05
  - **场景**：SCN-008
  - **验收**：AC-04、AC-05

### 页面与批次目录（PUB）

页面是与 CompanyBrain 同构的可消费产物；批次目录是带机读状态的交付单元。

- **FR-PUB-001**：每页 frontmatter 覆盖 15 字段正式块 + 复用的 `source` 字段（共 16 个受校验字段）：`title`（中文标题，模型起、缓存冻结）、`type: reference`、`page_model: derived`、`scope: company`、`product`（目录名 slug）、`section`（模块目录名）、`module`（同 section，目录层取模块层名）、`tier: 2`、`trust: medium`、`source_status: compiled`、`quality_status: formal`、`created/updated`（见下）、`generated_by: knowledge_digest_semantic_compiler.py`、`tags: [company, <product>, <section>]`。`created` = 该页全部来源中最早的来源 mtime 归一化到日（`YYYY-MM-DD`）；`updated` = 最晚来源 mtime 归一化到日；两者不取运行时刻。`source` 字段：单来源页写 `<语料根目录名>/<语料根内相对路径>`；多来源合并页写主来源路径，其后以 `; ` 分隔列出其余来源（同一根、同一形态）。页面文件名与目录名为英文 slug，是 gbrain 归一化的不动点（经 gbrain slug 规则作用后不变）、批内唯一、不依赖任何导入顺序。页面内 `[[wikilink]]` 双链可解析：当本页叙述文本中原样出现另一页的规范主题标题名时，在「相关页面」节按固定模板给出指向该页 slug 的 wikilink。
  - **范围边界**：16 字段取值以上述为准，不新增字段名；slug 具体生成/碰撞后缀算法归 build-plan（OPEN-003），本契约只固定「gbrain 不动点 + 批内唯一 + 确定性 + 不依赖导入顺序」
  - **依据**：R-013 / R-035 / R-036 / R-039；D-005 / D-006 / D-015；OI-08/11/12；PFACT-003/004/005/011/013
  - **场景**：SCN-001 / SCN-005
  - **验收**：AC-03、AC-06
- **FR-PUB-002**：每次运行在冻结父目录 `/Users/Hugh/Downloads/KD测试` 下新建批次目录，命名 = `<YYYY-MM-DD>-<当天自增序号>`（从 1 起，扫描既有兄弟目录确定）；目录内固定为 `README.md` + `products/<产品>/<模块>/<页面>.md` + `_audit/{reference-blocks.jsonl, sources.jsonl, page-manifest.json, run-metrics.json, suspected-synonyms.md}`。`README.md` 与 `suspected-synonyms.md` 由确定性模板生成：不写批次名、运行时刻、实际调用数。
  - **范围边界**：父目录冻结值不可由运行自行改向；批次目录名与运行级字段不参与产物字节比对（AC-06）
  - **依据**：R-018 / R-031 / R-040；D-002 / D-017
  - **场景**：SCN-001
  - **验收**：AC-06、AC-08
- **FR-PUB-003**：单页叙述正文不超过 300 行，超出必须分页；每个 claim 只进入一个 part；旧 part 不删除（本卡无原子发布，分页为单批内结构）；失败运行不产出「已完成」产物。**受控豁免**：单个参考块超 300 行时整块不切断（AC-02 优先），该块独占一个参考附录 part，part 头标注 `oversized_reference_block: true`；300 行上限对叙述正文与导读仍硬生效；覆盖校验把「块 → 该附录 part 锚点」视为合法承载。
  - **范围边界**：300 行硬上限继承母任务 S6；分页只在本批次目录内生效
  - **依据**：R-016；D-013
  - **场景**：SCN-001 / SCN-011
  - **验收**：AC-07

### 审计与状态（AUD）

审计面让「没丢、没改写、可回溯、状态可复算」全部机器可验。

- **FR-AUD-001**：生成 `_audit/reference-blocks.jsonl`：每块一条 `{block_id, source_path, content_hash, block_kind, line_start, line_end, page_path, page_anchor, status, alias_of?, canonical_block_id?}`；`block_id` 由来源路径+行区间+内容指纹确定性导出。用独立第二方法（与主拆块器不同策略的扫描器，但共享 FR-BLK-001 的边界与类型契约）生成可比清单并逐块交叉验证（集合与指纹一致）。覆盖不变量：每块要么有唯一输出锚点（`page_path` + 标题路径内块序号），要么出现在阻塞清单，要么以 `status=duplicate_alias` 登记别名承载——别名记录写 `alias_of`（canonical 来源路径）与 `canonical_block_id`，其 `page_anchor` 复用 canonical 块锚点（登记为别名承载，不产生新锚点）；覆盖校验走「canonical 覆盖 + alias 登记」分支，不判第三态、不判锚点重复。
  - **范围边界**：第二方法只用于交叉验证，不进入产物；`block_kind` 枚举（table/list/code/error_text/attachment_refs）按 Markdown 结构确定性分类
  - **依据**：R-034；D-011；OI-21；AC-01/13
  - **场景**：SCN-001 / SCN-004
  - **验收**：AC-01、AC-13
- **FR-AUD-002**：生成 `_audit/sources.jsonl`：每条 claim `{claim_id, source_path, content_hash, line_start, line_end, char_start, char_end, page_path, page_anchor, span_start, span_end, claim_kind, status, retrieval_evidence?}`；`claim_id` 稳定 = `cl_` + sha256(`source_path` + 行区间 + char 区间 + `occurrence_index` + 规范化文本) 前 12 位十六进制，`occurrence_index` = 同一来源内相同规范化文本的出现序号（从 1 起），同来源同行的重复 claim 因此不碰撞；`claim_kind ∈ narrative | intro`；`status ∈ sourced | 原文未明确`（`资料未明确` 的运行内值即「原文未明确」）。正文↔旁路映射为 span 级：页面正文中每个非模板文本 span 必须映射到恰好一条旁路记录（按 `page_path + page_anchor + span_start/span_end` 定位），多 claim 句逐条映射（句内 char 区间互不重叠）；导读被移除的无依据句以 `claim_kind=intro`、`status=原文未明确`、`page_anchor=intro`（对应页面导读标注行）登记，`retrieval_evidence` 对此状态必填。待验证事实全集 = 本次运行写入旁路的全部记录（含 intro 被拒候选）；事实分母 = 其中有原文依据的 claim 数；`资料未明确` 不进分母、不写成结论。
  - **范围边界**：claim 切分规则 = 句子级（句号/问号/叹号/分号/换行切分）且不切散原文行；schema 字段名以上述为准
  - **依据**：R-015；D-004 / D-005；OI-10/12；OPEN-012（本阶段冻结）
  - **场景**：SCN-001 / SCN-008
  - **验收**：AC-04、AC-05、AC-11
- **FR-AUD-003**：五类数据状态全部由程序从事实推导，两个层级分别判定——来源级：`ready`（读得到且能拆出块）、`known_empty`（读得到但拆不出参考块也无叙述内容）、`duplicate_alias`（内容指纹与其他来源相同且已有 canonical；按内容判定，与 product 无关，页面归属 canonical 来源的 product）、`audit_only`（**必须由确定性输入声明**——冻结台账 task5 `source_snapshot.expected_status` 的声明值或运行配置的显式来源列表；程序核验该来源的块确实零进入 `products/`，核验不通过即状态冲突、进阻塞清单；未声明而块零入 `products/` 的来源不得记 `audit_only`，同样按状态冲突进阻塞清单——禁止用输出缺失反推状态）；claim 级：`资料未明确`（见 FR-AUD-002）。判定规则可复算，不由模型判定、不留人工标注。来源级状态写入 `_audit/page-manifest.json` 的来源台账（见 FR-AUD-004）。
  - **范围边界**：来源级状态写入 `_audit/page-manifest.json` 来源台账；fixture 逐类可构造（AC-05）
  - **依据**：R-014 / R-025；D-009；OI-13；OPEN-009（本阶段冻结）
  - **场景**：SCN-008 / SCN-009 / SCN-010
  - **验收**：AC-05
- **FR-AUD-004**：生成 `_audit/page-manifest.json`：机读批次状态字段 `publish_status ∈ not_released | released`（本卡恒 `not_released`，`released` 保留给 K3）、`run_status ∈ complete | blocked | interrupted`、`attempt_id`、来源快照身份（冻结清单 id + 89 份路径与内容指纹）、阻塞项全集（可为空数组）、页面条目（含主题键、来源列表、claim/块计数）、来源→页面反查表、**来源台账**（每来源 `{source_path, content_hash, source_status, alias_of?, pages: [...]}`，`source_status` 为 FR-AUD-003 四态）。写入顺序上 manifest 最后落盘：中断批次要么 manifest 缺失/无效，要么 `run_status=interrupted|blocked`，不得表示为可发布；对账失败的批次骨架同样写入 manifest（`run_status=blocked`、页面条目为空，见 FR-SRC-001）。
  - **范围边界**：批次目录名与 `attempt_id` 不参与 AC-06 产物比对；状态词表与母任务状态链对齐
  - **依据**：R-024；D-008 / D-017；OI-15/21；AC-08
  - **场景**：SCN-011 / SCN-013
  - **验收**：AC-08
- **FR-AUD-005**：生成 `_audit/run-metrics.json`：耗时、provider 调用数、token 数、缓存命中数、阻塞清单；成功与失败运行都记录，三项成本计数（耗时/调用数/token）真实非 null；真实发生的 0 合法，原样记录并附 `reason`（`cache_hit` / `no_provider_call_yet` / `provider_unavailable`）；无法归因的 0 或与 `reason` 矛盾的计数判失败。运行前计划调用数 ≤ 合并后主题数 × 2 + 20；实际调用数 ≤ 计划 × 1.5；调用数不得随 claim 数或块数线性增长。
  - **范围边界**：预算上界为可复算硬约束；token 数按 provider 返回真实记录
  - **依据**：母任务成本硬约束；OI-20；AC-12
  - **场景**：SCN-001 / SCN-007
  - **验收**：AC-12

### 命令与回归（CLI / REG）

- **FR-CLI-001**：`digest` 命令执行新的语义编译行为；旧行为完整降级为 `scripts/` 下一次性对照脚本（保留相同能力以便对照）；两者互不影响。命令输入 = 冻结语料目录（对账见 FR-SRC-001）；产物父目录按 FR-PUB-002 冻结值。参数形态细节归 build-plan。
  - **范围边界**：不新增子命令；不做输入形状自动识别
  - **依据**：R-041；D-018；OI-14；PFACT-012
  - **场景**：SCN-001
  - **验收**：AC-09
- **FR-REG-001**：回归口径按 AC-10 冻结：与 `digest` 入口绑定的既有测试随旧路径改挂脚本或标废弃（不计新增失败）；不绑定该入口的测试（含 16 个既有失败）节点 ID 与失败原因逐一不变；基准 = 精确节点 ID 清单 + 测试清单 + 分类清单，不以计数为准；若 build-plan 决定修复某既有失败，作为受控基线变更记录（含原因与节点 ID）。
  - **范围边界**：本卡不修这 16 个失败（根因调查归 build-plan，OPEN-001/DEF-006）
  - **依据**：R-037；D-016；OI-14
  - **场景**：SCN-001（回归面）
  - **验收**：AC-10

## 6. 模块划分（产品职责）

> 只写产品职责边界，不写实现类名。

### 投料与对账

- **负责什么**：语料目录与冻结清单的对账、运行计划预告
- **对外提供什么**：通过/停止的明确判定与差异报告
- **依赖谁**：冻结清单（仓库内既定文件）、语料根目录
- **测试边界**：一致时放行；任一差异时停止且不产生产物

### 保真拆块与块清单

- **负责什么**：整块单元拆块、字节不改写、块级指纹与行区间、独立第二方法交叉验证
- **对外提供什么**：参考块全集清单（含锚点或阻塞归属）
- **依赖谁**：投料与对账
- **测试边界**：块集合与第二方法一致；坏行原样；零静默跳过

### 主题归组

- **负责什么**：标题名归一化、product 作用域分组、显式主题映射应用
- **对外提供什么**：确定性的主题组 → 页面划分
- **依赖谁**：拆块产物、显式主题映射配置
- **测试边界**：同输入划分恒定；模型建议不改变成员

### 语义编译与页面拼装

- **负责什么**：参考块逐字入页、叙述 claim 组织与读者侧出处、模型标题/导读（缓存冻结）、frontmatter 与双链、slug、分页
- **对外提供什么**：同构页面字节
- **依赖谁**：主题归组、模型缓存、slug 契约
- **测试边界**：16 字段断言、双链可解析、300 行上限、逐字节保真

### 审计与批次状态

- **负责什么**：五件 `_audit/` 产物、五类状态推导、批次状态、成本记账
- **对外提供什么**：机器可验的保真证据与 K3 可机读交接
- **依赖谁**：前述全部阶段的事实输出
- **测试边界**：覆盖不变量、零无锚点 claim、状态 fixture 逐类核对

## 7. 关键实体

- **批次目录**：一次运行的交付单元；父目录冻结为 `/Users/Hugh/Downloads/KD测试`；名 `<YYYY-MM-DD>-<n>`；定位 = 临时对照产物（不是语义层、不是知识库）。
- **页面**：一个主题组一 Page；路径 `products/<product>/<module>/<slug>.md`；frontmatter 16 字段；正文 = 参考块 + 叙述 claim + 导读 + 相关页面。
- **主题组**：归一化标题名（product 作用域）+ 成员章节集合；页面成员的唯一定义。
- **参考块**：整张表/整个列表/整段报错文案等整块单元；带 `block_id`、指纹、行区间、输出锚点。
- **claim**：叙述内容的最小可溯源单元（句子级）；带 `claim_id`、指纹、行区间、char 区间、页内锚点、状态。
- **来源（source）**：89 份冻结语料之一；身份 = 冻结清单 `source_uri` + `content_hash`。
- **显式主题映射**：人编辑的机械配置文件；`别名 → 规范主题`；模型不可写。
- **模型缓存**：任务级固定位置；键 = 来源内容指纹 + 模型标识 + 提示模板版本 + 主题映射版本。

## 8. 数据和生命周期

- **数据粒度**：块（参考型整块）与 claim（叙述型句子级）双粒度；页面由主题组装配。
- **数据时效**：来源冻结后内容不变；`created/updated` 取来源 mtime 日级归一化，不取运行时刻；缓存随输入指纹失效。
- **缺失或迟到**：语料差异→停止（SCN-002）；provider 不可用→退化或显式阻塞（SCN-007）；缺缓存→重调并写回。
- **预览与正式**：本卡只有正式批次目录一种产物；无预览态。
- **当前与历史**：批次目录之间不合并、不增量；每次运行独立成批；历史批次保留不做清理（清理归用户/K3）。
- **归属与清理**：批次目录归投料人所有；`_audit/` 与正文同批写出；临时对照产物的正式留存由 K3 发布通道负责。

## 9. 兼容性预留

- **既有消费方**：Obsidian 读者按目录/中文标题浏览（同构保障）；下游按路径/slug 检索（slug 批内唯一保障）；K3 按 manifest 机读交接。
- **命名预留**：英文 slug + 中文 `title` 的双轨命名对 gbrain 归一化稳定；`generated_by` 命名遵守既有 `*.py` 生成器习惯。
- **容器预留**：`products/<product>/<module>/` 两层目录容纳后续 K2 导航挂接；`_audit/` 五件为 K2/K3 既定输入。
- **状态预留**：`publish_status` 词表保留 `released` 给 K3；`run_status` 三态覆盖中断语义；五类数据状态词表与母任务 S3 对齐。
- **扩展边界**：本卡不预留入口页、发布回滚、查询集验收的接口；多格式输入不做。

## 10. 明确不做与默认必须成立

### 明确不做

- NG-001 不依赖 build-spec 补齐需求（需求已在 make-decision 收敛）。
- NG-002 主会话不做重读取证（取证派子代理）。
- NG-003 不做入口页与分类导航，不做「从入口可达每一页」检查（K2）。
- NG-004 不做 staging 校验→原子切换→last-known-good→回滚与四类负例注入（K3）；本卡不具备写入中断不留半成品的保证，该限制显式保留。
- NG-005 不做源码瘦身删码与三项度量（K4）。
- NG-006 不做真实查询集对照验收（K3）。
- NG-007 不引入向量库/图数据库/服务化/前端/多格式输入。
- NG-008 不改 CompanyBrain 既有正式页、不改停摆自动化流水线、不改 gbrain 配置与索引状态、不下载语料图片与附件。
- 分批与恢复能力本卡不激活（D-013）：一次运行处理全部 89 份，不实现调度/中断续跑。

### 默认必须成立

- 写权受限：运行只写本次批次目录与仓库内既定路径（显式主题映射配置为只读输入）；CompanyBrain/gbrain/停摆流水线零写入（关联 FR-PUB-002、NG-008）。
- 失败不伪装成功：任何跳过、阻塞、中断都在 `_audit/` 与批次状态中显式可见（关联 FR-BLK-002/FR-AUD-004）。
- 可重复运行：同输入产物字节一致，模型结果冻结（关联 FR-CMP-003、AC-06）。
- 不丢内容：参考块零丢失且逐块可回原文（关联 FR-AUD-001）。
- 同输入页面划分恒定（关联 FR-GRP-001）。

## 11. 验收标准

- [ ] **AC-01**：参考块清单零丢失且经独立第二方法交叉验证
  场景：对 89 份输入生成 `_audit/reference-blocks.jsonl`，每块带 `source_path`、`content_hash`、`line_start/line_end`、`block_kind`、唯一输出锚点；独立第二方法清单与主清单逐块一致；任一块缺失、错位、指纹不一致即失败；每块要么有锚点要么在阻塞清单，无第三态（AC-13）。
验证：机器全量比对两份清单集合与指纹 + 覆盖关系机械检查 + 人工抽 20 块逐字复核。
通过：两份清单逐块一致；覆盖关系双向可反查。
失败：任一块缺失/错位/指纹不一致；第二方法发现而主方法缺失；存在既无锚点也不在阻塞清单的块。
证据：test（清单比对脚本产出）+ evidence（抽样复核记录）。

- [ ] **AC-02**：参考内容逐字保真
  场景：每个参考块在页面中的文本与原文对应行区间逐字节一致（表格/列表结构保留）；图片与附件 URL 原样保留且带显式外部资源标注。
验证：机器逐块 diff（从原文按行区间切片与页面切片比对）。
通过：全部块字节一致、URL 未改写、坏行原样。
失败：任一处语义改写、字段丢失、结构破坏、块被从中间切断、URL 被改写或删除。
证据：test。

- [ ] **AC-03**：同构页面编译
  场景：抽 10 页做结构/元数据校验：16 个受校验字段齐备（15 字段正式块 + `source`）；`page_model=derived`、`generated_by=knowledge_digest_semantic_compiler.py` 断言成立；`source` 可解析到本次语料具体文件并标注语料根目录；`[[wikilink]]` 双链可解析；文件名与目录名为 gbrain 归一化不动点且批内唯一。
验证：校验脚本（字段断言 + slug 唯一性检查 + 双链解析）。
通过：全部断言通过。
失败：任一字段不符、断言失败、`source` 缺失或不可解析、slug 非法或批内重复、双链不可解析。
证据：test。

- [ ] **AC-04**：claim 级溯源零违规
  场景：机械扫描零「无出处结论」：每条 claim 带 `source_path` + 内容指纹 + 行区间（+ char 区间）；多 claim 句子逐条映射；回不到原文的内容只出现在 `资料未明确` 且显式标注并带检索证据；模型导读逐句可回溯。
验证：解析器扫描 `_audit/sources.jsonl` 零违规 + 导读逐句回溯检查。
通过：零无定位肯定句、零错定位、多 claim 全逐条映射、导读句句有依据。
失败：出现无原文定位的结论行、错定位、未逐条映射、导读含原文没有的信息。
证据：test + evidence。

- [ ] **AC-05**：五类数据状态一致
  场景：来源级四态与 claim 级一态分属两层分别判定（规则见 FR-AUD-003，`audit_only` 必须由确定性输入声明并经程序核验，禁止用输出缺失反推）；构造五类 fixture 逐类核对：状态与正文一致；重复来源单页化（alias 登记见 AC-13 分支）；`资料未明确` 不写成结论、不进事实分母（分母 = 待验证事实全集中有原文依据的 claim 数）；来源级状态逐条写入 manifest 来源台账。
验证：五类 fixture 逐类核对 + 两个层级判定规则可执行。
通过：逐类状态正确、层级不混用、分母口径正确。
失败：重复来源发成两页；未明确写成结论或进入分母；来源级与 claim 级混用。
证据：test。

- [ ] **AC-06**：可重复运行
  场景：同批输入连跑两次，比对范围（`products/**` 全部字节 + `_audit/**` 中逐块/逐条产出内容：`reference-blocks.jsonl`、`sources.jsonl`、`suspected-synonyms.md`、`page-manifest.json` 的页面条目部分）字节一致；排除批次目录名、`attempt_id`、`run-metrics.json` 计时数据；改任一来源一个字节后受影响页面缓存失效并重算；`created/updated` 取来源确定性事实；README 由确定性模板生成。
验证：两次运行产物 diff（按上述范围）+ 缓存失效负例 + 时间戳确定性检查。
通过：比对范围内零差异；来源变化正确失效；缓存缺失时重调并写回。
失败：比对范围内任何字节差异；产物抖动；来源变化而缓存误命中。
证据：test。

- [ ] **AC-07**：结构不变量
  场景：单页叙述正文不超过 300 行，超出分页且每 claim 只进一个 part；来源去重生效；失败运行不产出「已完成」产物；单个参考块超 300 行时按 FR-PUB-003 受控豁免整块入参考附录 part（part 头标注 `oversized_reference_block: true`），覆盖校验视其为合法承载。
验证：分页与去重断言 + 失败注入。
通过：无超限页、无重复承载 claim、失败语义正确。
失败：页面超限、claim 重复进入多个 part、失败被写成完成。
证据：test。

- [ ] **AC-08**：阻塞显式化与批次状态可机读
  场景：无法处理的内容产出显式阻塞清单（文件、位置、原因、影响），产物无静默跳过；`_audit/page-manifest.json` 带机读批次状态（`publish_status`、`run_status`、`attempt_id`、来源快照身份、阻塞项全集）；K3 能区分「完整待发布」与「半成品」；不得把中断或部分完成批次表示为可发布。
验证：阻塞清单存在性与覆盖检查 + 批次状态字段校验 + 故意中断负例。
通过：阻塞清单覆盖所有未处理项；状态字段齐备且语义正确。
失败：存在静默跳过、阻塞清单缺失、缺批次状态字段、未完成批次标为 `complete`。
证据：test。

- [ ] **AC-09**：命令与旧路径隔离
  场景：`digest` 执行新语义编译行为；旧行为由 `scripts/` 下一次性对照脚本承载且保留相同能力；两者互不影响。
验证：命令行为断言 + 旧脚本可运行。
通过：新命令走新链路；旧脚本独立可跑。
失败：新命令仍走旧路径，或旧脚本无法运行。
证据：test。

- [ ] **AC-10**：回归口径
  场景：新链路自身测试全绿；回归基准按分类清单定义：绑定旧 `digest` 入口的行为测试改挂脚本或标废弃（不计新增失败）；不绑定该入口的测试（含 16 个既有失败）节点 ID 与失败原因完全不变；基准 = 精确节点 ID 清单 + 测试清单，不以计数为准；若 build-plan 修复某既有失败，以受控基线变更记录。
验证：精确节点 ID 集合比对 + 测试清单比对 + 分类清单。
通过：非绑定用例无新增失败；16 个既有失败 ID 与原因不变。
失败：非绑定用例新增失败、既有失败 ID/原因变化、用例集合变化而计数掩盖。
证据：test。

- [ ] **AC-11**：读者侧出处呈现
  场景：页面正文对每条叙述显示「原始文件名 + 文件内标题」，不显示行号；页头 `source` 可解析；`_audit/sources.jsonl` 逐条带指纹与行区间，且与页面正文 claim 可交叉核对（扫正文零无锚点 claim，不只扫旁路文件）。
验证：页面渲染检查 + `source` 可解析性检查 + 正文扫描与旁路交叉核对。
通过：显示合规、无行号、解析成功、正文零无锚点 claim。
失败：页面不显示文件+标题、显示行号、`source` 缺失或不可解析、正文存在无锚点 claim。
证据：test + evidence。

- [ ] **AC-12**：成本与失败记账
  场景：运行前打印计划调用数；实际 ≤ 计划 × 1.5 且计划 ≤ 合并后主题数 × 2 + 20；不随 claim 数或块数线性增长；`run-metrics.json` 对成功与失败运行都记录耗时、调用数、token（真实非 null）；真实 0 合法并附 `reason`；无法归因的 0/null/矛盾计数判失败。
验证：计划/实际调用数比对 + 两类运行的指标字段检查。
通过：预算上界成立；字段真实完整；真实 0 有因。
失败：逐 claim 调用；任一计数 null/伪造；缺该文件。
证据：test。

- [ ] **AC-13**：来源→输出覆盖不变量
  场景：`_audit/reference-blocks.jsonl` 每条带 `block_id` 与输出锚点（`page_path` + 页内定位：标题路径内块序号）；每条要么有非空锚点、要么出现在阻塞清单、要么以 `status=duplicate_alias` 走别名承载分支（写 `alias_of` + `canonical_block_id`，复用 canonical 锚点、不产生新锚点）；`page-manifest.json` 可反查「一份来源 → 哪些页面」，来源台账含 `alias_of` 与 `source_status`。
验证：覆盖关系机械检查（block_id 集合 ↔ 锚点集合 ↔ 阻塞清单）+ 来源→页面反查。
通过：双向覆盖、锚点唯一、重复标注、反查可得。
失败：存在第三态块、锚点不唯一、重复承载未标注、来源无法反查。
证据：test。

## 12. 风险、未决与交接

### 风险（继承 decision-log 风险台账；本阶段新增 RISK-015）

- **RISK-002**：K1 无原子发布能力，写入中断可能留半成品。缓解：AC-08 显式报告 + K3 根除。处理 Stage：K3。
- **RISK-003**：导读引入无依据信息。缓解：FR-CMP-004 逐句回溯 + 留空规则（AC-04）。处理 Stage：build-code 验证。
- **RISK-004**：同义不同名归并不彻底。缓解：FR-GRP-002 疑似同义报告 + 显式主题映射。接受。
- **RISK-005**：缓存误命中。缓解：缓存键绑定内容指纹 + AC-06 负例。
- **RISK-006**：Downloads 批次目录可能被清理。缓解：用户已知悉；正式留存归 K3。
- **RISK-007**：gbrain 实际检索未验证（DEF-002）。本卡只断言 slug 合法且批内唯一（AC-03）。
- **RISK-008**：task4 `manifest_hash` / task5 `snapshot_id` 聚合哈希不可复算。登记为事实缺陷；不作为完整性凭证（DEF-007）。
- **RISK-009**：基线测试为红。缓解：AC-10 精确节点 ID 口径；不修这 16 个（OPEN-001/DEF-006 归 build-plan）。
- **RISK-010**：`source` 沿用既有字段易被误读为 SourceArchive 路径。缓解：根目录名首段标注 + README 说明 + K3 决定是否先归档语料。
- **RISK-011**：K1 产物与 CompanyBrain 既有同主题页冲突。处理 Stage：K3（DEF-008 取代关系）。
- **RISK-012**：ADR 0013 唯一新字段授权悬空。本任务不使用该授权；K3 重新决定（G-001）。
- **RISK-013**：模型建议 vs 机械决定边界若实现模糊会破坏可重复性。缓解：FR-GRP-002 写入产品契约。
- **RISK-014**：`资料未明确`/`audit_only` 曾缺可观察推导输入。缓解：本阶段 FR-AUD-002/003 冻结 schema 与规则，OPEN-009 关闭。
- **RISK-015**（本阶段新增）：`created/updated` 取自来源 mtime（PFACT-013），语料整体被重新拷贝/导出时 mtime 可能变化导致产物时间戳变化。缓解：语料冻结（A-1）+ 变化即视为输入变化按 AC-06 重算；K3 上库前如需固定时间戳可改取指纹基线（受控基线变更）。

### 未决项（OPEN）

- **OPEN-001**（owner build-plan）：16 个基线失败根因与处置。关闭条件：根因结论 + 删除/修复决定。
- **OPEN-002**（owner build-plan）：缓存持久化位置、生命周期与四项键的实现。关闭条件：四项键定义 + 负例验证。
- **OPEN-003**（owner build-plan）：slug 生成方式与碰撞后缀策略。关闭条件：批内唯一性断言 + import-order 无关测试。
- **OPEN-004**（owner build-plan）：疑似同义报告人工处置流程细节。关闭条件：报告载体落地 + 显式主题映射路径打通。
- **OPEN-005**（owner build-code）：旧 digest 测试分类清单。关闭条件：分类清单产出且 AC-10 失败清单保持。
- **OPEN-010**（owner build-plan）：AC-10 基准精确冻结形态。关闭条件：基准清单冻结且可机械判定。
- **OPEN-006**（owner build-spec）：**本阶段关闭**——KD 溯源语义已登记进 `CONTEXT.md`（批次目录/临时对照产物、参考块、双轨出处、待验证事实全集、显式主题映射），与页头/旁路字段一致。
- **OPEN-008**（owner build-spec）：**本阶段关闭**——归一化规则、product 作用域、显式主题映射存储形态、模型建议边界冻结于 FR-GRP-001/002。
- **OPEN-009**（owner build-spec）：**本阶段关闭**——两层状态判定规则与「待验证事实全集」声明冻结于 FR-AUD-002/003；五类 fixture 可依 schema 构造。
- **OPEN-011**（owner build-spec）：**本阶段关闭**——`created/updated` 取来源 mtime 日级归一化（RISK-015 登记）。
- **OPEN-012**（owner build-spec）：**本阶段关闭**——claim 切分、`claim_id` 稳定性、char 区间、正文↔旁路一对一覆盖 schema 冻结于 FR-AUD-002。
- **OPEN-007**：ADR 0013 是否修订——用户在 make-decision 已决定「不改 ADR，只声明不使用授权」；本阶段维持。

### 交接给 build-plan 的边界

- 不猜 slug 算法与碰撞后缀（OPEN-003）；不猜缓存位置（OPEN-002）；不猜 16 个基线失败处置（OPEN-001）。
- 本规格的 13 条 AC 是验收口径；实现方案不得放宽（用户在 make-decision 确认「保持 13 条 AC 不放宽」）。

## 13. 业务影响与回归范围

### digest 命令

- **既有行为**：`digest` 承载旧 reader 编译行为（518 个测试绑定）。
- **本需求影响**：`digest` 执行 K1 语义编译；旧行为降为 `scripts/` 一次性对照脚本。
- **回归路径**：AC-09 命令隔离 + AC-10 节点 ID 基准。
- **验收**：AC-09 / AC-10。

### 既有产物目录

- **既有行为**：release4 bundle 等历史产物不受影响。
- **本需求影响**：新产物只落在 KD测试批次目录；CompanyBrain/gbrain 零写入。
- **回归路径**：写权边界负向检查（NG-008）。
- **验收**：AC-03 / AC-08。

### 可能受冲击的业务规则

- 「失败不伪装成功」「不丢内容」「可重复运行」「claim 级溯源」「300 行分页」五个既有不变量在新链路必须保持（D-013）。
- 明确无影响：CompanyBrain 既有页内容与元数据流水线（本卡零接触）；gbrain 配置与索引状态。

---

## 阶段执行记录（build-spec）

### spec-clarify 执行记录

spec-clarify trigger = false；理由 = 本阶段负责的 OPEN-006/008/009/011/012 经逐项核对均可由已批准决策与已核实事实唯一推导（归一化规则、状态 schema、时间戳取值、claim schema、CONTEXT 登记），无用户裁决分叉；其余 OPEN 项按 decision-log owner 列归属 build-plan/build-code；open material ambiguity = 0。十维 completeness 检查：用户旅程=SCN-001…013 全覆盖；页面范围=第 5/7 节；数据与状态=FR-AUD-003；成功边界=SCN-001/005/012；失败边界=SCN-002/004/007/011；权限=写权默认必须成立；集成的外部效果=K3 交接（SCN-013）；非目标=第 10 节；延期交接=第 12 节；验收=第 11 节。无 unknown 维度。

### conditional-spec-research 执行记录

已执行一轮只读取证（子代理）：CONTEXT.md 现状与术语落点、digest 注册入口与参数面、冻结清单路径与字段名、config 目录现状。结论已固化为 PFACT-002/012/013 与 FR-PUB-001 字段值锚点（真实 CompanyBrain 页抽样）。正式 research receipt 的公共发布入口仅暴露 make-decision（本会话无 build-spec 发布通道），按合同记为未供给，不影响本草拟。

### simplicity-guard 四阶梯执行记录

- 分批与恢复：P0 不成立——本卡一次跑完（D-012/D-013），不激活、不预留实现。
- 拆块：P2——复用仓库既有保真拆块并追加表格行聚合（PFACT-006），不重写。
- 原子发布/回滚：P0 不成立——K3 范围（NG-004）。
- 独立第二方法：P0 成立——AC-01 硬要求，不删。
- 疑似同义报告/显式主题映射：P2——复用确定性模板 + 人编辑配置，不建自动合并系统。
- 向量库/图库/服务化：P0 不成立——NG-007。
- 结论：无范围膨胀项；第 10 节非目标与第 5 节边界即四阶梯裁决结果。

### plan-ceo-review 执行记录

- 用户问题与证据分离：问题=参考型内容丢失（PFACT-007 证）；紧迫性=K2/K3/K4 底座（第 1 节）。
- 最窄范围：K1 一张卡（D-001）；既有杠杆=保真拆块/标题树/冻结清单（PFACT-002/006）。
- 可信备选对照：保留母任务备选（摘要索引路线）与已拒方案（decision-log `## 拒绝方案`），本阶段无新备选优于已选方向。
- 可否定前提：PFACT-001/002/006（语料干净、清单可用、保真拆块可行）；若被推翻回 make-decision。
- 时机/影响半径/最小缺口：影响半径=digest 命令面 + 测试口径；最小缺口=slug 算法与缓存位置（已归 build-plan）。

### review-frozen-spec 执行记录（step 11–12）

wh-review build-spec surface 真实调用一轮：canonical attempt `a9bf4dec-e9f8-5b53-a6d7-37c016c1efb8`，12 条 reportable findings（1 blocking + 10 major + 1 minor，全部 actionable、direct 证据）。逐条处置 = 全部 `fixed`，零静默丢弃、零 accepted_risk（无需要用户风险确认的取舍）：

| finding | 处置落点 |
| --- | --- |
| F-9b95e21cba7d（blocking：claim schema 碰撞/行级映射/被拒导读无锚点） | FR-AUD-002 重写：claim_id 加 char 区间 + occurrence_index；正文↔旁路改 span 级映射；被拒导读句以 `page_anchor=intro` 登记、`retrieval_evidence` 必填 |
| F-22c31fd54144 / F-4f97d2c2cc07（SCN-007「按规则退化」开放措辞；模型不可用矩阵未冻结） | SCN-007 改为确定性三态矩阵（缓存命中/缺缓存可调用/缺缓存不可用的回退值与阻塞记录） |
| F-2806bbdd9065（块边界/类型判定不确定，两方法无共享语义） | FR-BLK-001 增加判定优先级与边界规则（table>list>code>attachment_refs>error_text），fixture 归 plan/tasks |
| F-3cfcdfa7857b / F-55d2a2187ec1（对账失败无批次目录 vs AC-12 失败也记账；「不写任何产物」冲突） | FR-SRC-001/SCN-002 修订：每次尝试（含对账失败）建批次骨架（README + run-metrics 0 调用附 reason + manifest blocked），不写 products |
| F-64177896e89c（复合页缓存键未聚合成员来源） | FR-CMP-003 缓存键改页面复合输入指纹（成员 content_hash 按主题键升序拼接 + 主题键） |
| F-811d79eaec20（加载态 N/A 引用了无出处的 `_digest/runs/` 路径） | 状态覆盖清单加载态条目删除该路径声明 |
| F-adf3246fc023 / F-ed80ba598a9b（audit_only 循环定义；manifest 缺来源级状态） | FR-AUD-003 改声明式输入 + 程序核验（禁止输出反推）；FR-AUD-004 增加来源台账 schema |
| F-bf3d9bf01ac0（整块保真 vs 300 行分页冲突未定义） | FR-PUB-003/AC-07 增加受控豁免（超 300 行参考块独占附录 part） |
| F-d106914aae73（duplicate_alias 与覆盖不变量无可兼容记录规则） | FR-AUD-001/AC-13 增加别名承载分支（`alias_of` + `canonical_block_id`，复用 canonical 锚点不产生新锚点）；跨 product 归属 canonical |

修复均在本阶段完成并回写本规格；无 finding 升级或降级处置；未引入 decision-log 之外的产品方向。

### UI 条件路径记录（steps 7–9）

UI applicability = non_ui（继承 decision-log，三来源一致）。`ui-project-init` / `design-source-readiness` / `conditional-plan-design-review` 均 N/A——原因：CLI + Markdown 产物，读者界面由第三方编辑器提供，无浏览器界面/路由/交互组件；不产生 UI contract facts，不构成质量缺口。

### 阶段末遗漏披露（build-spec 收尾时逐项核对）

见本文件末次修订时点的收尾说明（发布步骤输出）。
