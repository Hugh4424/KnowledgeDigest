# 决策记录 · task7-semantic-layer-compiler

> 本文件是 make-decision 阶段唯一权威材料。OI 大纲只存在于本文件内，不另建需求账本、状态机或第五份材料。
> 当前阶段状态：**approved**（step 1–11 完成：load-context、triage-scope、Talk Round 1、事实核实与调研、Talk Round 2、
> direction-advice 与处置、Talk Round 3、grill-with-docs、决策草稿、detail-advice 与处置、用户真实确认；
> 余下 step 12 stage-end-spec-analyze 与 step 13 publish-decision 见 `## 阶段执行记录`）。
> 标题层级说明：`## 原始需求`、`## 核心需求`、`## 核心目标`、`## 已选方向`、`## 验收标准`、`## 范围`、
> `## 非目标`、`## 风险与延期交接`、`## UI applicability`、`## 收敛检查` 是运行时读取的固定小节名，保持不带编号。

## 任务身份

| 项 | 值 |
| --- | --- |
| project | KnowledgeDigest |
| task_id | `task7-semantic-layer-compiler` |
| stage | make-decision |
| worktree | `/Users/Hugh/Hugh/Project/KnowledgeDigest-task7-semantic-layer-compiler` |
| branch | `task/KnowledgeDigest/task7-semantic-layer-compiler` |
| baseline_commit | `c5fb2b5d4dde7b00afdfe668303c31b032477d29` |
| task_path | `/Users/Hugh/Hugh/Knowledge/Projects/KnowledgeDigest/tasks/task7-semantic-layer-compiler` |
| created_at | 2026-09-13 |

- **任务类型**：普通任务

`普通任务`保留既有提问与产物深度，允许在本阶段追问实现细节（文件路径与文件面、函数名、字段名、
算法、schema 形状、命令形态、入口参数形态、行号、代码片段、测试记录与实测记录），当这些细节的
答案会改变实现时即提问。本任务不做 `规划任务` 的方向层限制。

**范围声明（用户已确认，2026-09-13）**：本任务范围 = 母任务 PRD（`specs/archive/task6-effect-gap-and-architecture-reset/prd.md`）
中的 **K1 一张卡**（参考保真 + 语义层页面编译），不含 K2 入口与导航、K3 发布通道与查询集验收、K4 瘦身删码。
母任务与其兄弟任务材料对本任务只读；本任务自建 `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` 四份材料。

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 状态/处置 | 关联 D/OI |
| --- | --- | --- | --- | --- |
| R-001 | 按标准 WorkflowHub 从 make-decision 开始本任务，先创建 worktree | 用户原话 2026-09-13 第 1 句 | covered | 阶段执行记录 |
| R-002 | 不跳阶段 | 用户原话 2026-09-13 第 1 句 | covered | 阶段执行记录 |
| R-003 | 不依赖 build-spec 补需求；先基于原始需求在 make-decision 内把需求梳理完整 | 用户原话 2026-09-13 第 1 句 | covered | OI-01…OI-19 全部在本阶段收敛 |
| R-004 | 在 make-decision 过程中共同梳理六类边界 | 用户原话 2026-09-13 第 1 句 | covered | 六固定类别全覆盖 |
| R-005 | 注意主会话上下文控制与子代理派发 | 用户原话 2026-09-13 第 1 句 | covered | NG-002；`## 调研` 记录两次子代理取证 |
| R-006 | Talk 与 grill 用大白话说明选项、后果和风险 | 用户原话 2026-09-13 第 1 句 | covered | `## Talk`；Talk 卡格式 |
| R-007 | 任务范围 = 母任务 PRD 的 K1 卡 | 用户答复（三问之一） | covered | OI-01, D-001 |
| R-008 | 任务类型 = 普通任务 | 用户答复（三问之一） | covered | `## 任务身份` |
| R-009 | K1 结果 = 89 份 Confluence Markdown → 与 CompanyBrain 同构的知识页；参考型内容零丢失且逐块可回原文区间；叙述内容逐条带出处；`page_model=derived` 断言成立 | 母任务 PRD K1「结果」 | covered | OI-04, OI-11, OI-12, D-006 |
| R-010 | K1 的 5 条 FR/AC | 母任务 PRD K1 表 | covered | OI-04, OI-09…OI-13, D-006 |
| R-011 | K1 scope：只做 Confluence Markdown（89 份冻结语料）；输出为语义层页面 + 参考块清单；不做入口导航、不做发布通道、不删代码 | 母任务 PRD K1「scope」 | covered | OI-01, NG-003…NG-006 |
| R-012 | K1 用户流程与状态转换：投料 → 解析拆块 → 编译成页 → 结构校验 → 待发布 → 交 K3 发布 | 母任务 PRD K1「用户流程与状态转换」 | covered | OI-16, D-012 |
| R-013 | S1 语义层契约：与 CompanyBrain 同构的 frontmatter、目录与命名、`[[wikilink]]` 双链；硬断言 `page_model=derived` 且带 `generated_by` | 母任务 PRD S1 | covered | OI-11, OI-12, D-006 |
| R-014 | S3 数据状态词表；「资料未明确」不得写成结论、不得进入事实分母 | 母任务 PRD S3 | covered | OI-13, D-009 |
| R-015 | S4 证据零容忍：每条 claim 带 `source_uri`、内容指纹、行定位；回不到原文的进 `unknown` 并显式标注；多 claim 句子逐条映射 | 母任务 PRD S4 | covered | OI-10, OI-12, D-004, D-005 |
| R-016 | S6 保留不变量：300 行分页、分批与恢复、来源去重、失败不伪装成功、claim 级溯源 | 母任务 PRD S6 | covered | OI-14, D-013 |
| R-017 | S7 写权边界：KD 只写自己声明的路径；不改既有 CompanyBrain 正式页；不改停摆自动化流水线 | 母任务 PRD S7 | covered | OI-02, OI-17, NG-008 |
| R-018 | 目标父目录 `/Users/Hugh/Downloads/KD测试`，每次尝试在其下新建批次文件夹作为根目录，内部仿 CompanyBrain 结构 | 用户答复 Q1/Q1b | covered | OI-02, D-002 |
| R-019 | 逐条出处以「原始文件 + 文件内标题」呈现（不向读者显示行号，因原始文件经常更新） | 用户答复 Q3/Q3b/Q3c | covered | OI-10, D-004 |
| R-020 | 页头复用现有 `source` 字段，细粒度出处走旁路文件 | 用户答复 Q4b | covered | OI-12, D-005 |
| R-021 | 按主题合并；允许一份文件拆分到多页 | 用户答复 Q2/Q10 | covered | OI-05, OI-06, D-003 |
| R-022 | 模型仅用于起标题/写导读/判主题，禁止改写参考型内容 | 用户答复 Q14 | covered | OI-07, D-007 |
| R-023 | 模型结果冻结成缓存，命中不重调，以保住「同输入同结果」 | 用户答复 Q17 | covered | OI-07, OI-08, D-007 |
| R-024 | 「部分成功 + 显式列表报告阻塞项」作为成功/失败边界 | 用户答复 Q8 | covered | OI-15, D-008 |
| R-025 | 五类数据状态全部由程序从事实推导 | 用户答复 Q9 | covered | OI-13, D-009 |
| R-026 | 沿用现有冻结清单作为验收基准，不重新核对语料 hash | 用户答复 Q6 = B | covered | OI-19；事实核实已证明磁盘与清单一致，RISK-001 降级 |
| R-027 | 不碰 gbrain，只校验页面路径能生成合法 slug | 用户答复 Q18 | covered | OI-19, OI-17；DEF-002 |
| R-028 | 参考块以「整张表/整个列表」为一个逻辑单元 | 用户答复 Q13 | covered | OI-09, D-010 |
| R-029 | 图片/附件 URL 原样保留并标注 | 用户答复 Q5 | covered | OI-09, D-010 |
| R-030 | 5 项非目标（不做入口导航、不做原子发布回滚、不做瘦身删码、不做真实查询集对照验收、不做向量库/服务化/前端/多格式输入） | 用户答复 Q7 | covered | NG-003…NG-007 |
| R-031 | 批次文件夹命名 = 日期 + 当天自增序号 | 用户答复 Q16 | covered | OI-02, D-002 |
| R-032 | 与 CompanyBrain 既有页面完全无关：不读、不合并、不比对 | 用户答复 Q22 | covered | OI-17, D-014 |
| R-033 | 确认 5 条延期项及其归属与触发条件 | 用户答复 Q23 | covered | OI-19, DEF-001…DEF-005 |
| R-034 | AC-K1-1 的基准用「冻结清单 + 独立第二方法交叉验证」破解循环 | 用户答复 Q24 | covered | OI-04, D-011 |
| R-035 | 页面文件名用英文 slug，中文标题放 frontmatter `title` | 用户答复 Q25 | covered | OI-08, OI-11, D-015 |
| R-036 | `source:` 写语料相对路径并标注根目录 | 用户答复 Q26 | covered | OI-12, D-005 |
| R-037 | 先查清 16 个基线失败、当基线写进计划 | 用户答复 Q27 | covered | OI-14, D-016 |
| R-038 | 一次运行处理全部 89 份 | 用户答复 Q28 | covered | OI-16, D-012 |
| R-039 | `generated_by = knowledge_digest_semantic_compiler.py` | 用户答复 Q29 | covered | OI-11, D-006 |
| R-040 | 批次目录结构 = 页面 + 页面清单 + 两份审计文件 | 用户答复 Q30 | covered | OI-02, D-017 |
| R-041 | `digest` 换成新行为，旧行为降为 `scripts/` 下一次性的对照脚本 | 用户答复 Q20/Q20b | covered | OI-14, D-018 |

**未覆盖/待定**：无。R-001…R-041 全部落到 OI、D 条目、非目标或延期项；无 `accepted_omission` 条目。

### 需求框架预设（先于研究/Talk 选定）

- **framework**：`functional`（背景 → 问题 → 目标 → 方案 → 验收 → 扩展）。
- **选择理由**：本任务主体是"把 89 份 Confluence Markdown 编译成可检索的语义层知识页"这一行为与结构改动；
  方向已由母任务决策记录（revision-19e398）冻结，本阶段收敛的是 K1 范围内的落地形态、边界与验收口径，
  因此以外层行为骨架为主，把"证据保真"与"下游可消费性"挂在 `acceptance` 与 `extension` 节点下，
  不另开一套 research 或技术框架。
- **回填规则**：Talk、调研、审查、Grill 只更新本文件的 OI 表与 D* 条目，不新建第二张表、不新建需求账本。

### 用户原话（逐字，未改写）

> 请检查"/Users/Hugh/Hugh/Project/KnowledgeDigest/specs/archive/task6-effect-gap-and-architecture-reset/prd.md"，我准备开始其中第1个任务了。
> 我希望现在按标准 WorkflowHub 开始这个第二个任务，先创建worktree，然后从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。先基于原始需求，在make-decision的过程中和我一起仔细梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。注意主会话上下文控制和子代理派发。Talk 和grill请用大白话说明选项、后果和风险；

> （追问澄清）为什么有两个任务分支，是不是创建错了，请检查"/Users/Hugh/Hugh/Project/KnowledgeDigest-task7-semantic-layer-compiler"和"/Users/Hugh/Hugh/Project/KnowledgeDigest-task5-reader-quality-compiler-redesign"

## 核心需求

KnowledgeDigest 现有管线（89 份 Confluence Markdown → release4 bundle）产出的是「文档的场景化摘要索引」，
不是「面向检索的知识库」：参考型内容（表格/参数/枚举/字段字典/URL/报错文案）在产物中大面积消失，
下游读者与 Agent 拿不到可直接引用的事实。母任务已把方向定为**直接产出与 CompanyBrain 同构的语义层页面**。
本任务（K1）负责这条新编译链路的**内容正确性与保真性**：把 89 份冻结语料编译成带逐条出处、
参考内容零丢失、可被下游按 slug 检索的知识页，并把产物交到指定批次目录等待发布通道接管。

**事实核实补充（子代理只读核实，2026-09-13）**：现有管线的丢失是结构性的——`reader_compiler.py` 的拆块是
**固定 240 行窗口**、不认标题、会把表格从中间切断，且会改写文本；而仓库里已经存在保真取向的拆块实现
（`compiler.py:2940-2991` `_paragraph_evidence`：标题/列表项/表格行/代码块各自成块，"The bytes are never rewritten"）。
即缺的不是拆块能力，而是一条**以保真为第一目标、且直接产出语义层页面**的编译链路。

## 核心目标

**目标（用户在 Talk Round 1 答复并确认）**：让 89 份冻结 Confluence 语料变成**参考保真、逐条可溯、结构同构**的语义层知识页，写入用户指定的批次目录；本节五条判据即为「达成」的定义，每条都可被机器或人工核对。

- 第一判据（保真）：参考型内容（表格/参数/枚举/字段字典/URL/报错文案）**逐字零丢失**，结构与原文一致，不经模型改写。
- 第二判据（可溯）：叙述型内容**逐条带回原文的定位**——读者可见「原始文件 + 文件内标题」，机器可验「文件 + 内容指纹 + 行区间」；
  回不到原文的内容只能进 `unknown` 并显式标注，不得写成结论。
- 第三判据（同构）：产物页与既有 CompanyBrain 页面同构（frontmatter、目录与命名、`[[wikilink]]` 双链），
  硬断言 `page_model = derived` 且 `generated_by = knowledge_digest_semantic_compiler.py`，避免被既有元数据流水线判成 `source` 或 `curated`。
- 第四判据（可重复）：同一批输入重复运行产出**字节级一致**的产物；模型结果冻结成缓存，命中不重调。
- 第五判据（可下探）：页面路径使用**英文 slug 文件名**（gbrain 的 slug 规则会删除全部中文字符），
  中文标题放在 frontmatter `title`；批次目录内部仿 CompanyBrain 结构，为下游技能/Agent/应用层的消费留出接口。

**当前证据状态**：`evidence_status: confirmed`（两轮 Talk 共 26 项用户答复 + 两次子代理只读核实），`evidence_owner`: 主会话，
`next_review_trigger`: 若用户改变 Q1/Q2/Q14/Q17/Q25 任一答复则重算本目标。

## 已选方向

**选定方向（全部来自用户答复并确认，2026-09-13；每条取舍同时记录了被拒方案与取舍理由）**：

用户在各决策轴上的答复、被拒方案与取舍理由如下（完整的被拒方案清单另见 `## 拒绝方案`）：

- **产出落点（用户答复并确认 Q1/Q1b/Q16/Q30）**：写入父目录 `/Users/Hugh/Downloads/KD测试`，每次尝试在其下新建批次文件夹作为该次根目录；
  批次目录名 = 日期 + 当天自增序号。该目录是**临时对照产物**，不是正式知识库；正式上库由 K3 的发布通道负责。
- **目录形态**：批次目录内部仿 CompanyBrain 结构，为以后整目录平移留路。
- **批次目录内容**：`README.md`（本次说明）+ `products/<产品>/<模块>/<页面>.md`（知识页）
  + `_audit/reference-blocks.jsonl`（参考块清单）+ `_audit/sources.jsonl`（旁路溯源）
  + `_audit/page-manifest.json`（页面清单、分类归属与机读批次状态，交 K2/K3）
  + `_audit/run-metrics.json`（成功与失败两类运行的耗时/调用数/token 与阻塞清单）
  + `_audit/suspected-synonyms.md`（疑似同义主题报告，RISK-004 的缓解载体）。
  `README.md` 与 `suspected-synonyms.md` 必须由确定性模板生成（不写批次名、运行时刻或实际调用数），以保证 AC-06 的字节一致。
- **一次运行范围**：一次命令处理全部 89 份，一次产出整个批次目录；不做分批。
- **页面粒度**：按主题合并（同一主题多来源合为一页）；允许一份文件的不同章节拆分到不同页面。
- **主题判定**：按标题名做**确定性**合并（同一份文件每次运行得到同样分组），不把主题归组交给模型随机决定。
- **模型边界**：模型用于起标题与写导读；**禁止**改写参考型内容与叙述型正文。主题归组由确定性标题名规则单方决定，模型对主题的判断只作建议（详见 D-007）。
- **可重复性**：模型结果冻结成缓存，缓存键绑定来源内容指纹，命中即不重调；输入变化才重新调用。
- **参考块单元**：整张表 / 整个参数列表 / 整段报错文案 = 一个逻辑单元（一块），保留结构。
- **图片与附件 URL**：原样保留并显式标注为外部资源链接，不下载、不改写、不删除。
- **出处呈现（双轨）**：页面显示「原始文件 + 文件内标题层级」；机器在旁路文件另存「文件 + 内容指纹 + 行区间」。
- **页头字段**：`source:` 复用既有字段，写语料相对路径并标注根目录；逐条出处的细粒度信息只进旁路文件。
- **页面命名**：文件名与目录名使用**英文 slug**（gbrain slug 规则会删除中文字符，纯中文名会导致 62 个页面互相覆盖）；
  中文标题放在 frontmatter `title`。
- **页面身份字段**：`page_model: derived`、`generated_by: knowledge_digest_semantic_compiler.py`。
- **数据状态**：五类状态全部由程序从事实推导，不由模型判定、不留人工标注。
- **成功/失败边界**：部分成功 + 显式列表报告阻塞项；不做「全有或全无」，也不允许「能写多少写多少、不报阻塞」。
- **验收基准**：沿用仓库现有冻结清单（`confluence-raw-89-20260818-v1`；已核实磁盘 89/89 与清单 sha256 一致）；
  AC-K1-1 的"冻结分层全量清单"以「冻结清单 + 独立第二方法交叉验证」破循环。
- **与既有知识库的关系**：完全不读、不合并、不比对 CompanyBrain 的 1347 个页面。
- **命令门牌**：`digest` 命令换成新的语义编译行为；旧行为降为 `scripts/` 下一次性的对照脚本（K4 删旧码时一并删除）。
- **gbrain**：本任务不触碰 gbrain 的配置与索引状态，只校验页面路径能生成合法且唯一的 slug。
- **成本闸门**：运行前先打印本次计划（来源数、主题数、预计页面数、预计 provider 调用），不等人确认直接执行。

## 验收标准

**验收标准（用户已答复并确认，每一条均可验证且各自带失败的判定条件）**：K1 产出的批次目录中，参考型内容可逐块与原文逐字对上、每条叙述结论可回原文定位、
页面结构与既有 CompanyBrain 契约一致、同输入重复运行结果字节一致；下表 AC-01…AC-13 的「失败判据」列即为不通过的判定条件。

| AC | 判据（可执行） | oracle | 失败判据 |
| --- | --- | --- | --- |
| AC-01 参考块清单零丢失 | 对 89 份输入生成 `_audit/reference-blocks.jsonl`，每块带 `source_path`、`content_hash`（块内容 sha256）、`line_start`/`line_end`、`block_kind`；块的全集与**独立第二方法**（不依赖同一拆块器的独立扫描）生成的清单逐块一致 | 机器全量比对两份清单 + 人工抽 20 块逐字复核 | 任一块缺失、错位、指纹不一致，或第二方法发现而主方法缺失 |
| AC-02 参考内容逐字保真 | 每个参考块在产物页面中的文本与原文对应行区间**逐字节一致**（表格/列表结构保留），图片与附件 URL 原样保留且带显式外部资源标注 | 机器逐块 diff（重新从原文按行区间切片对比） | 任一处语义改写、字段丢失、结构被破坏、或块被固定窗口从中间切断 |
| AC-03 同构页面编译 | 抽 10 页做结构/元数据校验：frontmatter 覆盖母任务 S1 的 15 字段正式块（`title/type/page_model/scope/product/section/module/tier/trust/source_status/quality_status/created/updated/generated_by/tags`）**加 1 个按 D-005 复用的 `source` 字段（共 16 个受校验字段）**；`source` 必须可解析到本次语料的具体文件并标注语料根目录；`page_model=derived` 与 `generated_by=knowledge_digest_semantic_compiler.py` 断言成立；`[[wikilink]]` 双链可解析；文件名与目录名为合法 gbrain slug 且**批内唯一** | 校验脚本 + slug 唯一性检查 | 任一字段不符、断言失败、`source` 缺失或不可解析、slug 非法或批内重复 |
| AC-04 claim 级溯源零违规 | 机械扫描零「无出处结论」：每条 claim 带 `source_path`（与母任务 S4 的 `source_uri` 指同一物，本任务统一用 `source_path`）+ 内容指纹 + 行区间；多 claim 句子逐条映射；回不到原文的内容只出现在 `unknown` 且显式标注「原文未明确」并携带检索证据；模型生成的导读**逐句**都能在原文找到依据 | 解析器扫描零违规 + 导读逐句回溯检查 | 无定位肯定句、错定位、未逐条映射、导读出现原文没有的信息 |
| AC-05 五类数据状态一致 | 五类状态**分属两个层级，分别判定**：**来源级**（`ready`=读得到且能拆出块；`known_empty`=读得到但拆不出参考块也无叙述内容；`duplicate_alias`=内容指纹与其他来源相同且已有 canonical 来源；`audit_only`=只用于追溯、不进正文——判定规则=该来源的块全部只出现在 `_audit/` 且不进入任何 `products/` 页面）；**claim 级**（`资料未明确`=该 claim 在原文中找不到依据，需先有"待验证事实全集"）。构造五类 fixture 逐类核对：状态与正文一致；重复来源单页化；「资料未明确」不写成结论、不进事实分母（分母 = 待验证事实全集中有原文依据的 claim 数） | 五类 fixture 逐类核对 + 两个层级的判定规则可执行 | 重复来源发成两页、未明确写成结论或进入分母、来源级与 claim 级状态混用 |
| AC-06 可重复运行 | 同一批输入连续运行两次，产物**按下方定义的比对范围**逐字节一致；改动任一来源文件一个字节后，受影响页面的缓存必须失效并重算。**缓存契约**：缓存持久化在任务级固定位置（不随批次目录销毁）；键 = 来源内容指纹 + 模型标识 + 提示模板版本 + 主题映射版本；缺缓存时必须重新调用并把结果写回，不得静默产出不同内容。**比对范围**：`products/**` 的全部字节，以及 `_audit/**` 中**逐块/逐条产出的内容**（`reference-blocks.jsonl`、`sources.jsonl`、`suspected-synonyms.md`、`page-manifest.json` 的页面条目部分）；**明确排除运行级字段**：`_audit/run-metrics.json` 的计时数据、`page-manifest.json` 中的 `attempt_id`、以及批次目录名——这些按定义每次运行都会变化，不属于"同输入同输出"的比对对象。**确定性要求**：`created`/`updated` 取来源文件的确定性事实（如来源内容指纹对应的固定基线值或来源文件 mtime 的归一化值），不得取运行时刻；`README.md` 必须由确定性模板生成，不得写入批次名、运行时刻或实际调用数；批次目录名（日期+序号）与运行元数据不参与 `products/**` 与 `_audit/**` 的产物比对 | 两次运行产物 diff（按上述范围）+ 缓存失效负例 + `created`/`updated` 确定性检查 | 比对范围内出现任何字节差异、产物抖动，或来源变化而缓存误命中 |
| AC-07 结构不变量 | 单页不超过 300 行，超出必须分页且每个 claim 只进一个 part；来源去重生效；失败运行不产出「已完成」产物 | 分页与去重断言 + 失败注入 | 页面超限、claim 重复进入多个 part、失败被写成完成 |
| AC-08 阻塞显式化与批次状态可机读 | ① 无法处理的内容产出显式阻塞清单（文件、位置、原因、影响），产物中不出现静默跳过；② `_audit/page-manifest.json` 必须带**机读批次状态**，字段与取值如下（与母任务状态链对齐，消除同名两义）：
   `publish_status` ∈ `not_released`（**正常完成的成功末态**，母任务 PRD 规定 K1 完成即待发布）`|` `released`（本卡不产出，保留给 K3）；
   `run_status` ∈ `complete`（本次运行完整跑完）`|` `blocked`（有阻塞项未完成）`|` `interrupted`（写入中断，未走完 J6）；
   `attempt_id`、来源快照身份、阻塞项全集（可为空数组）
   ③ 使 K3 能直接区分"完整但待发布"（`publish_status=not_released` + `run_status=complete`）与"半成品"
   （`run_status=interrupted|blocked`），且**不得把中断或部分完成的批次表示为可发布** | 阻塞清单存在性与覆盖检查 + 批次状态字段校验 + 故意中断的负例 | 存在静默跳过、阻塞清单缺失、缺批次状态字段，或把未完成批次标为 `complete` |
| AC-09 命令与旧路径隔离 | `digest` 执行新语义编译行为；旧行为由 `scripts/` 下一次性的对照脚本承载，且该脚本保留相同能力以便对照；两者互不影响 | 命令行为断言 + 旧脚本可运行 | 新命令仍走旧路径，或旧脚本无法运行 |
| AC-10 回归口径（与 D-018 对齐） | 新链路自身的测试全绿；**回归基准按 OPEN-005 的分类清单定义**：① 挂在旧 `digest` 入口上的行为测试，随旧路径降级为脚本而**改挂脚本或标记废弃**，这部分不计入"新增失败"；② **不与 `digest` 入口绑定**的其他测试（含 16 个既有失败用例）必须保持节点 ID 与失败原因完全不变。基准以**失败用例的精确节点 ID 清单 + 测试清单**冻结，不以计数为准（计数不变但用例集合变化同样判失败） | 精确节点 ID 集合比对 + 测试清单比对 + OPEN-005 分类清单 | 非 `digest` 绑定的用例出现新增失败、16 个既有失败的节点 ID 或原因变化、或用例集合变化而计数掩盖 |
| AC-11 读者侧出处呈现 | 页面正文对每条叙述内容显示「原始文件名 + 文件内标题（`#`/`##`/`###`）」，且**不显示行号**；页头 `source` 能解析到本次语料的具体文件；`_audit/sources.jsonl` 逐条带内容指纹与行区间，且**与页面正文的 claim 句子可交叉核对**（对页面正文的实际 claim 做机械扫描，零无锚点 claim） | 页面渲染检查 + `source` 可解析性检查 + 扫描**页面正文**（非只扫旁路文件）与 `sources.jsonl` 的交叉核对 | 页面不显示文件+标题、显示了行号、页头 `source` 缺失或不可解析、或页面正文存在无锚点 claim |
| AC-12 成本与失败记账 | 运行前打印计划调用数与实际调用数**同阶**，量化为：**实际调用数 ≤ 计划调用数 × 1.5**，且**计划调用数 ≤ 合并后主题数 × 2 + 20**（可复算上界，由主题数机械推导，不由运行自行设定）；**不得随 claim 数或块数线性增长**；`_audit/run-metrics.json` 对成功与失败运行都记录耗时、调用数、token，**三项均真实非 null**；其中**真实发生的 0 是合法值**（例：缓存命中重跑、或在 J1/J2 早期失败尚未调用模型），必须原样记录 0 并附 `reason`（`cache_hit` / `no_provider_call_yet` / `provider_unavailable`）；只有**无法归因的 0、null、或与 `reason` 矛盾的计数**才判失败 | 计划/实际调用数比对 + 成功与失败两类运行的 `run-metrics.json` 字段检查 | 出现逐 claim 调用、任一成本计数为 null/0/伪造，或缺该文件 |
| AC-13 来源→输出覆盖不变量 | `_audit/reference-blocks.jsonl` 每条记录带 `block_id` 与**唯一输出锚点**（`page_path` + 页内定位：标题路径或块序号）；每条记录要么有非空锚点、要么出现在阻塞清单；无第三态；被两个锚点重复承载的块必须显式标为 `duplicate_alias` 而不是静默复制；`_audit/page-manifest.json` 可反查"一份来源 → 进入了哪些页面" | 覆盖关系机械检查（block_id 集合 ↔ 锚点集合 ↔ 阻塞清单）+ 来源→页面反查 | 存在既无锚点也不在阻塞清单的块、锚点不唯一、重复承载未标注，或来源无法反查到页面 |

**对照基线声明**：AC-K1-3 原文包含的「gbrain 按 slug 可检索」一项，因产物落在 gbrain 索引范围之外且用户选择不触碰 gbrain，
在本卡内记为**未验证**（DEF-002）；本卡只断言「路径能生成合法且唯一的 slug」。

**AC 与 OI 的对应**：AC-01↔OI-04/OI-09/OI-21；AC-02↔OI-09；AC-03↔OI-08/OI-11；AC-04↔OI-10/OI-12；
AC-05↔OI-13；AC-06↔OI-07/OI-20；AC-07↔OI-14；AC-08↔OI-15/OI-21；AC-09↔OI-14；AC-10↔OI-14；
AC-11↔OI-10/OI-12；AC-12↔OI-20；AC-13↔OI-21。

## 范围

范围与功能边界（用户答复并确认 Q0-b/Q7/Q22/Q20b）：本任务是**实现任务**（普通任务），范围是母任务 PRD 的 K1 一张卡，具体如下：

- 交付物：新的语义编译链路（读 89 份冻结 Confluence Markdown → 参考块清单 + 同构语义层页面 + 旁路溯源 + 页面清单）、
  批次目录下的真实产物、可重跑的验收证据。
- 覆盖内容：来源读取与拆块、参考块清单与独立第二方法、参考内容逐字保真、同构页面编译与英文 slug 命名、
  claim 级溯源（双轨）、五类数据状态处置、主题合并与拆分、模型权限边界与缓存确定性、批次目录落点与结构、
  `digest` 命令行为切换与旧行为降级。
- 不覆盖：入口与分类导航（K2）、原子发布与回滚（K3）、真实查询集对照验收（K3）、源码瘦身删码（K4）。
- 当前不确定性：仅剩实现层细节（模块划分、缓存键的具体构成、slug 生成算法的具体实现），
  方向层与验收层已由两轮 Talk 的 26 项答复全部确定。

## 完整用户旅程（六类边界之一：完整用户流程）

角色：**投料人**（用户本人，把 Confluence 导出的 Markdown 放进来并运行一次编译）、
**读者**（你自己或同事，在 Obsidian 里按目录与标题查产品知识）、
**下游消费者**（技能层 / Agent 层 / 应用层，按页面路径与 slug 检索）、
**维护者**（下一位改这条编译链路的人）。

| # | 阶段 | 谁做 | 发生什么 | 成功的样子 | 失败/中断的样子 |
| --- | --- | --- | --- | --- | --- | --- |
| J1 | 投料 | 用户 | 指定冻结语料目录与目标批次目录，运行 `digest` | 命令读入 89 份来源，打印本次计划（来源数、主题数、预计页面数、预计 provider 调用），不等人确认直接开始 | 语料目录不存在或为空：明确拒绝；语料数量或采样与冻结清单不一致：显式报告差异并停止 |
| J2 | 解析拆块 | 系统 | 逐份解析 Markdown，拆出参考型区块与叙述型段落 | 每块带来源、块指纹、行区间、块类型；**标题、列表项、代码块各自成块；连续表格行必须聚合为整张表一块**（与 D-010 的整块决定一致，不得按行成块）；**字节从不改写** | 解析不了的结构：显式标注并进阻塞清单，不静默降级为散文；坏表格坏行：原样保留而不是"修正"原文 |
| J3 | 主题归组 | 系统 | 按标题名确定性归组，决定页面划分与哪些来源进哪页 | 同一输入每次得到同样的页面划分；一页可含多来源，一来源可拆多页 | 标题漂移导致归组异常：显式报告异常分组，不静默合并 |
| J4 | 语义编译 | 系统 | 搬运参考型内容（逐字）+ 组织叙述型内容（逐条带出处）+ 生成标题与导读（走缓存） | 参考内容逐字节一致；叙述结论条条有定位；模型命中缓存时产物字节一致 | 模型不可用或缓存缺失：按规则退化或显式阻塞，不伪装成功；导读出现无依据内容：该页导读留空并标注 |
| J5 | 页面结构校验 | 系统 | 校验 frontmatter 15 字段、`page_model=derived` 断言、双链、300 行分页、英文 slug 合法且批内唯一 | 校验全绿，页面与既有 CompanyBrain 契约同构 | 任一断言失败：报告失败项，不写入「已完成」 |
| J6 | 写入批次目录 | 系统 | 把页面、页面清单、参考块清单、旁路溯源写入本次批次目录 | 目录结构完整：`README.md` + `products/...` + `_audit/` 三份文件 | 写入中断：**本卡无原子发布能力**，可能留下半成品并明确报告（K3 负责解决） |
| J7 | 阅读与查询 | 读者 / 下游 | 在 Obsidian 里按目录与中文标题找事实；下游按路径/slug 检索 | 能找到直接回答问题的段落，并知道它来自哪份原始文件的哪个标题 | 只能找到原文堆积、或结论与原文不符：判失败 |
| J8 | 复跑与核对 | 用户 / 系统 | 对同一批输入再跑一次，或改动一份语料后重跑 | 同输入产物字节一致；改动输入的受影响页面正确重算 | 产物抖动或缓存误命中：判失败 |
| J9 | 维护 | 维护者 | 改拆块规则、加页面类型、修编译失败 | 规则改动有测试与可复算证据；旧路径已降级为独立脚本，不牵动 K2/K3/K4 的机制 | 需要同时改多套历史实现、或改动破坏 K2/K3 边界：判失败 |

**旅程中的关键不变量**：不丢内容（参考型零丢失）、不伪装成功（无出处不得写成结论、失败必须显式）、
可重复运行（同输入同输出，模型结果冻结）、可追溯（读者可见文件+标题，机器可验指纹+行区间）、
写权受限（只写本次批次目录，不碰 CompanyBrain 与既有流水线与 gbrain）。

## UI applicability

三个输入事实按证据合并（不按调用方标签）。

```json
{
  "result": "non_ui",
  "sources": {
    "raw_requirement": {
      "applicability": "non_ui",
      "fact": "用户要求把 89 份 Confluence Markdown 编译成与 CompanyBrain 同构的知识页并写入本地批次目录；要求指向内容与结构契约，未要求开发或修改任何浏览器界面、路由或交互组件"
    },
    "project_inventory": {
      "applicability": "non_ui",
      "fact": "KnowledgeDigest 是 Python 命令行工具：无前端技术栈、无路由、无交互组件；用户可见产物是写入本地目录的 Markdown 文件，由第三方编辑器（Obsidian 类）打开"
    },
    "planned_or_changed_frontend_fact": {
      "applicability": "non_ui",
      "fact": "本任务已接受方向为内容编译链路与批次目录产物，不新增也不修改任何前端或界面实现"
    }
  },
  "reason": "三项来源一致为 non_ui：产品是 CLI + Markdown 产物，读者界面由第三方编辑器提供"
}
```

## 收敛检查

| 维度 | 用户答案 | 事实/材料引用 | 可执行验收 |
| --- | --- | --- | --- |
| 目标 | 用户答复并确认 T/Q：先把读者效果做对（Q2 按主题合并、Q14 模型只写标题导读、Q17 结果冻结、Q25 英文 slug 命名、Q28 一次跑全量）；目标即"89 份语料→参考保真、逐条可溯、结构同构的语义层页面" | decision-log.md#核心目标 / R-009, R-021…R-023, R-035, R-038 | 同一下达输入连跑两次，产物在 AC-06 定义的比对范围内字节一致（通过）；参考型块与原文逐字节零差异（通过）；任一处语义改写或结构破坏（失败） |
| 范围 | 用户答复并确认 Q0-b/Q7/Q22/Q20b：只做 K1 一张卡、只消费 89 份冻结语料、只做内容页与参考块清单、不碰 CompanyBrain 既有页、`digest` 换新行为 | decision-log.md#范围 / R-011, R-030, R-032, R-041 | 产物目录内不出现入口页/分类导航/发布回滚产物（通过）；CompanyBrain 与 gbrain 零写入（通过）；出现任一非目标项（失败） |
| 方案 | 用户答复并确认：取舍=接受批次目录作为临时对照产物、接受按标题名确定性归组、接受页头复用 `source` + 旁路文件；被拒方案=直写 CompanyBrain、一份来源一页、让模型运行时判主题、新增页头字段、新增独立子命令（完整清单见 `## 拒绝方案`）；未决项=OPEN-001…OPEN-012，各有 owner、触发条件与关闭条件 | decision-log.md#已选方向 / R-018…R-023, R-035…R-041；## 拒绝方案；## 未决项 | 页面可见「原始文件+标题」（通过）；旁路文件含指纹与行区间（通过）；slug 合法且批内唯一（通过）；出现未登记在未决项或延期项的悬空决定（失败） |
| 验收 | 用户答复并确认 Q6/Q8/Q9/Q10/Q24/Q27：沿用现有冻结清单（已核实 89/89 一致）、部分成功+阻塞清单、状态由程序推导、允许一来源拆多页、AC-K1-1 用独立第二方法破循环、保持 13 条 AC 不放宽 | decision-log.md#验收标准 / R-024…R-026, R-034, R-037；## 验收标准 AC-01…AC-13 | 场景：读者按目录与标题查产品知识，并能回到原文出处；数据来源：89 份冻结 Confluence Markdown + 冻结来源清单 + 独立第二方法清单；通过：AC-01…AC-13 全部满足；失败：任一条 AC 的失败判据命中，或把 DEF-001…DEF-008 写成已完成 |

## OI 大纲（唯一当前版本 · outline_version = v3 · step 6 direction-advice 后加入 OI-20/OI-21）

> 身份绑定：全部 OI 绑定 `task_id = task7-semantic-layer-compiler`、`outline_version = v3`
> （v1 为研究前初建版本；step 5 后升 v2；step 6 direction-advice 的 F-4/F-5/F-6 重写了 OI-04/OI-08/OI-11 的问句与验收，
> F-7/F-8 新增 OI-20/OI-21，故升 v3。旧版本的消费者事实不适用于 v3）。
> 状态取值只用 `open` / `confirmed` / `deferred` / `not_applicable`。
> `requires_user_decision` 语义：该 OI 是否必须由用户裁决。由仓库事实或已确认证据直接回答的记 `false`。

### Framework nodes

| node_id | framework_node | oi_ids | empty | reason |
| --- | --- | --- | --- | --- |
| N-background | background | OI-01, OI-17 | false |  |
| N-problem | problem | OI-03 | false |  |
| N-goal | goal | OI-04 | false |  |
| N-solution | solution | OI-05, OI-06, OI-07, OI-08, OI-09, OI-10 | false |  |
| N-acceptance | acceptance | OI-11, OI-12, OI-13, OI-15, OI-20, OI-21 | false |  |
| N-extension | extension | OI-14, OI-19 | false | OI-14 同时属固定类别 deferred（框架节点与固定类别是两个维度，允许交叉） |

### Fixed categories

| category | oi_ids | empty | reason |
| --- | --- | --- | --- |
| complete_user_flow | OI-02, OI-04, OI-16, OI-17 | false |  |
| page_scope | OI-01, OI-05, OI-06, OI-08, OI-11, OI-12 | false |  |
| data_state | OI-09, OI-13 | false |  |
| success_failure_boundary | OI-03, OI-07, OI-10, OI-15, OI-20, OI-21 | false |  |
| non_goals | OI-18 | false |  |
| deferred | OI-14, OI-19 | false |  |

### OI 记录（每项一个可独立处置的收敛项 · 终态已回填）

```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-01
category: page_scope
source: "R-007 / R-011"
question: |2-
  本任务的范围边界是否为母任务 PRD 的 K1 一张卡，以及 K1 是否只消费 89 份冻结 Confluence Markdown、只做内容页不做入口导航？
status: confirmed
selected_disposition: |2-
  用户选择：就是 K1 一张卡；只消费 89 份冻结 Confluence Markdown；只做内容页 + 参考块清单，不做入口导航（K2）、不做发布通道（K3）、不删代码（K4）
evidence: |2-
  decision-log.md#Talk R1 Q0-b；母任务 PRD K1 scope
acceptance: |2-
  产物目录内不出现入口页/分类导航/发布回滚产物；staging 内容只覆盖 89 份语料
counterexample: |2-
  若本任务交付了入口页、分类导航或发布回滚机制，即判范围越界
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G1-范围与任务身份"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-02
category: complete_user_flow
source: "R-018 / R-031 / R-040"
question: |2-
  K1 的产物写到哪里、目录如何组织、如何标识每次尝试？
status: confirmed
selected_disposition: |2-
  用户选择：父目录 /Users/Hugh/Downloads/KD测试，每次尝试在其下新建批次文件夹（命名=日期+当天自增序号）作为该次根目录；内部仿 CompanyBrain 结构；批次内含 README.md + products/<产品>/<模块>/<页面>.md + _audit/{reference-blocks.jsonl,sources.jsonl,page-manifest.json,run-metrics.json,suspected-synonyms.md}；定位=临时对照产物，正式上库归 K3
evidence: |2-
  decision-log.md#Talk R1 Q1/Q1b/Q16、R2 Q30
acceptance: |2-
  批次目录存在且命名匹配 日期+序号；四个组成部分齐备；CompanyBrain 与 gbrain 零写入
counterexample: |2-
  若产物写进了 CompanyBrain、或批次目录缺少清单/审计文件、或未按批次隔离，即判该决定未落实
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G1-范围与任务身份"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-03
category: success_failure_boundary
source: "R-009 / 两次子代理只读核实"
question: |2-
  现有管线为什么产出不了可检索的知识页（参考型内容到底丢了什么），以及现有仓库里有哪些可复用与必须绕开的资产？
status: confirmed
selected_disposition: |2-
  answered_by_fact: 现有 reader_compiler.py 的拆块是固定 240 行窗口、不认标题、会把表格从中间切断，且会改写文本（_clean_body/_rewrite_reader_links）；仓库已存在保真取向拆块 compiler.py:2940-2991 _paragraph_evidence（标题/列表项/表格行/代码块各自成块，字节从不改写；**注意：它把表格拆成单行**，而本任务 D-010 要求整张表为一块，故必须在其上增加"连续表格行聚合为单块"的步骤，不可原样复用）与 draft.py:96-135 标题树提取（带 lines:start-end 定位）；task4_reader_quality.py:290 有带行区间的表格解析但会规范化单元格，不可用于逐字保真；全仓库无任何模块写 CompanyBrain 形状的 frontmatter（page_model 在 src/ 零出现）
evidence: |2-
  quality/evidence/ 子代理核实结论（本文件 ## 调研 节）；src/knowledge_digest/reader_compiler.py:441-445,621,642；compiler.py:1717-1755,2940-2991；draft.py:65-135
acceptance: |2-
  可复核：重跑同一拆块对比，或直接读上述 file:line
counterexample: |2-
  若能证明固定窗口拆块不会切断表格，或证明已有模块能写 page_model，即判该结论被推翻
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "事实核实（未向用户提问，来源=子代理只读取证）"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-04
category: complete_user_flow
source: "R-009 / R-010 / R-034"
question: |2-
  AC-K1-1…AC-K1-5 各自的判据如何在 K1 内变得可观察、可被测试打破（而不是只证明内部自洽）？
status: confirmed
selected_disposition: |2-
  用户选择：完成判据 = 参考块与原文逐字节一致（AC-02）+ 读者可见「原始文件+标题」且机器可验「指纹+行区间」（AC-04）+ 同输入两次运行字节一致（AC-06）；AC-K1-1 的"冻结分层全量清单"以「冻结本次清单 + 独立第二方法交叉验证」破自证循环；AC-K1-3 的 gbrain 实际检索一项在本卡记为未验证（DEF-002）。**注**：direction-advice 的 F-4 指出本 OI 原问句提供了"仅内部一致性"这一弱化选项，与原始需求固定的验收标准不符，该弱化选项从未被用户选中；问句已按 finding 重写，五项判据均为必需而非可选
evidence: |2-
  decision-log.md#Talk R1 Q24；## 验收标准 AC-01…AC-10
acceptance: |2-
  十项 AC 各有 oracle 与失败判据，且 AC-01 存在独立第二方法
counterexample: |2-
  若验收只比对主方法与自身产物、或把 gbrain 检索写成已通过，即判验收不成立
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G3-验收与完成判据"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-05
category: page_scope
source: "R-021 / R-015(用户答复 Q15)"
question: |2-
  页面粒度是按来源一页、按主题合并，还是两者折中？跨文件的同一主题是否必须合到一页？
status: confirmed
selected_disposition: |2-
  用户选择：按主题合并；主题判定按标题名做确定性合并（同一输入每次得到同样分组），不把主题归组交给模型随机决定；被拒方案：一份来源一页（产物退化为文档仓库）、让模型判主题（破坏可重复运行）、先出候选清单人工确认（人力成本高）
evidence: |2-
  decision-log.md#Talk R1 Q2/Q15
acceptance: |2-
  同一批输入两次运行的页面划分与来源归属完全一致
counterexample: |2-
  若同一输入两次运行得到不同页面划分，或跨文件同标题未合到一页，即判该决定未落实
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G2-页面粒度与主题"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-06
category: page_scope
source: "R-021"
question: |2-
  一份来源文件内部包含多个互不相关的主题时，是否允许拆分到多个页面？
status: confirmed
selected_disposition: |2-
  用户选择：允许拆分到多页；同一份文件的映射关系（一份文件 → 哪几页）必须有可回溯登记
evidence: |2-
  decision-log.md#Talk R1 Q10；## 范围
acceptance: |2-
  任取一份来源文件，可从 _audit/page-manifest.json 反查它进入了哪些页面
counterexample: |2-
  若存在无法回溯到页面的来源文件，或跨主题内容被硬塞进单页，即判该决定未落实
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G2-页面粒度与主题"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-07
category: success_failure_boundary
source: "R-022 / R-023"
question: |2-
  模型在编译中的权限边界是什么（哪些产出允许模型参与、哪些必须机械化、模型对主题的判断是否能改变页面成员），以及如何在同一输入下保证重复运行得到一致产物？
status: confirmed
selected_disposition: |2-
  用户选择：模型只用于起标题与写导读；禁止改写参考型内容与叙述型正文；**页面成员由确定性标题名归组单方决定（见 OI-05/D-003），模型对主题的判断只作建议输出到疑似同义主题报告，不得改变页面成员**（D-007 的权限边界澄清）；模型结果冻结成缓存、缓存键绑定来源内容指纹、命中不重调；未选"全程不调 LLM"与"连叙述型也允许改写"；导读若出现原文没有的信息则该页导读留空并显式标注
evidence: |2-
  decision-log.md#Talk R1 Q7(未选纯规则)/Q14/Q17
acceptance: |2-
  同输入两次运行字节一致；改动来源一个字节导致受影响页面缓存失效并重算；导读逐句可回溯原文
counterexample: |2-
  若参考型内容被模型改写、或其缓存误命中产出陈旧内容，即判该决定被违反
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G4-模型边界与可重复性"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-08
category: page_scope
source: "R-035 / 子代理 gbrain 规则核实"
question: |2-
  产出页面的目录层级与命名如何在**冻结的 gbrain 归一化规则下**建立无碰撞、稳定的页面身份映射（碰撞或歧义检索即判失败），且不依赖导入顺序、不修改 gbrain 配置？
status: confirmed
selected_disposition: |2-
  用户选择：文件名与目录名用英文 slug，中文标题放 frontmatter title；目录仿 CompanyBrain（products/<产品>/<模块>/<页面>.md）。事实依据：gbrain src/core/sync.ts:100-136 的 slug 规则会删除全部非 ASCII 字符，实测 89 份语料仅得 37 个唯一 slug、10 组碰撞覆盖 62 个文件，且 import 按 slug 覆盖。direction-advice 的 F-5 指出原问句只泛问命名、未把碰撞约束写成硬要求；问句与验收已按 finding 强化为「无碰撞 + 歧义即失败 + 不依赖导入顺序」
evidence: |2-
  decision-log.md#Talk R2 Q25；子代理核实 /Users/Hugh/gbrain/src/core/sync.ts:100-136, src/core/import-file.ts:192
acceptance: |2-
  每页文件名与目录名为合法 slug，且**批内唯一**（0 组碰撞）；任何两页映射到同一 slug 即判失败；命名不依赖导入顺序
counterexample: |2-
  若产物出现两个页面映射到同一 slug、或唯一性依赖导入顺序才能成立，即判该决定未落实
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R2-G1-命名与slug"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-09
category: data_state
source: "R-028 / R-029"
question: |2-
  参考块以什么为一个逻辑单元，块内的图片/附件/URL 如何处理，坏表格与坏列表是否原样保留？
status: confirmed
selected_disposition: |2-
  用户选择：整张表 / 整个参数列表 / 整段报错文案 = 一个逻辑单元（块），保留结构；图片与附件 URL 原样保留并显式标注为外部资源链接（不下载、不改写、不删除）；坏表格坏行原样保留而不是修正原文；被拒方案：拆到行或单元格（丢结构、验收复杂度上升）、不分块（拿不出 AC-K1-1 的清单）
evidence: |2-
  decision-log.md#Talk R1 Q13/Q5
acceptance: |2-
  逐块 diff 时结构与字节同时一致；块内 URL 未被改写；带坏行的表格可原样对上
counterexample: |2-
  若某块被拆分粒度改变、URL 被改写或删除、坏行被规范化，即判该决定被违反
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G5-参考内容与附件"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-10
category: success_failure_boundary
source: "R-015 / R-019"
question: |2-
  逐条出处以什么形态呈现——读者看到什么、机器验证什么、行定位是否保留？
status: confirmed
selected_disposition: |2-
  用户选择：双轨——页面向读者显示「原始文件 + 文件内标题（#/##/###）」，不显示行号（理由：原始文件经常更新，行号无意义）；机器在 _audit/sources.jsonl 另存「文件 + 内容指纹 + 行区间」用于证明未改写；回不到原文的内容只进「原文未明确」这一状态（母任务 S3 词表中的显式标注态）并逐条标注，该状态本身也带检索证据；多 claim 句子逐条映射
evidence: |2-
  decision-log.md#Talk R1 Q3/Q3b/Q3c
acceptance: |2-
  机械扫描零「无出处结论」；页面可见文件+标题；旁路文件含指纹与行区间
counterexample: |2-
  若存在既无原文定位也无显式标注的结论行、或错定位、或多 claim 未逐条映射，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G3-验收与完成判据"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-11
category: page_scope
source: "R-013 / R-035 / R-039"
question: |2-
  产物页面的 frontmatter 字段集合、双链形态与托管标记如何确定，才能同时满足同构断言与被下游消费？
status: confirmed
selected_disposition: |2-
  用户选择：frontmatter 覆盖母任务 S1 的 15 字段（title/type/page_model/scope/product/section/module/tier/trust/source_status/quality_status/created/updated/generated_by/tags）；硬断言 page_model=derived 且 generated_by=knowledge_digest_semantic_compiler.py（该名字不以 clean_/sync_ 开头，按 apply_formal_knowledge_metadata.py 的推导规则不会判成 source）；中文标题放 title，文件名用英文 slug；输出 _audit/page-manifest.json（页面清单 + 分类归属）交 K2；事实依据：CompanyBrain 589 个带 frontmatter 的页中有 555 页使用这套正式字段块
evidence: |2-
  decision-log.md#Talk R1 Q19、R2 Q25/Q29；子代理核实 /Users/Hugh/Hugh/Knowledge/tools/apply_formal_knowledge_metadata.py:94-102
acceptance: |2-
  抽 10 页结构校验通过；同时验证四件事：① 15 字段齐备；② `page_model=derived` 断言成立；③ `generated_by` 前缀安全（不以 `clean_`/`sync_` 开头）；④ 输出路径不触及既有 CompanyBrain 正式页。任一失败即判失败
counterexample: |2-
  若任一页缺字段、被 `page_model_for()` 判成 source 或 curated、双链不可解析、或写入触及既有正式页，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G6-页面契约与字段"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-12
category: page_scope
source: "R-015 / R-020 / R-036"
question: |2-
  逐条出处的字段放在页面头还是旁路文件，命名是否沿用既有语义层字段而不新增名字？
status: confirmed
selected_disposition: |2-
  用户选择：页头复用现有 source 字段，写语料相对路径并标注根目录（因核实现有 source 一律指 SourceArchive/...，而本次语料在 /Users/Hugh/Downloads/confluence 原始数据，需显式标注根目录以免误读）；逐条出处的细粒度信息（指纹、行区间、状态）只进 _audit/sources.jsonl；不新增页头字段名；被拒方案：新增 built_from/built_by_run（下游需学新名字）、用现有 sources 列表字段（该字段已有一个私有格式）
evidence: |2-
  decision-log.md#Talk R1 Q4b、R2 Q26；子代理核实 source 字段 48 个页面全部为 SourceArchive 相对路径或自由文本、从不是列表
acceptance: |2-
  页面头的 source 可解析到具体语料文件；_audit/sources.jsonl 含每条 claim 的指纹与行区间
counterexample: |2-
  若页头出现新增字段名、或页头 source 指向不存在的路径、或旁路文件缺指纹/行区间，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G6-页面契约与字段"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-13
category: data_state
source: "R-014 / R-025"
question: |2-
  五类数据状态（ready / known_empty / duplicate_alias / audit_only / 资料未明确）由谁判定、依据什么事实、状态与正文如何保持一致？
status: confirmed
selected_disposition: |2-
  用户选择：全部由程序从事实推导，不由模型判定、不留人工标注；ready=读得到且能拆出块；known_empty=读得到但拆不出任何参考块也无叙述内容；duplicate_alias=内容指纹与其他来源相同（重复来源单页化）；audit_only=只用于追溯不进正文；资料未明确=原文找不到依据（不进事实分母、不写成结论）；被拒方案：程序初判+模型复核（引入不确定性）、留人工标注（交不出可验收产物）
evidence: |2-
  decision-log.md#Talk R1 Q9；母任务 PRD S3
acceptance: |2-
  五类 fixture 逐类核对：状态与正文一致；重复来源单页化；未明确不进分母
counterexample: |2-
  若重复来源发成两页、或未明确写成结论、或未明确进入事实分母，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G5-参考内容与附件"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-14
category: deferred
source: "R-016 / R-041 / R-037"
question: |2-
  母任务列为保留不变量的 300 行分页、分批恢复、来源去重、失败不伪装成功、claim 级溯源，在 K1 新链路里各自落到哪里？
status: confirmed
selected_disposition: |2-
  answered_by_user+fact: 300 行分页与 claim 单 part 归位保留（AC-07）；分批恢复本次不启用（用户选择一次跑完全部 89 份，缓存冻结使重跑代价可接受，分批能力不在本卡激活）；来源去重保留（duplicate_alias 单页化）；失败不伪装成功保留（AC-08 阻塞清单 + 部分失败不写完成）；claim 级溯源保留（AC-04 双轨）；digest 命令换成新行为，旧行为降为 scripts/ 下一次性对照脚本（用户选择，避免"忘了合并命令"导致库内堆积）
evidence: |2-
  decision-log.md#Talk R1 Q7/Q20b、R2 Q28；## 验收标准 AC-06/AC-07/AC-08/AC-09
acceptance: |2-
  五项不变量各有对应断言；旧行为脚本可独立运行；分批不在本卡激活且不伪装为已实现
counterexample: |2-
  若分页被绕过、或失败被写成完成、或旧行为脚本无法运行，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "R1-G7-非目标与流程约束（未向用户提问，来源=母任务S6+用户Q20b）"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-15
category: success_failure_boundary
source: "R-024"
question: |2-
  部分失败时 K1 的行为是什么——整批中止、部分产出并显式报告阻塞，还是静默跳过？
status: confirmed
selected_disposition: |2-
  用户选择：部分成功 + 显式列表报告阻塞项（给出文件、位置、原因、影响）；被拒方案：全有或全无（一份有问题就全白干，容易永远交不出）、能写多少写多少不报阻塞（违反"失败不伪装成功"不变量）
evidence: |2-
  decision-log.md#Talk R1 Q8；## 完整用户旅程 J2/J4/J6
acceptance: |2-
  阻塞清单存在且覆盖所有未处理项；产物中无静默跳过
counterexample: |2-
  若存在未登记在阻塞清单里的跳过项，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G8-成功与失败边界"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-16
category: complete_user_flow
source: "R-012 / R-018 / R-038"
question: |2-
  从投料到产物落地的完整用户旅程是什么，每一步成功与失败的样子分别是什么？
status: confirmed
selected_disposition: |2-
  已定：J1 投料（打印计划后直接运行，不等人确认；一次处理全部 89 份）→ J2 解析拆块 → J3 主题归组（确定性）→ J4 语义编译（模型走缓存）→ J5 页面结构校验 → J6 写入批次目录（无原子发布，中断留半成品需显式报告）→ J7 阅读与查询 → J8 复跑与核对 → J9 维护；每步的成功/失败样子见 ## 完整用户旅程 表
evidence: |2-
  decision-log.md#完整用户旅程；## Talk R1 Q21、R2 Q28
acceptance: |2-
  九步各有可观察的成功与失败状态；J6 的无原子发布限制被显式记录
counterexample: |2-
  若某一步只有成功路径没有失败判定，即判旅程未梳理完整
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "R1-G9-用户旅程与运行方式"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-17
category: complete_user_flow
source: "R-032 / 子代理 CompanyBrain 核实"
question: |2-
  既有 CompanyBrain 的页面契约在真实数据里有多一致，K1 应以哪一档为基准，以及 K1 是否要读既有页面？
status: confirmed
selected_disposition: |2-
  answered_by_user+fact: 用户选择完全不读、不合并、不比对 CompanyBrain 的 1347 个页面；事实依据：1347 个 .md 中仅 589 个（43.7%）有 frontmatter；带 frontmatter 的 589 页中 **555 页用正式 15 字段块**（口径基准），另有 **121 页用另一套方言**（page_type/language/source_type/semantic_tier，无 trust/tier/quality_status）——两集合**有重叠**（676−589=87），故不得相加；758 页无 frontmatter（Products 402、_gbrain 356）。**AC-03 以 555 页的正式 15 字段块为基准，方言页不作为基准也不作为反例**；page_model 分布 derived 465 / curated 47 / source 43；K1 以正式 15 字段块为基准
evidence: |2-
  decision-log.md#Talk R1 Q22；子代理核实 1347 页字段普查（## 调研）
acceptance: |2-
  产物页字段与 555 页正式块一致；K1 运行期间对 CompanyBrain 零读写
counterexample: |2-
  若 K1 读取或改动了 CompanyBrain 任一页面，即判写权边界被破坏
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "R1-G10-与既有知识库的关系"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-18
category: non_goals
source: "R-030 / R-017"
question: |2-
  本任务明确不做的事有哪些？
status: confirmed
selected_disposition: |2-
  用户选择 5 项 + 事实补充：不做入口页与分类导航（K2）、不做 staging+原子切换+回滚与四类负例（K3）、不做源码瘦身删码与三项度量（K4）、不做真实查询集对照验收（K3）、不引入向量库/图数据库/服务化/前端/多格式输入；另据 S7 写权边界：不改既有 CompanyBrain 正式页、不改停摆自动化流水线、不改 gbrain 配置与索引状态
evidence: |2-
  decision-log.md#Talk R1 Q7、R1 Q22、R1 Q18；## 非目标 NG-001…NG-008
acceptance: |2-
  逐条负向检查：NG-001…NG-008 未出现在本卡实现中
counterexample: |2-
  若实现中出现任一非目标项，即判范围越界
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G7-非目标与流程约束"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-19
category: deferred
source: "R-026 / R-027 / R-033"
question: |2-
  哪些事项明确延期到其他阶段或后续任务？
status: confirmed
selected_disposition: |2-
  用户确认 5 条延期及归属：DEF-001 语料 89 份 sha256 重核（owner=用户，触发=需要对外声明验收结论有效时；注：本次核实已证明当前磁盘与冻结清单 89/89 一致，故本条风险已降级）；DEF-002 gbrain 实际索引与按 slug 检索验证（触发=产物进入正式知识库目录后）；DEF-003 原子发布/回滚/last-known-good 与失败成本计数（owner=K3）；DEF-004 真实查询集对照验收（owner=K3）；DEF-005 停摆流水线接管与旧 synthesize_* 主题移交（owner=用户）
evidence: |2-
  decision-log.md#Talk R1 Q6/Q18/Q23；## 风险与延期交接
acceptance: |2-
  五条延期各有 owner、触发条件与关闭条件；AC-K1-3 的 gbrain 检索项在本卡标记为未验证
counterexample: |2-
  若把任一延期项写成已通过，即判为本卡伪造完成
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G11-延期与开放项"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-20
category: success_failure_boundary
source: "母任务成本硬约束 / direction-advice F-8（本阶段新增）"
question: |2-
  K1 编译链路一次运行的 provider 调用预算如何控制在约 150 次量级（哪些环节必须机械化、哪些才允许调模型），以及失败运行的耗时/调用数/token 如何真实非空记录？
status: confirmed
selected_disposition: |2-
  answered_by_user+fact: 用户已在 Q14 限定模型只用于起标题/写导读/判主题，且在 Q17 选择模型结果冻结成缓存命中不重调——**参考块搬运、主题归组、页面拼装、结构校验、指纹与行区间计算全部机械化，不产生 provider 调用**；模型调用量与"合并后的主题数"同阶而非与"claim 数"或"源文件数×行数"同阶，因此不构成逐 claim 调模型的预算风险。失败运行的三项计数（耗时/调用数/token）按母任务硬约束必须真实非 null 记录，不得写 0 或 null 冒充
evidence: |2-
  decision-log.md#Talk R1 Q14/Q17；母任务 S5「失败运行的耗时/调用数/token 必须真实非 null」；AC-K1-2（参考内容不经模型改写）
acceptance: |2-
  运行时打印的预计调用数与实际调用数同阶（不出现逐 claim 调用）；失败运行记录中耗时、调用数、token 三项均非 null；改变来源一个字节后缓存失效并按新主题数重新调用
counterexample: |2-
  若实现出现逐 claim 或逐块的模型调用、或失败运行的任一成本计数为 null/0/fabricated，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "母任务成本硬约束（未向用户提问，来源=方向盲审F-8+用户Q14/Q17）"
```
```yaml
task_id: task7-semantic-layer-compiler
outline_version: v3
oi_id: OI-21
category: success_failure_boundary
source: "direction-advice F-7（本阶段新增）"
question: |2-
  每个冻结来源参考块到输出页面锚点的完整覆盖关系如何建立与登记，合并/拆分/重复/未映射各自的规则是什么，未映射或被覆盖的块算不算交付失败？
status: confirmed
selected_disposition: |2-
  answered_by_user+fact: 用户已在 Q2/Q10 选择按主题合并且允许一份文件拆到多页，在 Q24 选择冻结清单 + 独立第二方法交叉验证，在 Q6 选择沿用现有冻结来源清单。据此建立覆盖不变量：① 每个参考块在 `_audit/reference-blocks.jsonl` 中有一条带 `block_id` 与 `content_hash` 的记录；② 每条记录必须带唯一的输出锚点（`page_path` + 页内定位），合并与拆分都必须在记录中体现；③ 一份来源进入多页时，来源→页面映射可从 `_audit/page-manifest.json` 反查；④ 未映射的块必须出现在阻塞清单而不是静默丢弃；⑤ 任一参考块被两个输出锚点重复承载时必须显式标注为重复（`duplicate_alias`）而不是静默复制
evidence: |2-
  decision-log.md#Talk R1 Q2/Q10/Q24、R1 Q6；## 验收标准 AC-01/AC-05/AC-08
acceptance: |2-
  参考块清单中每条记录的 `block_id` 集合与独立第二方法的块集合一致；每条记录都有非空输出锚点或位于阻塞清单；无第三态的块（既无锚点也不在阻塞清单）
counterexample: |2-
  若存在既无输出锚点也不在阻塞清单的参考块，或同一块被静默重复承载而无重复标注，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "母任务保真要求（未向用户提问，来源=方向盲审F-7+用户Q2/Q10/Q24）"
```

## Talk

### Talk Round 1（2026-09-13）· 用途：核实现有实现与冻结物，收敛 K1 的方向、边界与落地形态

开始前先做事实核对（不向用户提问）：仓库与 worktree 状态、WorkflowHub 身份与存储根、三份冻结物是否存在、
现有代码里是否已有可复用的读取/拆块/页面写出能力、CompanyBrain 的真实页面契约现状。核对结果见 `## 调研`。

**影响排序**：本组问题按"是否直接决定方向"从高到低排序；互相独立的轴放在同一组，有依赖的轴拆到后续组。

| 题号 | 影响 | 决策轴（单轴） | 用户答复 | 台账 |
| --- | --- | --- | --- | --- |
| Q0-a | high | 任务 ID（决定 worktree 路径与分支名） | `task7-semantic-layer-compiler` | `## 任务身份` |
| Q0-b | high | 任务范围 | 就是 K1 一张卡 | OI-01 |
| Q0-c | high | 任务类型 | 普通任务 | `## 任务身份` |
| Q1 | high | 产物落点与写入边界 | 自定义：`/Users/Hugh/Downloads/KD测试` | OI-02 |
| Q1b | medium | 该目录的定位与内部形态（多选） | 临时对照产物 + 仿 CompanyBrain 结构；**补充：该目录是父目录，每次尝试在其下新建批次文件夹** | OI-02 |
| Q2 | high | 页面合并粒度 | 按主题合并 | OI-05 |
| Q3 | high | 行定位跟谁跑 | 自定义：**不要行号**，只要"原始文件 + 子模块名"（理由：原始文件经常更新） | OI-10 |
| Q3b | high | 行定位与"文件+标题"的关系 | 双轨 | OI-10 |
| Q3c | medium | "子模块名"的层级 | 文件内标题（`#`/`##`/`###`） | OI-10 |
| Q4 | medium | 新增溯源字段命名 | 沿用现有命名 | OI-12 |
| Q4b | medium | 逐条出处落地形态 | 页头复用 `source`，细粒度走旁路文件 | OI-12 |
| Q5 | medium | 图片/附件 URL 处理 | 原样保留 + 标注 | OI-09 |
| Q6 | high | 验收基准来源 | **B：直接用现有清单，不重算** | OI-19 / RISK-001 |
| Q7 | high | 非目标（多选） | 选 5 项；**未选"全程不调 LLM"** | OI-18 / NG-003…NG-007 |
| Q8 | high | 部分失败时的行为 | 部分成功 + 显式列表报告阻塞项 | OI-15 |
| Q9 | medium | 五类数据状态由谁判 | 全部由程序从事实推导 | OI-13 |
| Q10 | medium | 一来源多主题能否拆页 | 允许拆分到多页 | OI-06 |
| Q13 | medium | 参考块单元大小 | 整张表/整个列表算一块 | OI-09 |
| Q14 | high | 模型的权限边界 | 允许起标题/写导读/判主题；禁止改参考内容 | OI-07 |
| Q15 | high | "同一主题"的判定方式 | 按标题名确定性合并 | OI-05 |
| Q16 | low | 批次文件夹命名 | 日期 + 当天自增序号 | OI-02 |
| Q17 | high | 可重复运行 vs 模型不确定性 | 模型结果冻结成缓存，命中不重调 | OI-07 / OI-14 |
| Q18 | medium | AC-K1-3 的 gbrain 检索项 | 不碰 gbrain，只校验 slug 规则 | OI-19 / DEF-002 |
| Q19 | medium | 与 K2 的交接产物 | 输出页面清单 + 分类归属 | OI-11 |
| Q20 | high | 新链路怎么被调用 | 自定义（反问）：为什么要新建命令？担心将来忘了合并、库里堆积垃圾 | OI-14 |
| Q20b | high | `digest` 门牌号归属 | digest 换新行为，旧行为降为一次性脚本 | OI-14 / D-018 |
| Q21 | low | 成本预告与人工闸门 | 先打印计划，不等人确认直接跑 | OI-16 |
| Q22 | high | 与 CompanyBrain 既有页面的关系 | 完全不管既有页面 | OI-17 / D-014 |
| Q23 | high | 延期项与归属确认 | 确认 5 条延期与归属 | OI-19 |
| Q24 | high | AC-K1-1 的验收基准循环 | 冻结清单 + 独立第二方法交叉验证 | OI-04 / D-011 |

### Talk Round 2（2026-09-13）· 用途：在核实事实到位后，收敛实现层决策

Round 1 结束后派子代理完成六项只读核实（语料 hash 对照、冻结 oracle 形状、gbrain slug 规则、
CompanyBrain 字段语义、可复用拆块代码、测试基线）。据核实结果，本组只问三项会直接改变实现的决策。

| 题号 | 影响 | 决策轴（单轴） | 关键事实（提问前已摆给用户） | 用户答复 | 台账 |
| --- | --- | --- | --- | --- | --- |
| Q25 | high | 页面文件命名 | gbrain 的 slug 规则删除全部非 ASCII 字符：89 份语料仅得 37 个唯一 slug、10 组碰撞覆盖 62 个文件，import 按 slug 覆盖 | 文件名用英文 slug，中文放 title | OI-08 / D-015 |
| Q26 | medium | `source:` 字段装什么 | 现有 `source:` 一律指 `SourceArchive/...`（相对 Knowledge 根），而本次语料在 Downloads 且不在知识库内 | 写语料相对路径，并标注根目录 | OI-12 / D-005 |
| Q27 | high | 红色测试基线怎么算 | 基线 `16 failed, 892 passed, 3 skipped`，退出码 1，16 个失败全在 `test_task2a_reader_bundle.py` | 先查清 16 个失败、当基线写进计划 | OI-14 / D-016 |
| Q28 | high | 一次运行范围 | 跨批次无法合并同一主题，会破坏"按主题合并"目标 | 一次跑完全部 89 份 | OI-16 / D-012 |
| Q29 | high | `generated_by` 取值 | 推导规则：以 `clean_`/`sync_` 开头 → `page_model=source`（有被清理风险）；有 `generated_by` 但不是那些前缀 → `derived` | `knowledge_digest_semantic_compiler.py` | OI-11 / D-006 |
| Q30 | medium | 批次目录文件构成 | 参考块可能上千个，全嵌页面会淹没正文 | 页面 + 一份清单 + 两份审计文件 | OI-02 / D-017 |

**影响重排记录**：

- Q14（允许模型写标题/导读）与母任务不变量"可重复运行"冲突 → **派生** Q17；用户选择缓存冻结，冲突消解。
- Q4（沿用现有命名）经核实发现 `source` 已被 48 页占用且语义为归档路径 → **派生** Q4b，再经 Q26 细化。
- Q20（新链路怎么调用）被用户反问"为什么要新建命令"，说明原轴设错 → **派生** Q20b，轴改为"`digest` 门牌号归属"。
- Q3（不要行号）与 AC-K1-4「行定位」硬要求冲突 → **派生** Q3b；用户选择双轨，冲突消解而非放宽 AC。
- Q7 未勾选"全程不调 LLM"被识别为关键信号（非遗漏）→ **派生** Q14 确认模型边界。
- 事实核实发现 gbrain slug 规则会删空中文 → 在 Round 2 **派生** Q25，直接改变页面命名方式。
- 事实核实发现基线测试为红 → 在 Round 2 **派生** Q27，改变验收口径。
- Q24 的基准循环问题是主会话在核实后新识别的事实，不属派生而是新增轴。

## 调研

### 取证方式（R-005 主会话上下文控制）

两轮取证全部交由子代理只读完成，主会话只保存结论与证据引用。子代理均未修改任何文件、
未运行 `digest` CLI、未调用任何 provider、未写入 Downloads 或 CompanyBrain。

### 取证一：K1 相关事实盘点（子代理只读）

| 事实 | 结论 | 证据 |
| --- | --- | --- |
| 语料规模 | `/Users/Hugh/Downloads/confluence 原始数据` 下 4 个顶层目录、89 份 `.md`、13,050 行；目录 `emm for android ` **末尾含空格**（27 份） | 子代理实测；`counter = {emm for android :27, GoInsight:22, emm for ios:20, merchant system:20}` |
| 语料形态 | 不是 Confluence storage XML：`id_remap`/`<ac:`/`ri:`/宏 XML 命中 0 份；残留仅为 `pax-sz.atlassian.net` 绝对 URL（81 份）、附件 URL（8 份）、图片引用（63 份） | 子代理全语料 grep |
| 语料结构特征 | 89 份中 0 份有 frontmatter；仅 3 份含 `# ` H1；表格常"粘"在 bullet 后，存在 `| | Reseller User Log` 这类坏行 | 子代理逐文件统计 + 代表文件逐行核对 |
| 现有代码是否写 CompanyBrain 形状的 frontmatter | **否**。`page_model` 在 `src/` 下 0 命中；唯一的写入者在仓库外 `/Users/Hugh/Hugh/Knowledge/tools/apply_formal_knowledge_metadata.py` | `grep -rn page_model src/knowledge_digest/*.py` |
| 可复用的读取器 | `reader_compiler.py:642` 已遍历任意裸 Markdown 目录；`:302` 已硬编码 `raw://confluence/` 溯源前缀 | 子代理 file:line |
| CLI 现状 | `cli.py` 无子命令；`pyproject.toml:15` 实际注册的 `digest` 入口是 `simple_cli.py`（与 AGENTS.md 的描述不一致） | 子代理核实 |

### 取证二：六项定向核实（子代理只读）

| 核实项 | 结论 |
| --- | --- |
| 语料 sha256 与冻结清单 | **89/89 全部一致**。`[task4-source-coverage-89-input.v1] match=89 mismatch=0 missing=0 absent=0`；`[task5-source-page-manifest-v2] match=89 mismatch=0 missing=0 absent=0`；task5 的 `byte_count`/`line_count`/`expected_status` 同样 0 差异 |
| 聚合哈希可复算性 | task4 oracle 的 `source_content_tree_hash` **精确复算成功**（`de977b15…`）；task5 的 `source_set.path_set_digest` **精确复算成功**（`7484673e…`）；**但** task4 的 `manifest_hash`（声明 `e1842f68…`）与 task5 的 `source_snapshot.snapshot_id`（声明 `…fc6cbe66…`）**试遍 70/30 种算法变体均无法复算** |
| 冻结 89 案例 oracle 能否当主题依据 | **不能**。`page_type` 89/89 为 `procedure`、`criticality` 89/89 为 `non_critical`，无 `product`/`module`/`topic_key`/`section` 字段，无法分割语料；`companybrain_entry_path` 89/89 为 `null`，无期望页面清单 |
| gbrain slug 规则 | `slugifySegment` 用 `[^a-z0-9.\s_-]` **删除全部非 ASCII**（即所有中文）；slug 为相对索引根的路径、根目录名不影响 slug；`import` 无需注册、`sync` 需注册 source；**slug 在 source 内唯一**，import 按 slug **覆盖**。套用本语料实测：**89 文件 → 37 个唯一 slug，10 组碰撞覆盖 62 个文件**（`goinsight` 被 16 文件占用等） |
| CompanyBrain 字段语义 | 1347 个 `.md` 中 589 个有 frontmatter（0 个 YAML 错误）、758 个没有；带 frontmatter 的 589 页中 555 页用正式 15 字段块（基准），**121 页是另一套方言**（两集合有重叠，不可相加）；`source:` 48 页全部为 `SourceArchive/...` 相对路径或自由文本、从不是列表；`sources:` 仅 1 页且是列表；`page_model` = derived 465 / curated 47 / source 43，且 `source`(43) 与 `trust: low`+`source_status: raw_cleaned`(43) **完全相同集合** |
| 可复用/必须绕开的代码 | **可复用但需加工**：`compiler.py:2940-2991` `_paragraph_evidence`（标题/列表项/表格行/代码块各自成块，"The bytes are never rewritten"；**它按行拆表格，与 D-010「整张表为一块」冲突，需追加表格行聚合步骤**）、`compiler.py:1717-1755` 块级指纹与行列坐标、`draft.py:96-135` 标题树提取（`fragment_locator = lines:start-end`）。**必须绕开**：`reader_compiler.py:441-445` 固定 240 行窗口拆块（会切断表格）、`_clean_body`/`_rewrite_reader_links`（会改写文本，破坏逐字保真）；`task4_reader_quality.py:290` 表格解析带行区间但会规范化单元格，不可用于逐字保真 |
| 测试基线 | `uv run --frozen pytest -q` → **`16 failed, 892 passed, 3 skipped`**，退出码 1，耗时 51.13s；16 个失败全部在 `tests/acceptance/test_task2a_reader_bundle.py`（旧 reader bundle 路径，正是本卡要替换的行为） |

### 调研结论对方向的影响

1. 保真的技术前提成立：语料干净（无宏 XML），且仓库已有"字节从不改写"的拆块实现可复用；缺的是**以保真为第一目标的编译链路**，不是拆块能力。
2. gbrain slug 规则是**必须处理的硬约束**，已在 Round 2 转为用户的命名决定（英文 slug 文件名）。
3. 冻结清单可用（89/89 一致），但**两个聚合哈希字段不可复算**——登记为事实缺陷，不阻塞本卡，也不写成"已验证"。
4. 基线测试为红是**既有事实**，K1 必须以"失败清单不变"而非"全绿"作为回归口径。

## grill

### Grill（2026-09-13）· 用现有 ADR、CONTEXT 术语与领域模型压力测试已选方案

**先核实、再提问**：下列检查全部读自本 worktree 的现有文档与已核实事实；能从文档得到的答案不向用户重问。
本轮**不产生新问题**（理由见「四项退出检查」），因此无 `ask → wait → reply → resume` 事件。

#### 全需求覆盖矩阵（五类原始消息 → 决策轴 → 台账）

| # | 原始消息类 | 覆盖的决策轴 | 用户选择或事实依据 | 绑定 |
| --- | --- | --- | --- | --- |
| 1 | 目标和成功意图 `goal` | 完成判据是什么、及格线怎么定 | 用户 Q24 + Q27；AC-02/AC-04/AC-06 | OI-04, D-011, AC-01…AC-10 |
| 2 | 用户旅程与页面/入口范围 `flow_or_surface` | 落点/批次结构、页面粒度、拆分、命名、与既有页关系 | 用户 Q1/Q1b/Q2/Q10/Q16/Q19/Q22/Q25/Q30 | OI-02, OI-05, OI-06, OI-08, OI-11, OI-17, D-002, D-003, D-015, D-017 |
| 3 | 数据、状态与状态变化 `data_or_state` | 五类数据状态判定、参考块单元、URL 处理 | 用户 Q9/Q13/Q5 | OI-09, OI-13, D-009, D-010 |
| 4 | 成功、失败、取消与验收边界 `success_failure_acceptance` | 部分失败行为、可重复性、基线口径、出处双轨、模型边界 | 用户 Q8/Q17/Q27/Q3b/Q14/Q15/Q29 | OI-07, OI-10, OI-14, OI-15, D-004, D-006, D-007, D-008, D-016 |
| 5 | 约束、非目标、延期与风险 `constraint_non_goal_defer` | 5 项非目标 + 写权边界、延期项归属、命令门牌 | 用户 Q7/Q20b/Q22/Q23 | OI-18, OI-19, NG-001…NG-008, DEF-001…DEF-007 |

五类原始消息全部落到决策轴，无整类缺失；每条高/中影响轴都有用户真实选择（见 `## Talk`），无「不提问」项。

#### 专项挑战一：与 ADR 0013 的冲突（**实质冲突，必须登记**）

ADR `docs/adr/0013-write-into-existing-semantic-layer.md` 的状态是 **accepted（2026-09-12）**，其 Decision 含四条。

| ADR 0013 的决定 | 本任务已选方向 | 一致性判定 |
| --- | --- | --- |
| KD 输出是语义层内容，不是并行 bundle | K1 输出写入 `/Users/Hugh/Downloads/KD测试` 批次目录（**不是** CompanyBrain） | **不冲突但需限定**：母任务 PRD 明确「K1 只产出 staging 产物，上库走 K3 通道」，故 ADR 0013 的"写进语义层"由 K3 兑现，K1 不是该决定的承担者。本任务必须显式声明此限定，避免被读成 K1 违反 ADR |
| 层契约/命名/链接风格是权威，KD 服从 | K1 服从 15 字段块 + `[[wikilink]]` + 目录命名 | 一致 |
| **只能引入一个新的页面级溯源字段，且必须在层的元数据权威中登记**（字面名与值形态在 build-spec 固定） | 用户选择**不新增任何页头字段**：页头复用既有 `source`，逐条出处细粒度只进旁路文件 `_audit/sources.jsonl` | **ADR 的授权未被兑现，但也没有被违反**——本任务引入了零个新字段，因此"唯一允许的一个字段"处于未使用状态。风险在**旁路文件不在层内**：它不进入 CompanyBrain，因此既不被层契约覆盖，也不受元数据脚本管辖；K3 上库时该文件不会随页面迁移 |
| 接管旧 `synthesize_*` 主题前必须先做只读对比并在自动化规则中登记 | K1 不做对比、不登记（母任务 PRD 把接管登记移交「流水线修复任务」） | 一致（延期已登记 DEF-005），但意味着本任务不产生任何 ADR 0013 合规证据 |

**Grill 结论 G-001**：ADR 0013 的"一个新溯源字段"授权与本任务的"零新字段 + 旁路文件"选择**不矛盾但相互悬空**。
必须在本任务显式记录：① 本任务不使用该授权；② 若 K3 上库时仍希望逐条出处可被层内消费者读取，
需重新决定是"启用那一个字段"还是"把旁路文件一并纳入层管理"。若不做此记录，K3 会以为授权已被消费。

#### 专项挑战二：术语与既有领域模型的一致性

| 术语（CONTEXT.md 已定义） | 本任务用法 | 判定 |
| --- | --- | --- |
| **语义知识层** = 物理位置 `/Users/Hugh/Hugh/Knowledge/CompanyBrain`（页面 + 元数据脚本 + gbrain 索引） | K1 产物落在 Downloads 批次目录，**不是**语义层 | 术语一致但**必须避免误称**：本任务材料不得把批次目录称为"语义层"或"知识库"。已在 `## 范围` 与 OI-02 中限定为"临时对照产物" |
| **唯一生产者（同一主题）** = 同一路径只能由一个生成器负责；接管前须只读对比并登记 | K1 不写 CompanyBrain，故本期不产生生产者冲突；但 K1 产物**已经与既有页面同主题**（语料覆盖 GoInsight/EMM/merchant system/MAXSTORE，CompanyBrain 已有这些产品的正式页） | **风险成立**：K3 上库时同一个主题路径会有"既有人工/`synthesize_*` 页"与"KD 新页"两个候选，必须由 K3 决定取代关系。登记为 RISK-011 / DEF-008 |
| **真实查询集验收** = 唯一被接受的"知识可用"证据 | K1 不做（NG-006，K3 范围） | 一致（范围划分），但意味着 **K1 交付时"知识是否可用"尚无唯一被接受的证据**；K1 只能给出内部一致性证据。已在 `## 验收标准` 的对照基线声明中写明 |
| **证据零容忍** = 每条结论必须回到原文具体位置，不接受只有页面级出处 | K1 的 AC-04 实现为双轨（页面显示文件+标题，机器存指纹+行区间） | **需要澄清一处张力**：CONTEXT 的 `_Avoid_` 明确写了「不接受只有页面级出处」。本任务的**页头 `source:` 是页面级出处**，因此它不能作为证据零容忍的满足物；真正的满足物是旁路文件里的逐 claim 指纹与行区间。已在 AC-04 中把 oracle 定为"解析器扫描 `_audit/sources.jsonl` 零违规"，页头 `source` 只作读者导航 |

#### 专项挑战三：更小或更稳的替代路径

- 本任务是否可以用**更小**的范围达成原需求？已评估并否决：若只做"参考块清单 + 保真校验"而不产出页面，
  则读者侧零收益、下游无可消费产物，等于把 K1 的全部价值推给 K3；若只做"页面编译"而不做参考块清单，
  则 AC-K1-2 的零丢失无从机器验证。两部分互相构成对方的 oracle，不可拆。
- 是否存在**已被拒绝但应复议**的选项？用户已拒：一份来源一页、模型判主题、候选清单人工确认、
  新增 `built_from` 字段、直写 CompanyBrain、下载附件、只校验不做第二方法。逐项检查后无新事实推翻这些拒绝。
- 是否引入了**没有故障证据或硬约束支撑的长期能力**？有且已收窄：分批与恢复（母任务 S6 列为保留不变量，
  但本任务用户选择一次跑完全部 89 份）→ 记为「本卡不激活」而非"已实现"，避免留下无故障证据的空壳能力（OI-14）。
- 是否**重复已有能力**？拆块与标题树提取在 `compiler.py` / `draft.py` 已有实现，本任务应优先复用而非重写；
  已在 `## 调研` 记录可复用清单与必须绕开的清单（NG 之外的实现约束）。

#### 四项退出检查

| 检查 | 结论 |
| --- | --- |
| 是否有会改变方向且 Agent 无法自答的剩余问题？ | **无**。G-001 的处置是"记录本任务不使用该授权 + 登记 K3 需重新决定"，属记录义务；术语张力已通过 AC-04 的 oracle 选择消解；生产者冲突已登记延期。故本轮零问题 |
| 是否与任一 accepted ADR 冲突？ | 无直接冲突；有一处**授权悬空**（G-001）与一处**范围限定需显式声明**（ADR 0013 的写权由 K3 兑现），均已记录 |
| 是否与既有领域术语冲突？ | 无冲突；有一处**用词风险**（不得把批次目录称为语义层）与一处**证据层级澄清**（页头 source 是页面级出处，不构成证据零容忍的满足物） |
| 是否引入了无支撑的长期能力或重复已有能力？ | 已收窄分批能力为"不激活"；已登记可复用清单以避免重写拆块 |

#### 文档动作

- **CONTEXT.md**：本任务的术语（"临时对照产物""批次目录""参考块""双轨出处"）在 make-decision 阶段不写入仓库
  `CONTEXT.md`；理由是这些是 K1 的实现语义，按母任务安排「KD 溯源字段字面名由 K1 的 build-spec 阶段冻结，登记进 `CONTEXT.md`」。
  因此 **CONTEXT changed = 否（本阶段），留待 build-spec**；此项必须由 build-spec 兑现，登记为 OPEN-006。
- **ADR**：本任务**不新增 ADR**（无新的不可逆架构决定）；ADR 0013 的授权悬空问题以 G-001 记录在决策记录内。
  **用户在 approve-decision 时已决定：不改 ADR 0013，只在本记录内声明"本任务不使用该授权"**（见 `## 最终确认`）。
- **规格/领域模型变更（第三项结构化判断）**：本阶段**不修改** `CONTEXT.md`、`docs/adr/` 或任何既有规格文件。
  理由：本任务的术语（临时对照产物、批次目录、参考块、双轨出处）属 K1 的实现语义，按母任务安排应由
  **build-spec** 在冻结溯源契约时登记进 `CONTEXT.md`（OPEN-006）。本阶段若提前改动，会与 build-spec 的
  冻结动作重复并可能产生两份口径。故第三项判断 = **规格/领域模型 changed: 否（本阶段），留待 build-spec**。


## 决定条目 D*

### Talk Round 3（step 7）· 用途：处理 direction-advice 的建议、矛盾、关键假设与剩余风险

**本轮的输入**：direction-advice 的真实建议（9 条实质 finding，见 `## 审查处置`）。逐条判断后：
F-1…F-8 均为**本阶段内可修复**的缺口（用户在 Round 1/2 已就相关轴作出真实答复，缺的是把答复写成够强的问句与验收），
故按"发现的 finding 必须先在当前 stage 修复"的要求在本阶段直接修复，不向用户重提已答问题；
F-9 属已核实事实缺陷，登记为 RISK-008 / DEF-007。**本轮无新增用户裁决项**，因此无 `ask → wait → reply → resume` 事件。

**本轮消解的矛盾（共 3 处，均为真实矛盾，不是措辞问题）**：

| # | 矛盾 | 消解方式 |
| --- | --- | --- |
| C-1 | 用户"读者只看到文件+标题、不要行号" vs AC-K1-4 要求"行定位" | 双轨（Q3b）：页面面向读者显示文件+文件内标题，机器在 `_audit/sources.jsonl` 存指纹+行区间。矛盾消解而非放宽 AC |
| C-2 | 用户"允许模型写标题/导读" vs 不变项"同输入同结果" | 缓存冻结（Q17）：模型结果按键冻结，缓存键绑定来源内容指纹；同输入第二次运行字节一致 |
| C-3 | 用户"页头复用现有 `source` 字段、不新增" vs ADR 0013「允许且仅允许新增一个新的页面级溯源字段」 | 本任务引入**零个**新字段，该授权处于未使用状态（不违反）；但旁路文件不在层内，故登记 RISK-012 + Grill G-001，由 K3 决定是否启用该授权或把旁路文件纳入层管理 |

**关键假设（如被推翻则需重算方向）**：

| # | 假设 | 若被推翻的后果 | 当前证据 |
| --- | --- | --- | --- |
| A-1 | 语料在冻结后不再变动 | 全部"零丢失"结论的基准失效 | 已核实 89/89 sha256 与两份冻结清单一致；风险已降级（RISK-001） |
| A-2 | 参考型内容可以不经模型改写而完整搬运 | AC-02 的可行性基础消失 | `compiler.py:2940-2991` 已有"字节从不改写"的拆块实现可复用 |
| A-3 | 主题可由标题名确定性归组，且归组结果对读者可接受 | 页面划分需引入模型判断，破坏可重复性 | 语料 89 份仅 3 份含 H1、多为 H2/H3 结构；RISK-004 已登记同义不同名的残留风险 |
| A-4 | 模型调用量与"合并后主题数"同阶（非逐 claim） | 单次运行成本可能远超 150 次可接受量级 | OI-20 已把该假设写成硬约束与验收项 |
| A-5 | 产物落在 Downloads 批次目录不会影响 K1 的验收有效性 | 批次目录被清理导致证据失效 | RISK-006 已登记；正式留存归 K3 |

**剩余风险清单**：RISK-002…RISK-012（见 `## 风险与延期交接`），其中本卡内**无法消除**的两条是
RISK-002（无原子发布能力，属 K3 范围）与 RISK-007（gbrain 实际检索未验证，DEF-002）。

**Round 3 结论**：direction-advice 的建议已全部处置；无未解的、会改变方向的剩余问题；无新的用户裁决项。

### D* 决定条目

| id | 选择 | 理由与事实依据 | 被拒方案（含拒绝理由） | 影响范围 | 风险 | supersedes |
| --- | --- | --- | --- | --- | --- |
| D-001 | 本任务 = 母任务 PRD 的 K1 一张卡；只消费 89 份冻结 Confluence Markdown；只做内容页 + 参考块清单 | 用户答复；母任务 K1 scope 明文；K2/K3/K4 各有 owner | K1+K2 合并（验收口径模糊、页面范围问题翻倍）；暂不定范围（talk 发散、易卷入其他卡） | 全部 OI 的边界 | 范围偏窄导致"读者能否找到"在 K1 内无法回答（已声明为 AC 未覆盖项） | — |
| D-002 | 产物写入 `/Users/Hugh/Downloads/KD测试/<日期>-<序号>/`，内部仿 CompanyBrain 结构，含 README + products/ + _audit/ 三件 | 用户 Q1/Q1b/Q16/Q30；该目录定位为临时对照产物；`_audit/` 隔离审计面与阅读面 | 直写 CompanyBrain（架空 K3 的原子发布/回滚，违反 PRD 的 K1 只产 staging）；写 KD 自己产物目录（不在语义层、gbrain 检索不到）；只出预览不写盘（AC 无法落地） | 交付物落点、写权边界、K3 交接 | RISK-006（Downloads 可能被清理） | — |
| D-003 | 页面按主题合并，允许一份来源拆到多页 | 用户 Q2/Q10；89 份语料跨目录讲同一件事，按来源一页会退化为文档仓库 | 一份来源一页（产物不像知识库）；按内容集中度灵活拆（不可机器判定，破坏可复算） | 页面范围、AC-01/AC-05 | RISK-004（同义不同名合并不彻底） | — |
| D-004 | 出处双轨：页面显示「原始文件 + 文件内标题」，机器另存「文件 + 指纹 + 行区间」 | 用户 Q3/Q3b/Q3c；行号对读者无意义（原文会更新），但"未改写"必须机器可验；CONTEXT 的 `_Avoid_` 明确不接受只有页面级出处 | 只记行号（原文更新即失效、读者看不懂）；只记文件+标题（AC-K1-2 逐字一致无从验证）；两套都显示在页面（页面被坐标淹没） | AC-02/AC-04、OI-10 | 读者看到文件+标题但机器凭据在旁路文件，需 README 说明二者关系 | — |
| D-005 | 页头复用现有 `source` 字段（**单来源页**写该语料相对路径；**多来源合并页**写 `primary` 主来源路径，并在其后以 `; ` 分隔列出其余来源相对路径，全部相对同一语料根目录；完整清单以 `_audit/sources.jsonl` 与 `_audit/page-manifest.json` 为权威）；细粒度溯源只进 `_audit/sources.jsonl` | 用户 Q4b/Q26；核实发现 `source:` 已被 48 页占用且语义为 `SourceArchive/...` 相对路径 | 新增 `built_from`/`built_by_run`（下游须学新名字，且与 ADR 0013「仅允许一个新字段」的授权博弈）；用现有 `sources` 列表字段（该字段已有一个私有格式，语义不清） | AC-04、OI-12、CONTEXT 术语 | RISK-010（易被误读为语料在 SourceArchive） | — |
| D-006 | frontmatter 覆盖 15 字段；硬断言 `page_model=derived` 且 `generated_by=knowledge_digest_semantic_compiler.py` | 母任务 S1；用户 Q29；核实 555 篇正式页用这套 15 字段块；`page_model_for()` 规则使该名字判为 derived 而非 source | 不写 `generated_by`（一旦 frontmatter 被重写会判成 curated，溯源断裂）；`generated_by: digest`（与库里 31 个生成器的 `*.py` 命名习惯不一致） | AC-03、OI-11、页面身份 | 生成器名必须与实际脚本名一致，否则页头写假话（已写为验收项） | — |
| D-007 | 模型只用于起标题/写导读/辅助判主题；**禁止改写正文**；模型结果冻结成缓存，缓存键绑定来源内容指纹。**判主题的权限边界（detail-advice 澄清）**：页面划分由**确定性标题名归组（D-003/OI-05）单方决定**，模型对主题的判断只作为**建议**输出到"疑似同义主题"报告，模型输出**不得改变页面成员**；若用户依据建议决定合并某些主题，该决定以**机械方式**（显式主题映射）重新归组并重新计算，而不是让模型在运行时决定归组 | 用户 Q7（未选纯规则）/Q14/Q17；母任务把"LLM 改写诱惑"列为风险并以逐字保真压制；D-003 已把"让模型判主题"列为被拒方案，本条目据此澄清两者不冲突 | 全程不调 LLM（合并后标题生硬、跨文件去重无法自然组织）；连叙述型也允许改写（与 AC-K1-4 硬碰硬）；不缓存每次实时调（产物抖动，破坏可重复运行）；**让模型运行时决定页面成员（与可重复运行不可兼得，已拒）** | AC-02/AC-06、OI-07、OI-20 | RISK-003（导读引入无依据信息，已用"导读逐句可回溯"压制）；RISK-005（缓存误命中，已用指纹绑定 + 负例压制）；RISK-013（"建议 vs 决定"边界若实现模糊会破坏可重复性） | supersedes 本记录内早先含『模型可判主题』的表述（该表述来自 Talk R1 Q14 的原始答复，经 Q15 与 detail-advice D-F2/D-F16 澄清后收敛为本条） |
| D-008 | 部分成功 + 显式阻塞清单 | 用户 Q8；母任务"失败不伪装成功"不变量 | 全有或全无（一份有问题就全白干，容易永远交不出）；静默跳过（直接违反不变量） | AC-08、OI-15 | 阻塞清单可能很长，需按影响排序以便用户处置 | — |
| D-009 | 五类数据状态全部由程序从事实推导 | 用户 Q9；母任务 S3 词表；推导规则可复算，保住"可重复运行" | 程序初判 + 模型复核（同输入两次可能不同，且把"不算结论"的权限交给模型）；留人工标注（交不出可验收产物） | AC-05、OI-13 | 阈值边界情况可能与用户直觉不一致，需抽查（已写入验收） | — |
| D-010 | 参考块以整张表/整个列表/整段报错文案为一个逻辑单元；URL 与附件原样保留并标注 | 用户 Q13/Q5；拆到行会丢结构且验收复杂度上升；母任务 NG 明确不做多格式/附件处理 | 拆到行或单元格（丢表格结构、逐字保真验证复杂化）；删除图片行（违反 AC-K1-2 零丢失）；下载附件（需登录内网、且属超范围） | AC-01/AC-02、OI-09 | 块内单行有错时报告粒度偏粗（已由"块内定位到行"缓解） | — |
| D-011 | AC-K1-1 的基准 = 冻结本次生成的清单 + 独立第二方法交叉验证 | 用户 Q24；"自己生成的东西不能当自己的验收基准"；与母任务 S2 的冻结思路一致 | 只冻结首轮清单当回归基准（首轮拆漏则永远发现不了，只能证"稳定"不能证"没丢"）；不建清单只做反向核对（只能验"产物里原文有"，验不了"原文里产物有"） | AC-01、OI-04、OI-21 | 需实现两套方法，工作量增加（用户已知悉并选择） | — |
| D-012 | 一次运行处理全部 89 份，一次产出整个批次目录 | 用户 Q28；分 4 批会破坏"按主题合并"（跨批次同主题无法合并）；缓存机制使重跑代价可接受 | 分 4 批（批次边界破坏主题合并，且需额外合并轮）；先小批试跑再全量（小批划分与全量不同，小批产物不能当验收依据） | AC-06、OI-16、批次目录 | 单次耗时长；中途失败需整体重跑（缓存降低成本） | — |
| D-013 | 300 行分页与 claim 单 part 归位保留；分批与恢复**本卡不激活**；去重、失败语义、claim 级溯源保留 | 母任务 S6 保留不变量；用户 Q28 选择一次跑完，故分批在本卡无使用场景 | 在本卡实现分批与恢复（无故障证据支撑的长期能力，属计划外的能力扩张）；直接删除分批（母任务把它列为保留不变量，删除属 K4 范围） | AC-07、OI-14 | 分批不激活意味着大语料或长运行无法中断续跑（用户已知悉） | — |
| D-014 | 与 CompanyBrain 既有 1347 页完全不读、不合并、不比对 | 用户 Q22；写权边界（S7）；K1 只写批次目录 | 检测并标注重叠（需读正式库 + 名字匹配，多一套规则与失败路径）；直接合并既有页内容（把"替换/上库"语义提前引入 K1，属 K3 职责） | OI-17、NG-008 | RISK-011（K3 上库时的"唯一生产者"取代关系未决 → DEF-008） | — |
| D-015 | 文件名与目录名使用英文 slug；中文标题放 frontmatter `title`；slug 必须批内唯一 | 用户 Q25；gbrain 规则删空非 ASCII，实测 89 文件 → 37 唯一 slug、10 组碰撞覆盖 62 文件，import 按 slug 覆盖 | 保留中文名并输出碰撞清单（碰撞仍存在，上库即互相覆盖）；不管 slug（"路径能生成合法 slug"形同虚设，下游 62/89 页面注定丢失） | AC-03、OI-08、下游可消费性 | 英文名需生成或推导，多一道命名步骤；Obsidian 里文件名不直观（中文标题在页内） | — |
| D-016 | 先查清 16 个基线失败用例的性质并当基线写进计划；K1 以"失败清单不变"为回归口径 | 用户 Q27；基线 `16 failed, 892 passed, 3 skipped`（退出码 1）为既有事实 | 顺手修好 16 个（修的是 K4 要删的旧路径，可能白干且撑大 K1 范围）；不管（交付时无法区分"K1 弄坏的"与"本来就坏的"） | AC-10、OI-14、DEF-006 | 仓库交付时仍为红，需在计划中明确口径以避免误读 | — |
| D-017 | 批次目录结构 = `README.md` + `products/<产品>/<模块>/<页面>.md` + `_audit/{reference-blocks.jsonl,sources.jsonl,page-manifest.json,run-metrics.json,suspected-synonyms.md}` | 用户 Q30/Q19；参考块可能上千条，嵌入页面会淹没正文；页面清单 + 分类归属交 K2 | 只输出页面 + 审计文件（K2 需自行重建页面清单、读者无入口说明）；全部嵌页面（页面被溯源淹没，与 Q4b 决定相左） | AC-01/AC-04/AC-08、K2 交接 | "产品/模块"两层需从语料 4 个顶层目录 + 标题推导，存在误判空间 | — |
| D-018 | `digest` 命令换成新语义编译行为；旧行为降为 `scripts/` 下一次性的对照脚本（K4 删旧码时一并删除） | 用户 Q20b（明确担心"忘了合并命令、库里堆积垃圾"）；只保留一个门牌号 | 新增独立子命令（用户明确反对：多一个入口、将来忘合并）；自动识别两种输入（一个命令两种行为、靠输入形状猜意图，正是垃圾堆积来源）；直接删旧路径（失去与 release4 的对照能力，且删除属 K4） | AC-09、OI-14、命令面 | 旧 digest 的 518 个测试将大面积变红，需分类（OPEN-005）；即 K1 一定要付这笔测试整理成本 | supersedes 旧 `digest` 命令的既有行为（旧行为不再由该入口承载，降级为一次性对照脚本） |


## 审查处置

### direction-advice（step 6，2026-09-13）

**调用事实**：`wh-review` direction track，pair_id `ce86a01d-80a3-419f-9f80-4998850e9461`，
material_id `90734f7bd19dcdf06a2f301d64cd406a842f9e409fcdc29704d608867ad685ed`，
sink_ref `/Users/Hugh/.workflowhub/review-sink/e0089d3329ff0205974d9b2cc1266e31ad9f845c697ac89411f5f17ad128bc4d.json`。
公共结果 `available-with-failures`（**不是 pass**）：red 三角色全部 completed（kimi/coding、antigravity/flash、codex/luna）；
blue 的 kimi/coding 因 `RATE_LIMITED` 失败，antigravity/flash 与 codex/luna completed。
前两次调用返回 `unavailable`（`MATERIAL_FORBIDDEN`：`approved_direction`、`known_facts_constraints_non_goals`
不是 direction track 的允许材料键）；第三次按 `runtime/review/stage-materials.json` 的
`make-decision/direction` 允许键（`raw_requirement` / `objective_facts` / `convergence_outline`）重建材料后才取得真实建议。
`unavailable` 的两次没有 findings，不写成"没有问题"。

**材料边界遵守情况**：direction 为盲审，未交付拟定方案、OI 答案、`selected_disposition`、decision-log、spec 或实现 diff；
`convergence_outline` 为 questions-only 投影（全部 `status: open`，无 `answer`/`disposition`/`evidence` 字段）。

**finding 逐条处置**（同一实质问题被 red/blue 重复提出时合并为一条处置）：

| # | severity | finding 实质 | 处置 | 证据/落点 |
| --- | --- | --- | --- | --- |
| F-1 | **blocking** | AC-K1-3 把「gbrain 按 slug 可检索」列为硬失败判据，但 gbrain 会删空非 ASCII 字符，89 文件只得 37 个唯一 slug、10 组碰撞覆盖 62 个文件；不改 gbrain 规则则该判据必然无法通过 | **有效，已在本阶段修复**：用户已在 Round 2 Q25 决定文件名用英文 slug + 中文标题放 `title`；AC-K1-3 已改为「文件名与目录名为合法 gbrain slug 且**批内唯一**」，并显式声明母任务原文的"gbrain 实际检索"一项在本卡记为未验证（DEF-002） | AC-03、AC-K1-3 对照基线声明、OI-08、D-015、DEF-002 |
| F-2 | major | FR-K1-1/AC-K1-1 要求参考块清单与"冻结分层全量清单"100% 一致，但该清单不存在，且既有的 89 案例 oracle 无法充当块级基准，构成不可核验的依赖 | **有效，已在本阶段修复**：用户已在 Q24 选择「冻结本次清单 + 独立第二方法交叉验证」破自证循环；AC-01 已明确基准由本卡冻结、并由不依赖同一拆块器的独立第二方法逐块比对 | AC-01、OI-04、D-011 |
| F-3 | minor | S1 声明的 frontmatter 是 12 字段，而 CompanyBrain 真实正式块是 15 字段，硬编码校验会与真实页面不一致 | **有效，已在本阶段修复**：AC-03 已改为对齐真实 15 字段正式块（`title/type/page_model/scope/product/section/module/tier/trust/source_status/quality_status/created/updated/generated_by/tags`），OI-11 同步记录；事实依据为 555 篇正式页的字段普查 | AC-03、OI-11、`## 调研` 字段普查 |
| F-4 | major（red+blue 各提一次） | OI-04 把完成判据写成"读者可查证/下游可检索 **或** 仅内部一致性"的二选一，等于允许弱化原始需求已固定的验收标准 | **有效，已在 OI 层修复**：OI-04 的问题改为「如何让 AC-K1-1…K1-5 各自的判据在 K1 内可观察、可被测试打破」，不再提供弱化选项；"仅内部一致性"从未被用户选中，属问题措辞缺陷 | OI-04（问题已重写）、AC-01…AC-10 |
| F-5 | major（red+blue 各提一次） | OI-08 只泛问命名与 slug 检索，未把已知的 slug 碰撞与覆盖行为转化为必须解决的约束 | **有效，已在本阶段修复并强化**：OI-08 的问题与验收改为显式要求"在冻结的 gbrain 归一化规则下建立**无碰撞、稳定**的页面身份映射，碰撞或歧义检索即判失败，且不得依赖导入顺序或修改 gbrain 配置" | OI-08（问题与 acceptance 已重写）、AC-03、D-015 |
| F-6 | major（red+blue 各提一次） | OI-11 未把 `generated_by` 取值与外部 `page_model_for()` 推导规则、以及被既有流水线清理的风险绑定为同一硬约束 | **有效，已在本阶段修复并强化**：OI-11 的验收改为要求同时验证「15 字段齐备 + `page_model=derived` 断言 + `generated_by` 前缀安全（不以 `clean_`/`sync_` 开头）+ 输出路径不触及既有正式页」，任一失败即判失败 | OI-11（acceptance 已重写）、AC-03、NG-008、D-006 |
| F-7 | major（red+blue 各提一次） | 大纲把页面粒度与块形状分开问，但未要求建立"每个冻结来源参考块 → 输出锚点"的完整覆盖关系，可能选了主题策略却静默丢块 | **有效，本阶段新增 OI-21 补齐**：要求建立来源→输出的覆盖不变量（合并/拆分/重复/未映射各自的登记方式），并把"未映射或被覆盖的块"定义为交付失败 | **新增 OI-21**（`success_failure_boundary`）、AC-01 与 AC-08 联动 |
| F-8 | major | 19 个 OI 无任何一条覆盖硬约束「一次运行约 150 次 provider 调用是可接受量级；失败运行的耗时/调用数/token 必须真实非 null」 | **有效，本阶段新增 OI-20 补齐**：要求明确调用预算的分配（哪些环节必须机械化、哪些才允许调模型）与失败运行的成本记账方式 | **新增 OI-20**（`success_failure_boundary` → 归入固定类别 `success_failure_boundary`）、AC-08 联动 |
| F-9 | minor | AC-K1-1 的验收需要一个可验证的整体身份锚点，而 task4 `manifest_hash` 与 task5 `snapshot_id` 不可复算 | **部分有效，登记为已知缺陷而非新增方向轴**：逐文件 sha256 已核实 89/89 一致，可作为身份锚点；两个聚合字段不可复算的事实登记为 RISK-008 与 DEF-007，不阻塞本卡 | RISK-008、DEF-007、AC-01 |

**处置结果**：F-1…F-7 在本阶段修复（其中 F-4/F-5/F-6 属问题措辞与验收强度缺陷，已重写问句与 acceptance；
F-7/F-8 新增两条 OI）；F-9 登记为已知缺陷。**无 finding 被静默丢弃**。
修复改变了 OI 集合与措辞，因此 `outline_version` 由 v2 升为 **v3**；按合同"没有真实主题变化不重复 review"，
本次不因升版再发起新的 direction review（已有真实建议，且修复内容均由该建议直接驱动）。

### detail-advice（step 10，2026-09-13）

**调用事实**：`wh-review` detail track，公共结果 **`available-with-failures`（不是 pass）**，共 **26 条 finding**
（red：pi/v4flash、antigravity/flash；blue：antigravity/flash、codex/luna）。材料按 `stage-materials.json` 的
`make-decision/detail` 允许键提交：`raw_requirement`、`approved_direction`（当前 decision-log 全文字节）、
`draft_spec_or_acceptance`（验收标准 + 范围的连续切片）。**首次调用因提交 `oi_terminal_records` 返回 `MATERIAL_FORBIDDEN`**
（该键不在该 track 的允许清单，OI 终态已含于 `approved_direction` 全文）；自行诊断后重建材料才取得真实建议。
`unavailable` 的那次没有 findings，不写成"没有问题"。

**26 条 finding 去重后为 16 个实质问题，逐条处置**：

| # | severity | finding 实质 | 处置 |
| --- | --- | --- | --- |
| D-F1 | **blocking**（antigravity red+blue、pi red） | D-018 把 `digest` 换成新行为会让旧 518 个测试变红，与 AC-10「新增失败即失败」直接死锁；且改旧命令超出 K1「不删代码（K4）」的边界 | **有效，已在 AC 层修复，D-018 保留**：用户已在 Q20b 明确选择换门牌号（并明确反对新增命令），方向不改；AC-10 补齐与 D-018 的对账口径——回归基准按 OPEN-005 分类清单定义，**与 `digest` 入口绑定的测试随路径改挂脚本或标废弃、不计入"新增失败"**，**不与该入口绑定的测试（含 16 个既有失败）必须节点 ID 与原因逐一不变**；基准从"计数"改为"精确节点 ID 清单 + 测试清单"。新增 OPEN-010 跟踪冻结形态 |
| D-F2 | major（codex blue、antigravity blue、pi red） | 主题归组权限自相矛盾：D-003/OI-05 要求确定性标题归组且明确拒绝"让模型判主题"，而 D-007/OI-07 仍写"判主题" | **有效，已在条款层修复**：D-007 增加权限边界——页面成员由确定性标题名归组**单方决定**，模型对主题的判断只作**建议**输出到疑似同义主题报告，**不得改变页面成员**；用户若要合并须走显式主题映射的机械重算。已选方向的"模型边界"条目同步改写；新增 RISK-013 与 OPEN-008 跟踪契约 |
| D-F3 | major（pi red、codex blue） | 新增 OI-20/OI-21 的验收没有落进 AC（AC↔OI 映射声称覆盖但表内无条款） | **有效，已修复**：新增 **AC-12**（成本与失败记账）与 **AC-13**（来源→输出覆盖不变量）；AC-08 扩为"阻塞显式化与批次状态可机读"；AC↔OI 映射同步更新 |
| D-F4 | blocking（antigravity blue、pi red、codex blue） | 提交的 `draft_spec_or_acceptance` 材料首行截断、缺少声明的小节、且与 `approved_direction` 内容重复 | **有效，已在材料层修复**：该问题由主会话按小节下标切割材料造成（首行带残留反引号且与全文重复），**不是决策内容缺陷**；材料已重建为「验收标准 + 批次目录契约 + 阶段末摘要」的完整连续切片。如实登记，不掩盖 |
| D-F5 | major（codex blue、pi red） | AC-06「逐字节一致」与 `created`/`updated`、批次目录名、README、运行成本记录冲突：这些内容随运行变化则两次运行不可能逐字节一致 | **有效，已修复**：AC-06 增加**比对范围**（`products/**` 与 `_audit/**`，其中 `run-metrics.json` 的计时数据不参与）与**确定性要求**（`created`/`updated` 取来源确定性事实而非运行时刻；README 与疑似同义主题报告用确定性模板、不写批次名/时刻/调用数；批次目录名不参与比对）。新增 OPEN-011 跟踪时间戳取值来源 |
| D-F6 | major（antigravity red+blue、pi red） | AC-04 的 oracle 只在旁路文件上扫描，交付页面正文的 claim 可以漂移而不被发现；读者侧出处呈现缺判据 | **有效，已修复**：新增 **AC-11**，要求 oracle **扫描页面正文的实际 claim** 并与 `_audit/sources.jsonl` 交叉核对（零无锚点 claim），同时覆盖"页面显示文件+标题且不显示行号""页头 `source` 可解析"两条读者侧判据 |
| D-F7 | major（antigravity blue） | AC-03 的 15 字段清单漏了 D-005 选定的 `source`，校验脚本可能因"多余字段"失败或使 `source` 脱离校验 | **有效，已修复**：AC-03 明确为「15 字段正式块 **+ 1 个复用的 `source` 字段（共 16 个受校验字段）**」，并说明 `source` 的校验内容（可解析到本次语料文件 + 标注语料根目录） |
| D-F8 | major（antigravity red） | 复用 `compiler.py:2940-2991` 与 D-010「整张表为一块」冲突——该实现把表格拆成单行 | **有效，已修复**：OI-03 与 `## 调研` 均标注该实现**不可原样复用**，必须追加"连续表格行聚合为单块"的步骤；D-010 的整块决定不变 |
| D-F9 | major（codex blue） | 交给 K3 的交接状态不可机读：产物无批次状态/完成标记/阻塞产物，K3 可能把中断批次当可发布 | **有效，已修复**：AC-08 要求 `_audit/page-manifest.json` 带机读批次状态（`not_released`/`complete`/`blocked` + `attempt_id` + 来源快照身份 + 阻塞项全集）并加"故意中断"负例；D-017 目录结构补入 `run-metrics.json` |
| D-F10 | major（codex blue） | 英文 slug 算法与碰撞后缀策略未冻结（OPEN-003），而 D-015 已要求无碰撞 | **部分有效**：方向已定（英文 slug、批内唯一、不依赖导入顺序），**具体算法属实现层**；OPEN-003 的关闭条件补记"必须含碰撞后缀策略与 import-order 无关性测试"。不上升为方向问题 |
| D-F11 | major（codex blue、antigravity red） | RISK-004 的缓解手段（疑似同义主题报告）没有交付载体，也没有 AC | **有效，已修复**：D-017 与"已选方向·批次目录内容"补入 `_audit/suspected-synonyms.md`，并规定由确定性模板生成；OPEN-004 的关闭条件绑定该载体 |
| D-F12 | minor（pi red） | OI-17 的数字算术不成立：555 + 121 = 676 > 589 | **有效，已修复**：OI-17 与 `## 调研` 改为"带 frontmatter 的 589 页中 555 页用正式 15 字段块（基准），另有 121 页用另一套方言，**两集合有重叠（676−589=87）不可相加**"，并明确 AC-03 以 555 页为基准 |
| D-F13 | minor（antigravity blue） | OI-14/OI-17 的 `category` 填了框架节点值（`extension`/`background`），两张索引表只汇总 18 条 OI | **有效，已修复**：OI-14 的 category 改为 `deferred`、OI-17 改为 `complete_user_flow`；Fixed categories 表补入 OI-14/OI-17（覆盖 21 条）；Framework nodes 表中 OI-14 同时属 N-extension，已在该行显式说明交叉关系 |
| D-F14 | major（codex blue、pi red） | `资料未明确` 与 `audit_only` 无法从已声明输入推导（缺"待验证事实全集"与审计素材的检测规则） | **有效，登记为真实缺口**：新增 **RISK-014** 与 **OPEN-009**，交 build-spec 定义状态记录 schema 与可观察输入。本卡**不假装**这两类状态已可推导 |
| D-F15 | major（codex blue） | AC-10 只有聚合计数（16 failed）而无精确失败指纹，计数不变但用例变化会被掩盖 | **有效，已修复**：AC-10 改为以**精确节点 ID 清单 + 测试清单**冻结基准，明确"计数不变但用例集合变化同样判失败" |
| D-F16 | minor（pi red、codex blue） | 模型权限表述在多处不一致（"判主题"残留） | **有效，已修复**：与 D-F2 同批处理——"已选方向·模型边界"与 D-007 均统一为"起标题 + 写导读"，主题判断只作建议 |

**处置结果**：D-F1…D-F16 全部处置。其中 14 条在本阶段修复（新增 AC-11/AC-12/AC-13，扩写 AC-03/AC-04/AC-06/AC-08/AC-10，
补入批次目录两件产物，修正数字与 OI 分类，澄清模型权限边界）；2 条（D-F10 的具体算法、D-F14 的状态推导输入）
登记为延期/未决并给出 owner 与关闭条件，**不假装已完成**。**无 finding 被静默丢弃**。
detail-advice 与 direction-advice 都是质量事实而非推进许可；本阶段据此修复后进入用户确认（step 11）。



## 非目标

- NG-001 不依赖 build-spec 补齐需求；需求收敛在本阶段完成。
- NG-002 主会话不做重读量取证；取证派子代理，主会话只收结论与证据引用（上下文守恒）。
- NG-003 不做入口页与分类导航，不做「从入口可达每一页」的检查（K2 范围）。
- NG-004 不做 staging 校验 → 原子切换 → last-known-good → 回滚，不做四类负例注入（K3 范围）；
  本卡因此**不具备**写入中断后不留半成品的保证，该限制必须显式报告。
- NG-005 不做源码瘦身与删码，不做「源码行数净下降 / 不可达模块归零 / 零引用配置下降」度量（K4 范围）。
- NG-006 不做真实查询集对照验收（冻结快照 + 逐题判定 + 汇总通过条件），不做逐题四结果判定（K3 范围）。
- NG-007 不引入向量库、图数据库、服务化部署；不做前端或可浏览界面；不做多格式输入（PDF/Word/网页）。
- NG-008 不修改既有 CompanyBrain 正式页（不读、不合并、不比对），不修改停摆的自动化流水线，
  不修改 gbrain 的配置与索引状态，不下载语料中的图片与附件。

## 风险与延期交接

| risk/deferred_id | 风险或延期内容 | 触发/后果 | 处理阶段/owner |
| --- | --- | --- | --- |
| RISK-001 | ~~冻结清单可能与磁盘不一致~~ **已降级**：核实证明 89/89 sha256 一致、0 差异、task5 的 byte_count/line_count/expected_status 也 0 差异 | 原风险不成立；保留登记以说明用户 Q6 的选择已被事实兜底 | 已关闭（事实核实） |
| RISK-002 | K1 没有原子发布能力（NG-004）：写入中断可能留下半成品 | 批次目录里出现混合版本，读者无法分辨 | 本卡显式报告（AC-08）；K3 发布通道负责根除 |
| RISK-003 | 模型写导读可能引入原文没有的信息，形成「无出处结论」 | 违反 AC-04 零容忍 | 本卡以「导读逐句必须有原文依据」压制（AC-04）；无法满足则该页导读留空并显式标注 |
| RISK-004 | 按标题名做确定性合并，跨文件同义不同名（如「激活&停用」vs「Terminal 激活」）合并不彻底 | 页面划分偏离读者直觉，出现近似重复页 | 本卡接受；输出「疑似同义主题」报告供人工判断，不自动合并 |
| RISK-005 | 模型结果缓存误命中（输入实际变化但缓存键未变）会产出陈旧内容 | 产物与原文不一致且难以发现 | 缓存键必须绑定来源内容指纹；以负例验证（改一个字节必须导致缓存失效，AC-06） |
| RISK-006 | 产物落在 `/Users/Hugh/Downloads/KD测试`，可能被系统清理或用户误删 | 批次产物丢失、验收证据失效 | 用户已知悉该目录为临时对照产物；正式留存由 K3 发布通道负责 |
| RISK-007 | 批次目录不在 gbrain 索引范围内（Q18），AC-K1-3 的「gbrain 按 slug 可检索」在本卡内只能记为未验证 | 该项验收结论缺失 | 延期项 DEF-002 |
| RISK-008 | **聚合哈希不可复算**：task4 `manifest_hash`（声明 `e1842f68…`）与 task5 `source_snapshot.snapshot_id`（声明 `…fc6cbe66…`）在 70/30 种算法变体下均无法从冻结文件复算 | 这两个字段不能作为可验证的完整性凭证；若下游依赖它们做校验会误判 | 本卡登记为事实缺陷；不改动这两个冻结文件（它们不属于本卡产物） |
| RISK-009 | **基线测试为红**：`c5fb2b5` 上 `16 failed, 892 passed, 3 skipped`，失败全在 `test_task2a_reader_bundle.py` | 无法用「全绿」判断 K1 是否引入回归；且交付时仓库仍为红 | 本卡以「失败清单与原因不变」为口径（AC-10）；是否修这 16 个由用户在 plan 阶段决定触发条件 |
| RISK-010 | 现有 `source:` 语义为 `SourceArchive/...` 相对路径，K1 沿用它承载语料相对路径并标注根目录 | 读者可能误以为语料也在 SourceArchive 内 | 页头与 README 显式标注根目录；K3 上库时需决定是否先归档语料 |
| RISK-011 | **K1 产物与既有页面同主题**：语料覆盖 GoInsight/EMM/merchant system 等，而 CompanyBrain 已有这些产品的正式页（GoInsight 151 个无 frontmatter 页、EMM 65 个、MAXSTORE 64 个）；K1 选择完全不比对既有页 | K3 上库时同一主题路径出现"既有人工/`synthesize_*` 页"与"KD 新页"两个候选，违反 CONTEXT 的「唯一生产者」不变量 | 本卡登记；K3 必须在发布前决定取代关系（DEF-008） |
| RISK-013 | D-007 澄清后的"模型建议 vs 机械决定"边界若在实现中模糊，可能让模型输出间接改变页面成员 | 破坏 AC-06 的可重复运行 | 本卡以"主题归组机械化 + 模型输出仅进建议报告 + 页面成员变更须走显式主题映射"压制；OPEN-008 跟踪其具体契约 |
| RISK-014 | `资料未明确` 与 `audit_only` 两类状态缺少"待验证事实全集"的声明式定义 | AC-05 的 fixture 无法完整构造，两类状态可能退化为实现者的主观判断 | OPEN-009 明确记录该缺口，交 build-spec 定义状态记录 schema 与可观察输入；本卡不假装它已可推导 |
| RISK-012 | **ADR 0013 的溯源字段授权悬空**：ADR 授权"且仅允许引入一个新的页面级溯源字段"，本任务选择零新字段 + 旁路文件 | K3 可能误以为该授权已被消费，或旁路文件因不在层内而不随页面迁移，导致逐条出处在层内不可读 | 以 Grill G-001 记录：本任务不使用该授权；K3 需重新决定「启用该字段」或「把旁路文件纳入层管理」 |
| DEF-001 | 语料 89 份 sha256 重核 | 母任务 S2 的硬前提 | owner=用户；触发=需要对外声明验收结论有效时；**当前已核实一致，故非阻塞** |
| DEF-002 | gbrain 实际索引与按 slug 检索验证 | 下游可消费性的最终证明 | owner=后续任务/用户；触发=产物进入正式知识库目录后 |
| DEF-003 | 原子发布、回滚、last-known-good 与失败成本计数 | K1 产物进入正式知识库的前置 | owner=K3（后续任务） |
| DEF-004 | 真实查询集对照验收（三份冻结物 + 逐题四结果判定） | 最终及格线 | owner=K3（后续任务） |
| DEF-005 | 停摆自动化流水线接管登记与旧 `synthesize_*` 主题移交 | 既有流水线恢复时可能改名/删除 `Products/` 下页面 | owner=用户（流水线修复任务） |
| DEF-006 | 16 个基线失败用例的根因定位与处置决定 | 决定它们是"随旧路径一并删除"还是"需要修复" | owner=K1 的 build-plan 阶段（本卡先取证，不修） |
| DEF-007 | task4 `manifest_hash` / task5 `snapshot_id` 的生成算法缺失 | 两个冻结字段目前不可复算 | owner=用户；触发=需要把这两个字段当作完整性凭证时 |
| DEF-008 | K1 产物与 CompanyBrain 既有同主题页的取代关系，以及旁路溯源文件如何随页面上库 | 违反「唯一生产者」不变量的直接来源 | owner=K3；触发=发布通道把 K1 产物写入语义层时 |

## 阶段末摘要（六项，交下游 build-spec）

1. **本阶段做了什么**：经两轮 Talk（34 项用户真实答复）、两次子代理只读取证、一次 direction-advice 独立盲审（9 条 finding 全部处置）
   与一次 Grill（与 ADR/CONTEXT 压力测试），把 K1 的方向、边界、数据状态与验收口径收敛为 21 条已确认 OI 与 18 条决定条目。
2. **覆盖到什么程度**：母任务 K1 的 5 条 FR/AC 全部落到可执行判据（AC-01…AC-13，见 `## 验收标准` 的 AC↔OI 对应）；
   六类边界（完整用户流程/页面范围/数据状态/成功失败边界/非目标/延期）全部有用户答复或事实依据，无 `empty` 占位。
3. **与上游产物是否一致**：与母任务 PRD 的 S1/S3/S4/S6/S7 一致；与 ADR 0013 一致但存在一处**授权悬空**（G-001）；
   与 CONTEXT 术语一致（批次目录不称为语义层；页头 `source` 只作读者导航，不构成证据零容忍的满足物）。
4. **本阶段当场修复了什么**：direction-advice 的 F-1…F-8 全部在本阶段修复（含重写 OI-04/OI-08/OI-11 的问句与验收、新增 OI-20/OI-21）；
   两次 `MATERIAL_FORBIDDEN` 的材料错误经自行诊断后按 `stage-materials.json` 的允许键重建材料，第三次才取得真实建议。
5. **剩余风险与未决**：RISK-002…RISK-014、DEF-001…DEF-008、OPEN-001…OPEN-011；
   其中本卡内**无法消除**的是无原子发布能力（RISK-002）与 gbrain 实际检索未验证（RISK-007）。
6. **下游可直接消费什么、不能猜什么**：build-spec 可直接消费 21 条已确认 OI 与 18 条决定条目（D-001…D-018）；
   **不得**重新决定产品方向；**不得**把 DEF-001…DEF-008 当作已完成；**不得**把 `available-with-failures` 的 direction-advice 写成 pass。

## 未决项

| id | 未决内容 | owner | 触发条件 | 关闭条件 |
| --- | --- | --- | --- | --- |
| OPEN-001 | 16 个基线失败用例的性质（本来就坏 vs 被近期改动弄坏）与最终处置 | K1 build-plan | 进入 build-plan 写测试策略时 | 给出根因结论并决定"随旧路径删除"或"列入修复" |
| OPEN-002 | 缓存的持久化位置、生命周期与键构成（来源内容指纹 + 模型标识 + 提示模板版本 + 主题映射版本） | K1 build-plan | 设计缓存实现时 | 四项键全部定义；缺缓存时重新调用并写回；负例验证通过（改一字节必失效）且同输入两次运行字节一致 |
| OPEN-003 | 英文 slug 的生成方式与碰撞后缀策略（从标题翻译、从来源目录名推导，还是模型生成后冻结） | K1 build-plan | 设计页面命名时 | 批内 slug 唯一性断言通过；含碰撞后缀策略；有「与导入顺序无关」的测试；中文全文检索能力不被破坏 |
| OPEN-004 | 「疑似同义主题」报告的形态与人工处置流程 | K1 build-plan | 主题归组实现完成后 | 报告落于 `_audit/suspected-synonyms.md` 且由确定性模板生成；有人工处置路径（显式主题映射），且模型建议不改变页面成员（RISK-004/RISK-013 的缓解手段） |
| OPEN-005 | 旧 `digest` 行为降级为脚本后，其 518 个既有测试中哪些仍适用、哪些随路径废弃 | K1 build-code | 切换 `digest` 行为时 | 测试分类清单产出，且 AC-10 的失败清单保持 |
| OPEN-006 | KD 溯源语义登记进 `CONTEXT.md`（母任务安排：字面名由 K1 的 build-spec 冻结并登记进 `CONTEXT.md` 与既有元数据脚本） | K1 build-spec | 写 spec 冻结溯源契约时 | `CONTEXT.md` 出现 KD 溯源术语条目，且与页头/旁路文件的真实字段一致 |
| OPEN-008 | 主题归组的机械契约：标题名归一化规则、显式主题映射的存储形态、模型建议如何进入/不进入页面成员 | K1 build-spec | 写 spec 冻结主题归组规则时 | 同一输入两次运行的页面成员完全一致，且模型建议可追溯但不改变成员 |
| OPEN-009 | `资料未明确` 与 `audit_only` 的可观察推导输入与状态记录 schema（含"待验证事实全集"如何声明） | K1 build-spec | 写 spec 冻结五类状态契约时 | 五类 fixture 可构造且逐类可核对；两类状态不再依赖实现者主观判断 |
| OPEN-010 | AC-10 回归基准的精确冻结形态：失败用例节点 ID 清单 + 测试清单 + OPEN-005 分类清单 | K1 build-plan | 切换 `digest` 行为前 | 基准清单冻结，且 AC-10 可在切换后机械判定 |
| OPEN-011 | `created`/`updated` 的确定性取值来源（来源内容指纹派生的固定基线 vs 来源 mtime 归一化） | K1 build-spec | 冻结 frontmatter 契约时 | AC-06 的字节一致比对通过，且时间戳对读者仍有意义 |
| OPEN-012 | claim 级溯源的可机械连接 schema：claim 切分规则、稳定 `claim_id`、页面正文片段 hash、正文↔旁路记录的一对一覆盖关系 | K1 build-spec | 冻结溯源契约时 | 可机械判定「零无锚点 claim」；正则可解析；AC-04/AC-11 的 oracle 可执行 |
| OPEN-007 | 是否修订 ADR 0013 以反映"本任务不使用新增溯源字段授权、改为复用 `source` + 旁路文件" | 用户（approve-decision 时决定） | 用户确认决策时 | 决定结果写入 `## 最终确认`；若修订则产出新 ADR 或修订记录 |

## 最终确认

- **状态**：`approved`（用户真实确认，2026-09-13）
- **确认方式**：宿主结构化问答工具（`ask_user_question`），按主题分组展示选项、直接后果与主要风险。
  第一轮用户选择"先展开细节给我看"；主会话据此展开验收标准（AC-01…AC-13，含 AC-06 的比对范围定义）、
  14 条风险、8 条延期项与 8 条非目标后，第二轮用户选择确认。
- **用户原文**（逐字）："确认，进入 stage-end 与发布（推荐）"
- **确认覆盖范围**：本决策记录全部方向、边界、验收、非目标、延期与风险；无保留、无部分确认。
- **同步确认的三项**：
  1. ADR 0013 的溯源字段授权处置 = **不改 ADR，只在本记录内声明"本任务不使用该授权"**，并标记 K3 上库时重新决定（G-001 / RISK-012 / DEF-008）。
  2. 16 个基线失败用例的根因调查时机 = **在 build-plan 阶段先查清**（DEF-006 / OPEN-001），不在本阶段展开。
  3. 验收力度 = **保持全部 13 条 AC，不放宽**（含 AC-01 的独立第二方法、AC-06 的字节一致、AC-13 的覆盖不变量）。
- **未确认/保留内容**：无。21 条 OI 状态全部为 `confirmed`，无方向层遗留项。
- **确认前置的质量事实**：direction-advice（9 条 finding）与 detail-advice（26 条 finding）均已真实执行，
  结果均为 `available-with-failures`，**均非 pass**，且 findings 已全部处置（见 `## 审查处置`）。用户确认时已知悉该性质。

### 阶段发布时的结构校验（官方 `run --action=execute` 真实反馈）

首次调用官方发布入口时 `quality_status=incomplete` 并列出 `missing_items`。这些不是 review finding，
而是**官方校验器对我这份决策材料真实结构缺陷的反馈**，逐条诊断并修复：

| # | 校验器报出的缺口 | 真实根因（自行诊断） | 修复 |
| --- | --- | --- | --- |
| P-1 | `outline reference OI-03/OI-04/OI-07/OI-14/OI-15/OI-20 has no OI record` | 这 6 条 OI 的 YAML 记录**解析失败**：其正文含成对的内层直引号（如 ASCII 双引号包裹的短语），被包在双引号标量内导致 YAML 语法错误；校验器解析失败即跳过，记录等同于不存在 | 全部 21 条 OI 记录改为 **YAML 字面块标量**（竖线加缩进指示符，两空格缩进），引号与换行不再破坏语法；已用 YAML 解析器逐条验证 21/21 可解析 |
| P-2 | `OI OI-01/02/05/06/08/09/10/11/12/13/18/19 visible_group_id or batch_id is required` | `approve-decision` 要求按主题分组展示并记录分组绑定，我的 OI 记录只有 `requires_user_decision: true` 而无分组标识 | 为全部 21 条补 `visible_group_id`，值取**本会话真实展示给用户的分组名**（R1-G1…R1-G11、R2-G1，或"未向用户提问，来源=…"的事实核实类） |
| P-3 | `OI OI-10 confirmed selected_disposition is missing` | 校验器 `substantiveConvergenceText` 把含 `unknown`/`未知`/`缺失`/`待定` 的文本判为**占位符**；而 OI-10 答复正文出现了数据状态名 `unknown`，被误判为占位 | 改写为领域词表里的显式标注态「原文未明确」（母任务 S3 用词），语义不变、消除关键词碰撞；已扫描 21 条确认无其他同类碰撞 |
| P-4 | `stage-end-spec-analyze:unavailable`、`current review result is unavailable for finding disposition` | 这两项**不是材料缺陷**：前者需外部宿主生成 stage outcome（本会话无外部宿主，按合同记 `unavailable`）；后者需把 review 结果写入 task store 的 canonical 记录 | P-1…P-3 修复后 `outline_closed` 通过；P-4 的两项按真实状态保留，**不伪造** |

**修复后真实结果**：`outline_closed` 通过；`missing_items` 仅剩 `current review result is unavailable for finding disposition`；
`stage_outcome_status = unavailable`（`reason: stage_outcome_missing`）。`quality_warnings` 含
`stage-end-spec-analyze:unavailable`、`goal_achievement:missing`、`acceptance_clarity:missing`、
`solution_convergence:missing`、`human_confirmation:missing`——**如实保留，不写成通过**。

**同一根因的第四处暴露（step 14 / stage-reflection）**：`stage-reflection.v2` 要求 judgment 引用**恰好一个**
外部宿主生成的 stage outcome 原件（`quality/evidence/stage-outcomes/make-decision/<sha256>.json`）。
本会话无外部宿主 ⇒ 无该原件 ⇒ 官方 runner 按合同拒绝并记 `unavailable`（`executor_absent`），
**不是材料缺陷，也不能靠改材料解决**。至此可以把本阶段的 `unavailable` 收敛为一个根因：

> **task7 的整个生命周期（含 step 12 `stage-end-spec-analyze`、step 14 `stage-reflection`、stage handoff）
> 都缺少"外部 Stage Agent 宿主"这一环。** 对照事实：同项目的 task6 有 3 份 `stage-outcomes/make-decision/*.json`，
> 因为它当时由外部宿主接入执行；task7 由本会话直接执行，无宿主桥接。
> 合同对此的处置是明确的：*"没有外部宿主 outcome 时，正式 run 不因缺少宿主而拒绝当前工作，
> monitoring 必须保留 `unavailable` 执行事实"*。

因此本阶段最终读数为 **11/12 质量谓词 satisfied**，未满足的 1 项与 2 条 `unavailable` 事实共享同一根因，
且**均不阻塞交接**（`work_status=ready`、`continuation_allowed=true`）。

**自省**：P-1 与 P-3 都属于"材料看起来写全了、但机器读不到"的类型（前者 YAML 语法，后者校验器关键词）。
这印证了"产物存在不能替代完成判据"：若不调用官方发布入口，我会一直以为 21 条 OI 都已生效。

## 第二轮 detail 复核的 finding 处置（2026-09-13）

按"材料实际变化才重跑受影响检查"的规则，在修复 P-1…P-4 与 D-F1…D-F16 后，用官方
`review --action=record` 对**当前材料**重跑了一次 detail track（canonical 记录：attempt
`fc161583-…`/`b25d2d1a-…`（首次，材料含截断缺陷）与 `20171ef6-…`/`4319be0a-…`（修复后重跑））。
26+19+17 条 finding 去重后，除已处置项外新增以下**真实缺陷**，逐条修复：

| # | severity | finding 实质 | 处置 |
| --- | --- | --- | --- |
| G-1 | blocking/major | AC-08 把 `not_released` 与 `blocked` 并列为"失败或未完成"，而母任务规定 K1 **正常完成的末态正是 `not_released`**——同一取值同时承载成功末态与失败态 | 拆分两个正交字段：`publish_status`（`not_released`=成功末态 / `released` 留给 K3）与 `run_status`（`complete`/`blocked`/`interrupted`），并明确 K3 据此区分"完整待发布"与"半成品" |
| G-2 | major/minor | AC-12 把"任一成本计数为 0"判为失败，但**真实 0 是合法值**（缓存命中重跑、J1/J2 早期失败尚未调模型） | 明确真实 0 合法，须原样记录并附 `reason`（`cache_hit`/`no_provider_call_yet`/`provider_unavailable`）；只有无法归因的 0、null 或与 `reason` 矛盾的计数才判失败 |
| G-3 | major | AC-12 的"同阶"不可证伪：计划数由同一次运行自行打印，实现可把计划设成实际值 | 加可复算上界：**计划调用数 ≤ 合并后主题数 × 2 + 20**，实际 ≤ 计划 × 1.5 |
| G-4 | major | 用户旅程 J2 写"表格行各自成块"，与 D-010/OI-09/AC-01 的"整张表为一块"直接冲突，实现者按 J2 做就会违反验收 | J2 改为"标题、列表项、代码块各自成块；**连续表格行必须聚合为整张表一块**" |
| G-5 | blocking/major | 五类数据状态混用了**来源级**（ready/known_empty/duplicate_alias/audit_only）与 **claim 级**（资料未明确）语义，且缺"待验证事实全集"与事实分母定义，无法确定性实现 | AC-05 明确两个层级各自的判定规则；`资料未明确` 归 claim 级；事实分母 = 待验证事实全集中**有原文依据**的 claim 数。OPEN-009 继续跟踪"待验证事实全集"的声明式定义 |
| G-6 | major | 多来源合并页无法用标量 `source` 字段表达（D-003 与 D-005 冲突） | 明确 `source` 的形态：单来源页写该语料路径；多来源合并页写主来源，其后以 `; ` 分隔列出其余来源，全部相对同一语料根目录；完整清单以 `_audit/` 两文件为权威 |
| G-7 | blocking/major | （**材料层缺陷**）提交给 detail track 的 `draft_spec_or_acceptance` 首行是从固定小节名清单中部截断的残片，且因主会话切片越界而整段重复了决策记录全文 | **根因**：`## 阶段末摘要` 在文件中的位置早于 `## 风险与延期交接`，导致按"下一个同级标题"切片时越界到文末，并把整份决策记录重复带入。**修复**：改用受标题边界约束的提取，重新生成 115 行的完整连续材料（5 个小节、13 条 AC、14 条 RISK、8 条 DEF，无截断、无重复、不含 OI/Talk/Grill/D 条目）。这是主会话的材料构造错误，如实登记 |
| G-8 | major | 页面身份未冻结：OPEN-003（slug 生成与碰撞后缀）与 OPEN-008（标题归一化与显式主题映射）仍延期，AC 只要求"最终唯一"而未规定映射函数，不同实现可产出不同页面集合与路径 | **部分有效，维持延期但收紧关闭条件**：方向已定（英文 slug、批内唯一、不依赖导入顺序、标题名确定性归组）；OPEN-003/OPEN-008 的关闭条件已含"唯一性断言 + import-order 无关测试"。**本阶段不再上升为方向问题**——具体映射函数属 build-spec/plan 的实现冻结范围，且 K1 不消费既有 CompanyBrain 页面，不存在跨实现的兼容约束 |
| G-9 | major | claim 级溯源缺可机械连接的 schema：AC-04/AC-11 要求交叉核对，但未定义 claim 切分规则、稳定 ID、正文到旁路记录的链接方式，且原文 `source_uri` 与验收 `source_path` 用词不统一 | **有效，本阶段修复用词并交 build-spec 冻结 schema**：AC-04/AC-11 统一用 `source_path`；新增 **OPEN-012** 跟踪 claim 切分规则、`claim_id` 稳定标识、正文片段 hash 与一对一覆盖关系的 schema，关闭条件=可机械判定"零无锚点 claim" |
| G-10 | minor | AC-10 冻结"16 个既有失败的节点 ID 与原因不变"，与 OPEN-001/DEF-006"交由 build-plan 决定修复或废弃"冲突——将来若修复这些失败反而会被 AC-10 判为回归 | **有效，已修复**：AC-10 补充"若 build-plan 决定修复某既有失败，则以该决定为基线变更记录（含原因与节点 ID），变更后的清单同样适用精确比对"，使"修复"成为受控的基线变更而非回归 |
| G-11 | major | 缓存未定义持久化位置、生命周期、模型/提示版本键，缺缓存时行为未定（OPEN-002 未关闭），两次新建批次运行可能重新调用模型而破坏 AC-06 | **有效，AC-06 收紧**：缓存必须持久化在**任务级固定位置**（不随批次目录销毁），键 = 来源内容指纹 + 模型标识 + 提示模板版本 + 主题映射版本；**缺缓存时必须重新调用并把结果写回缓存**，不得静默产出不同内容。OPEN-002 的关闭条件同步补齐这四项 |

**处置结果**：G-1…G-11 全部处置，其中 9 条在本阶段修复（含 AC-05/AC-06/AC-08/AC-10/AC-12 与 J2 的实质修正、
`source` 多来源形态、材料重构），2 条（G-8 的映射函数、G-9 的 claim schema）登记为 OPEN-008/OPEN-009/OPEN-012
并在 build-spec 关闭。**无 finding 被静默丢弃**。

**质量事实**：本阶段累计调用 wh-review **5 次**（direction 1 次成功 + 2 次材料错误；detail 2 次成功记录 + 1 次材料错误），
其中真实语义结果均为 `available-with-failures`，**无一次是 pass**。合并去重后共处置
**9（direction）+ 16（detail 第一轮）+ 11（detail 第二轮新增）= 36 个实质问题**。

## 拒绝方案

| 选项 | 拒绝理由 | 关联 D |
| --- | --- | --- |
| 一份来源一页（不做主题合并） | 产物会退化为"文档仓库"；89 份语料跨目录讲同一件事时会重复 | D-003 |
| 按内容集中度灵活决定拆不拆页 | "集中度"不可机器判定，会把页面粒度交给模型或人，破坏可重复运行 | D-003 |
| 让模型在运行时决定主题归组 | 同输入两次可能给出不同分组，直接违反"可重复运行"不变量 | D-003, D-007 |
| 先出主题合并候选清单交人工确认 | 每次新增资料都要再来一轮人工，长期维护成本高 | D-003 |
| 直写 CompanyBrain（跳过批次目录） | 架空 K3 的原子发布/回滚与 last-known-good；违反母任务 PRD 的 K1 只产 staging | D-002 |
| 只出预览不写盘 | AC-K1-1/K1-2/K1-3 无真实文件可验，等于交不出东西 | D-002 |
| 新增 `built_from` / `built_by_run` 页头字段 | 下游需学新字段名；且与 ADR 0013「仅允许一个新字段」的授权关系需额外澄清 | D-005 |
| 用现有 `sources` 列表字段承载 KD 溯源 | 该字段已有一个私有格式（1 个页面在用），语义不清 | D-005 |
| 新增独立子命令，不动 `digest` | 用户明确反对：多一个入口，将来会"忘了合并命令"、库内堆积垃圾 | D-018 |
| `digest` 自动识别两种输入 | 一个命令两种行为、靠输入形状猜意图，正是"垃圾堆积"的来源 | D-018 |
| 直接删除旧编译路径 | 失去与 release4 的对照能力；且删除属 K4 范围 | D-018 |
| 全程不调 LLM（纯规则编译） | 合并后的页面标题生硬、跨文件去重无法自然组织文字 | D-007 |
| 连叙述型正文也允许模型改写 | 与 AC-K1-4「零无出处结论」硬碰硬；母任务已把"LLM 改写诱惑"列为风险并以逐字保真压制 | D-007 |
| 不缓存、每次实时调用模型 | 产物抖动、diff 不干净，破坏"可重复运行" | D-007 |
| 把参考块拆到行或单元格 | 丢失表格结构（AC-02 要求结构保留），且逐字保真验证复杂度上升 | D-010 |
| 删除语料中的图片行 | 直接违反 AC-K1-2「参考型内容零丢失」 | D-010 |
| 下载图片/PDF 附件改本地路径 | 需登录内网 `pax-sz.atlassian.net`；母任务把多格式/附件处理列为非目标 | D-010 |
| 全有或全无（任一处不达标即不产出） | 89 份里一份有问题就全白干，容易变成"永远交不出" | D-008 |
| 能写多少写多少、不报阻塞 | 违反"失败不伪装成功"不变量 | D-008 |
| 五类数据状态由模型复核或留人工标注 | 模型复核引入不确定性；留人工标注则交不出可验收产物 | D-009 |
| 只记行号（不记文件+标题） | 原文更新即失效，且读者看不懂 | D-004 |
| 只记文件+标题（不记行区间） | AC-K1-2「逐字一致」无从机器验证 | D-004 |
| 两套坐标都显示在页面上 | 页面被坐标淹没，读者体验差 | D-004 |
| 只冻结首轮清单当回归基准 | 首轮拆漏则永远发现不了，只能证明"稳定"不能证明"没丢" | D-011 |
| 不建清单、只做反向核对 | 只能验"产物里的原文有"，验不了"原文里的产物有" | D-011 |
| 分 4 批（按语料顶层目录）跑 | 批次边界会破坏"按主题合并"（跨批次同主题无法合并） | D-012 |
| 先小批试跑再全量 | 小批的页面划分与全量不同，小批产物不能当验收依据 | D-012 |
| 在本卡内实现分批与恢复 | 用户已选一次跑完，该能力在本卡无使用场景，属无故障证据的能力扩张 | D-013 |
| 与 CompanyBrain 既有页做重叠检测或直接合并 | 需读写正式库、多一套规则与失败路径；"替换/上库"语义属 K3 职责 | D-014 |
| 页面保留中文文件名（只输出碰撞清单） | slug 碰撞依旧存在，上库即互相覆盖（62/89 文件受影响） | D-015 |
| 完全不关心 slug | 用户已选"路径能生成合法 slug"将形同虚设，下游大量页面注定丢失 | D-015 |
| 顺手修好 16 个基线失败用例 | 修的是 K4 要删的旧路径，可能白干且撑大 K1 范围 | D-016 |
| 不区分"本来就坏"与"K1 弄坏" | 交付时无法归因，验收扯皮 | D-016 |
| 把参考块清单与溯源全部嵌进页面 | 参考块可能上千条会淹没正文；与 Q4b 的旁路文件决定相左 | D-017 |
| 现在修订 ADR 0013 | 旁路文件将来是否被 K3 采纳未定，现在写进 ADR 可能白写 | 用户确认（B） |
| 现在就查 16 个基线失败的根因 | 会拖长 make-decision；且那些用例可能随 K4 一起删除 | 用户确认（C） |

## 阶段执行记录

| step | 状态 | 事实 |
| --- | --- | --- |
| 1 load-context | completed | 任务身份与 `任务类型：普通任务` 建立；原始需求落盘于任务记录 `evidence/interactions/original-requirement.md` |
| 2 triage-scope | completed | OI 大纲 v1 建立（6 框架节点 + 6 固定类别 + 19 条 OI）；范围、不确定性与非目标写入本节 |
| 3 talk-round-1 | completed | Round 1 共 28 个问题、28 项用户真实答复（Q0-a…Q24，含 4 次派生追问）；Talk 表完整记录选项、后果、风险与影响重排 |
| 4 research-inputs | completed | 两次子代理只读取证：①K1 事实盘点；②六项定向核实（语料 hash / 聚合哈希 / 冻结 oracle / gbrain slug / CompanyBrain 字段 / 可复用代码 / 测试基线）。结论见 `## 调研` |
| 5 talk-round-2 | completed | 6 项用户真实答复（Q25…Q30），全部由核实事实驱动；OI 升 v2 并回填终态 |
| 6 direction-advice | completed（`available-with-failures`） | wh-review direction track 真实调用；前两次 `MATERIAL_FORBIDDEN`（材料键不在允许清单）经自行诊断后修正，第三次取得 9 条实质 finding。red 三角色全部 completed；blue 的 kimi/coding `RATE_LIMITED`，另两家 completed。F-1…F-8 在本阶段修复，F-9 登记为事实缺陷；OI 升 v3 |
| 7 talk-round-3 | completed | 处理 direction-advice 的建议：消解 3 处真实矛盾（C-1…C-3）、登记 5 条关键假设（A-1…A-5）、列出剩余风险；本轮无新增用户裁决项 |
| 8 grill-with-docs | completed | 建立五类原始消息的覆盖矩阵（无整类缺失）；专项挑战 ADR 0013（发现一处**授权悬空** G-001 与一处范围限定需显式声明）、CONTEXT 术语（一处用词风险 + 一处证据层级澄清）、更小替代路径（含"分批能力不激活"的收窄）；四项退出检查全部通过，本轮零问题 |
| 9 write-decision-draft | completed | 写入 D-001…D-018 决定条目（含选择、理由与事实依据、被拒方案、影响范围、风险）；补 `## 阶段末摘要（六项）`；AC↔OI 对应表建立 |
| 10 detail-advice | completed（`available-with-failures`） | wh-review detail track 真实调用，26 条 finding（去重后 16 个实质问题 D-F1…D-F16，全部处置，零静默丢弃）；首次调用因提交非允许材料键返回 `MATERIAL_FORBIDDEN`，自行诊断后重建材料。据此新增 AC-11/AC-12/AC-13，扩写 AC-03/AC-04/AC-06/AC-08/AC-10，补批次目录两件产物，修正数字与 OI 分类，澄清模型权限边界；新增 RISK-013/RISK-014 与 OPEN-008…OPEN-011 |
| 11 approve-decision | completed | 用户真实确认（`ask_user_question`）：原文「确认，进入 stage-end 与发布（推荐）」；同步确认 ADR 授权处置、基线调查时机、保持 13 条 AC 不放宽。详见 `## 最终确认` |
| 12 stage-end-spec-analyze | unavailable | 需要外部宿主生成的 stage outcome（本会话无外部宿主）；官方发布入口如实返回 `stage_outcome_status=unavailable`（`reason: stage_outcome_missing`），未伪造完成 |
| 13 publish-decision | completed（`quality_status=incomplete`） | 官方 `run --action=execute` 真实执行。结果：12 项质量谓词中 **11 项 satisfied**（scope / non_goals / risks / ui_applicability / requirement_coverage / goal_achievement / acceptance_clarity / solution_convergence / plain_language_card / outline_closed / human_confirmation），**唯一未满足项 = `stage_end_spec_analyze`**（需要外部宿主生成的 stage outcome，本会话无外部宿主，按合同记 `unavailable`）。用户确认经官方 `confirm --action=decision` 写入 canonical 记录（`human-confirmation.v3`）。`missing_items` 仅剩 `current review result is unavailable for finding disposition`，如实保留、未伪造 |
| 14 stage-reflection | unavailable（`executor_absent`） | 调用官方 `run --action=reflect` 真实返回 `status=unavailable`、`error="reflection requires exactly one explicit authenticated executor outcome"`，availability 原件 `quality/evidence/stage-reflection-availability/8a59602115c069f6dd9bc592138db4b301bec007481b38de6b392ab8800c23a8.json`。**根因（自行诊断）**：`stage-reflection.v2` 的 judgment 必须在 `judgments[].evidence_refs` 中引用**恰好一个**`quality/evidence/stage-outcomes/make-decision/<sha256>.json`，而该 stage outcome 只能由**外部宿主**生成；本会话无外部宿主，故无该原件，runner 按合同拒绝并如实记 `unavailable`，不伪造 judgment。stage handoff 同样因缺该来源而 `unavailable`（官方 `run` 输出：`stage handoff requires an authenticated stage outcome source`） |
