# ADR-0011：Task5 Reader-quality 盲审评分合同

## 结论

Task5 不使用页面数、关键词命中、行数、平均分或机器汇总分证明质量。最终评价单位是：

`冻结用户问题/场景 × 五个维度 × 实际 Reader 页面`。

六个固定 case（Q-POS、Q-CON、QR、Zero Touch、Q-DIA、Q-EXP）都要逐项比较；任一维度是 `TIE`、`CB_WIN`、`UNKNOWN`、`INVALID` 或 `CB_MISSING`，都不能发布。

## 盲审边界

- 审查者只读指定运行的 `Home.md`、Reader Markdown、Audit Markdown、冻结的 89 条原始来源和 CompanyBrain 对照页。
- 不读 `quality.json`、自动 verdict、baseline comparison projection 或其他自动评分结果，避免被机器结论带偏。
- 先走 Home 的问题入口，再读 Reader；Reader 不能打开 Audit 或来源时，Reader-Audit 直接失败。
- CompanyBrain 只作为冻结对照观察。CompanyBrain 有但 89 条原始来源没有的事实，要标为“基线额外事实”；KnowledgeDigest 不能补写该事实，也不能把缺源伪装成胜出。

## 五个维度

### 1. 问题/场景路由（route）

从 Home 输入主问题和至少两种自然同义问法，确认是否都能到达同一个正确答案页，并且产品、模块、对象、场景、边界没有在路由中丢失。只要读者仍需先猜文件名，不能判胜。

### 2. 五轴分类（taxonomy）

逐项核对产品、模块、对象、场景、边界：

- 每一项都能从页面回到来源 Claim；
- 对象不是把模块名或文件名冒充业务对象；
- 场景不是泛化成“使用文档”；
- 边界包含版本、设备、权限、状态或不能判断条件（按 case 适用）；
- 不把相邻产品、不同平台或不同状态混在一起。

五项全对但只是“写出来了”不算胜出；必须比 CompanyBrain 更少让读者走错模块或误用对象。

### 3. 业务化答案正文（business-answer）

先写出用户完成任务所需的必答原子，再检查正文是否直接给出答案、关系、操作/诊断动作和边界。页面应把来源事实编译成可用答案，而不是把原文逐行搬过来。

- 定位：是什么、服务谁、解决什么、和谁不同、边界；
- 概念：术语、对象、层级关系、生效条件、误用边界；
- 操作：前置、步骤、结果、验证、失败/回滚；
- 诊断：现象、检查顺序、原因、动作、升级边界；
- 经验：背景、取舍、版本/时间、教训、适用边界。

一条 CompanyBrain 额外事实不在原始语料中时，不要求 KD 凭空补齐；但只要该事实属于当前原始语料的必答原子而 KD 没编译出来，就不能判 `KD_WIN`。

### 4. 页面类型（page-type）

页面类型评价的是五类正文合同是否匹配用户任务，不是比较 Markdown 头部有没有同一个字符串。`reference`、`overview` 等 CompanyBrain 标签不自动等于五类合同；同样标为 `operation` 也不自动平手。

判定要看对应合同的必答槽位是否齐全、有证据、可执行，并比较哪一页更能避免误操作。一个混合页不能代替 Q-BND 的操作页和诊断页两个投影。

### 5. Reader 可见、Audit 可回查（Reader-Audit）

Reader 必须从 Home 可达，正文不泄漏内部 ID；每个可见答案块都必须有 RenderLedger、Audit、source block、snapshot、hash 和 locator。只写“来源：某文件”不算回查；Audit 很完整但 Reader 看不懂也不算通过。

## 判定规则

每项只允许：`KD_WIN`、`TIE`、`CB_WIN`、`UNKNOWN`、`INVALID`、`N/A`、`CB_MISSING`。

- `KD_WIN`：候选必答原子全部成立，禁写项为零，证据完整，并有实际 Reader 证据证明严格优于 CompanyBrain；
- `TIE`：两边都能完成同一任务，或优势只有“字更多/标签不同”；
- `CB_WIN`：CompanyBrain 更完整、准确或更易用；
- `UNKNOWN`：来源、Reader、Audit 或比较证据不够；
- `INVALID`：case、投影或 baseline 合同不完整；
- `CB_MISSING`：CompanyBrain 快照缺失或 hash 漂移；
- `N/A`：双方对该 case 都没有该维度含义，必须写出理由，不能用于当前六个 case。

`KD_WIN` 必须附候选文件行证据、CompanyBrain 文件行证据和一句“为什么是严格胜出”；只附自动 verdict 不算证据。至少两名相互独立的审查者都对六个 case 的五维给出 `KD_WIN`，并绑定相同 `run_id`、source snapshot hash 和候选 Reader/Audit 表面的 `candidate_surface_sha256`，才允许写入 independent-review manifest。最终收口必须使用 `task5_reader_quality.py finalize` 重放同一候选包；不能因为重新调用一次模型得到相似结果就替代对已审查候选包的绑定。

## 失败后的处理

盲审出现非 `KD_WIN` 时，先判断是：

1. 原始语料有事实但编译遗漏：补语义 Claim、页面槽位和回查；
2. 页面有事实但读者找不到：补问题别名、路由链和页面类型；
3. CompanyBrain 使用了原始语料没有的额外事实：保留差异记录，不编造；
4. 来源为空、冲突或无法定位：留在 Audit/candidate，保持 `not_released`。

不能通过改 baseline、放宽 verdict、增加关键词或手工生成 review manifest 绕过失败。
