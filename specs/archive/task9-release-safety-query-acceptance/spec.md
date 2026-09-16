# 规格 · task9-release-safety-query-acceptance（K3：安全地交出去）

> 本文件是 build-spec 阶段唯一权威材料，只细化 `decision-log.md` 已批准的方向；
> 不重开产品方向、不重跑 Talk/Grill。方向级问题回 make-decision，实现拆分归 build-plan。

## 材料导航

| 材料 | 职责 | 状态 |
| --- | --- | --- |
| `specs/task9-release-safety-query-acceptance/decision-log.md` | 方向、用户选择、风险、非目标 | approved（2026-09-15 用户确认） |
| 本文档 | 产品行为、流程、状态、FR/AC、失败边界 | 当前 |
| `plan.md` / `tasks.md` | 工程拆分 | 未开始（build-plan） |
| 母任务 PRD K3 卡 + S2/S3/S5/S7/S8 | 只读上游 | archive |
| K1 spec（task7）/ K2 spec（task8） | 交接接口来源 | archive，只读 |

## 速读卡（30 秒）

- **做什么**：给 KnowledgeDigest 补一条**原子换版通道**（发布/回滚/LKG）和一个**真实查询集验收器**，让新文档消化结果安全合并进用户显式指定的知识库目录，并让"这一批能不能用"可复跑地判定。
- **一句话行为**：发布 = 批次白名单把关 → 库外备份当前版本写指针 → 库外暂存区构造"库内原有内容+本批内容" → 原子换版并更新库根固定入口；读者全程可读，回滚一条命令。
- **不做**：不接 gbrain/检索层、不写既有 1347 页知识库（只读对照快照）、不改 K1 编译语义/K2 导航生成、不做 K4 删码、不新增人工闸门、发布与验收不调 LLM。
- **验收五件套**：四类负例整根等价+写入面差分 / 失败运行三项成本真实且承接编译侧 / 逐题四结果机器重放一致且汇总唯一（硬失败 0+命中率≥80%+未覆盖不计分） / 三类坏样本双向验证 / 三份冻结物齐备可复算。
- **主要风险**：RISK-K3-2（问题集自动生成与母任务 OPEN-002/ADR-0014 冲突，用户维持并保留声明）。

## 来源与决策映射

| 来源 | 内容 | 落点 |
| --- | --- | --- |
| 用户 R-001…R-006 | 标准 WorkflowHub、worktree 先行、六类边界、大白话、上下文控制 | 阶段执行记录 |
| 用户 R-027/R-028（Talk R3 纠正） | KD 与 gbrain/既有库无关；发布=消化合并进指定目录；观察对象=该目录当前版本 | 第 2/5/10 节；NG-009/010 |
| 用户 Talk R1 Q0–Q6 | 范围可修先记录、整库原子、两条命令无闸门、保留 1 版、三项成本非 null、内容快照+sha256、独立发布目录→指定知识库目录 | D-001…D-013 |
| 用户 Talk R2 Q7–Q11 | 修复边界、token 口径改 A、基线缺陷样本双向验证、出题机器生成、目标目录形态 | D-004/5/8、OPEN 关闭 |
| 用户 Talk R3 Q2–Q4 + detail D1–D4 | 固定槽位+指针、独立验收命令+冻结汇总、出题维持机器生成；固定入口+指针、保留库内内容、LKG 放库外、承接编译侧成本 | D-002/4/5/9/13 |
| 用户 grill G-1…G-3 | 切换窗口改固定入口、目标目录运行参数、批次=中间产物 | D-002/4b/13 |
| 用户 spec-clarify C1–C5 | 汇总阈值=硬失败 0+命中率≥80%+未覆盖不计分；问题集=每模块 2 题×3 模板；坏样本三类各绑 2 题；no-op 允许标 true；verify-code 真跑 89 份 | 本文 FR-ACC-003/4、FR-ACC-007、FR-PUB-006、第 15 节 |
| 母任务 S2/S5/S8、OI-25/OI-26 | 冻结三样、负例四类、对照四结果 | FR-FRZ、FR-NEG、FR-ACC |
| K1 spec FR-AUD-004/005 | manifest schema、run-metrics 三项来源、发布输入白名单 | FR-PUB-001、FR-COST-002、PFACT |
| K2 spec SCN-K2-008 | navigation 仅 generated_ok 放行 | FR-PUB-001 |

## 1. 问题与紧迫性

K1/K2 已交付"编译正确的页面 + 三层入口"，但：**没有通道**把这些页面安全放进一个真实知识库目录（现有两套发布机械都接不上：一套要求空目录且不留旧版，一套绑着待删的自证产物与人工确认）；**没有判定器**回答"这一批知识能不能用"（旧自证机器已按 ADR-0014 废除）；失败运行的成本在旧路径上被硬编码为 null（磁盘实物：`release2.failure.run-6e25dd21260b4e45…/failure.json` 中 `observed_calls:null`）。本卡补上这两样，且是 K1/K2/K4 合并前的全链路门禁输入。

## 2. 背景、目标与范围

### 背景

KnowledgeDigest 是独立 CLI 工具：输入新文档（本期=89 份冻结 Confluence Markdown），K1/K2 编译出带 `_audit/page-manifest.json` 的批次目录（`not_released + complete + navigation=generated_ok` 为可发布态）。本卡在批次与读者之间加"安全合并 + 可复跑验收"。

### 目标

G1 发布安全（四类负例整根等价、一条命令回滚）；G2 失败不伪装（三项成本真实非 null 且承接编译侧）；G3 判定可复跑（逐题一致、汇总唯一）；G4 问题集有效（双向验证）；G5 冻结物齐备（缺一即 blocked）。

### 范围内

- 发布命令、回滚命令、验收命令三个 CLI 入口（**参数形态归 build-plan**）；
- LKG 槽位/指针/失败收据的固定格式与写入规则；
- 三份冻结物的快照/清单/齐备门；
- 问题集生成规则、逐题四结果判定、汇总阈值、区分度 fixture；
- 批次白名单、合并规则、no-op 语义、四类负例注入与断言。

### 范围外

K1 编译语义、K2 导航生成、K4 删码、gbrain/检索层、既有 1347 页知识库写入、多格式输入、崩溃级（掉电/SIGKILL）一致性、人工闸门。命令行参数名、模块文件划分、实现算法归 build-plan；本文不写字段级代码符号。

## 3. 用户场景与状态覆盖

角色：**运行者**（跑发布/回滚/验收命令）、**读者**（Obsidian 打开知识库目录）、**验收人**（看 verdict）、**维护者**。

### SCN-K3-001：正常发布（空库首发布/非空库增量）

- **Given** 合法批次（白名单全绿）与目标知识库目录；空库或非空合规库
- **When** 运行发布命令
- **Then** 当前版本整根更新为"原有内容+本批内容"；库根固定入口全程可读；发布记录含新旧 tree hash、批次 attempt_id+hash、成本三项；退出码 0
- **失败**：批次任一项不绿 → 不碰目录，非零码，写明 reason

### SCN-K3-002：合并碰撞（未声明路径）

- **Given** 库内已存在某页面路径，且该路径不在 KD 声明托管范围内，本批欲写同路径
- **When** 发布
- **Then** 硬失败：非零码，目标库零字节变化，原因写明"未声明路径碰撞"
- **依据**：decision D-004/detail D2

### SCN-K3-003：换版中断（写入中断/校验失败）

- **Given** 发布进行至暂存区构造或换版步骤
- **When** 进程内异常注入（copytree/rename/校验点之一抛错）
- **Then** 当前版本仍整根等价旧版；失败收据落库外同级隐藏目录，含原因码+三项成本；重跑一次成功即恢复前进

### SCN-K3-004：取消（进程内协作式）

- **Given** 发布在固定检查点收到取消信号
- **Then** 进程完成恢复后返回非零码；当前版本不变；staging 与 LKG 状态可判（机器判据：锁释放后入口解析版本 tree hash=发布前版本，且库外隐藏目录无本次 `staging-<run_id>` 残留、指针清单无悬空条目）
- **边界**：不承诺 SIGKILL/掉电级（RISK-K3-6，AC 措辞写明）

### SCN-K3-005：越界写入

- **Given** fixture 批次内含一条落在"允许写位置清单"之外的页面路径
- **When** 发布
- **Then** blocked：非零码，目标库零字节变化
- **依据**：decision D-009/detail DB11

### SCN-K3-006：no-op 发布

- **Given** 本批合并结果与库现状整根 tree hash 相同
- **When** 发布
- **Then** 退出码 0，发布记录标 `no_op=true`，不轮换 LKG
- **依据**：clarify C4

### SCN-K3-007：显式回滚

- **Given** 已成功发布至少一次，库外 LKG 槽位有上一版+指针清单
- **When** 运行回滚命令
- **Then** 一条命令按指针整包换回；校验 tree hash 后更新入口；全程可读
- **失败**：指针损坏/槽位缺失 → 非零码并写明，不猜

### SCN-K3-008：失败运行成本（含编译侧）

- **Given** 批次编译阶段已花 provider 调用，随后发布阶段失败
- **When** 读本次运行记录
- **Then** 三项成本=编译侧承接值+发布段自身值，字段分别标明来源；无一为 null
- **依据**：decision D-005/detail D4

### SCN-K3-009：冻结齐备门

- **Given** 三份冻结物已生成（`freeze/<frozen_id>/manifest.json`）
- **When** 运行验收命令
- **Then** preflight 复算逐文件 sha256 与 frozen_id；一致才继续，缺一/不一致 → blocked，零逐题结论
- **边界**：判定器只读 `freeze/<frozen_id>/` 快照，读活库即 blocked

### SCN-K3-010：验收正常通过/不通过

- **Given** 冻结齐备 + 问题集已生成登记
- **When** 验收命令对当前知识库目录逐题判定
- **Then** 产出逐题记录（四结果）+verdict；硬失败题=0 且命中率≥80% → pass；否则 fail；"对照未覆盖"不计分子分母
- **依据**：clarify C1

### SCN-K3-011：被验收对象已变

- **Given** 判定记录绑定被验收树指纹 T1
- **When** 重放时当前版本指纹≠T1
- **Then** 明确报"被测对象已变，不可复跑"，不产出新结论
- **依据**：decision D-006

### SCN-K3-012：区分度检查

- **Given** 三类坏样本（缺表格/错出处/孤儿页）各绑 2 道必失败题，随冻结入库
- **When** 对坏样本跑问题集
- **Then** 各绑定题全部判失败；对正确产物跑同一批题不误判

### 状态覆盖清单

- [x] **默认态**：SCN-K3-001/007/010
- [x] **空态**：首发布（空目录建骨架）；问题集 0 题/重复 id → blocked（SCN-K3-010 preflight）
- [x] **错误态**：SCN-K3-002/003/005/008/011
- [x] **取消态**：SCN-K3-004
- [x] **加载态**：N/A（CLI 一次性命令；进度可见性不在本卡）
- [x] **边界态**：no-op（006）、并发（验收先取同一把库锁，见 FR-ACC-006）
- [x] **权限态**：允许写位置清单；越界硬失败（默认必须成立，见第 10 节）
- [x] **竞态**：发布/回滚/验收互斥（库级锁）；与读者无锁（固定入口保证读者永远可读）

## 4. 产品事实与假设（PFACT-K3）

- **PFACT-K3-001**：K1 批次 `_audit/page-manifest.json` schema=`task7-page-manifest.v1`；`publish_status` 在 K1 只允许 `not_released`（写 `released` 直接 ValueError）；`run_status∈{complete,blocked,interrupted}`；K2 把 `navigation={navigation_status,success_pages,blocked_sources,blocked_reasons}` 写回同一 manifest（`semantic_navigation.py:126-146`）。证据：调研取证一 #6a。
- **PFACT-K3-002**：K1 每批次 `_audit/run-metrics.json` 已有耗时/调用数/token 三项真实来源（`semantic_compiler.py:1384-1427` elapsed_ms；`:178-190/805-815/957-999` token；`provider_usage_unavailable` 词表）。证据：调研取证一 #3。
- **PFACT-K3-003**：现有 `full_release.atomic_release` 只借鉴机械（锁内整包替换+读回校验+失败自动恢复）；其入口与完整包判据不复用（含待删自证产物+人工确认；成功路径旧版不清理不建指针）。证据：D-010、红队 F-3/蓝队 B2。
- **PFACT-K3-004**：`kb_structure.default_publication_structure()` 存在，可生成新库默认骨架（`kb_structure.py:439-501`）。证据：蓝队 DB8 复核。
- **PFACT-K3-005**：磁盘事实：89 份语料在 `/Users/Hugh/Downloads/confluence 原始数据`（1.4 MB）；改造前快照 `…/KnowledgeDigest-task5-m402-20260908.release4`（14 MB/108 md）在盘；既有知识库 1347 md 无快照需本卡冻结；`~/Downloads/KD测试` 当前为空（无真实批次）。证据：调研取证一 #6b + 主会话补证。
- **PFACT-K3-006**：`observed_calls=null` 实物证据：`release2.failure.run-6e25dd21260b4e45…/failure.json`（`reason_code=QUALITY_FINALIZE_ValueError`）。该旧路径（`publisher.commit`）本卡不再可达；null 硬编码登记为随 K4 删除旧路径时清除，本卡不修（D-005 归属声明）。
- **PFACT-K3-007**：失败注入点与先例齐全：`kb_lock` 获取、copytree、拷贝后树哈希、两次 rename、projection 校验（`test_task3_quality_release.py:815-875`）。证据：调研取证一 #4。
- **假设**：目标知识库目录所在磁盘有足够空间容纳整库一份 LKG 副本（RISK-K3-5 用户已接受）；验收/发布期间无第三方进程写库（单写者假设，违反=未定义行为但负例注入自身不依赖此前提）。

## 5. 功能需求

### 发布通道（PUB）

- **FR-PUB-001 批次白名单**：发布命令读取批次 `_audit/page-manifest.json`，仅当 `run_status=="complete"` 且 `publish_status=="not_released"` 且 `navigation.navigation_status=="generated_ok"`（**显式等于**，不得写成"不等于 blocked 就放行"）且 `blockers` 为空数组时放行；缺任一即 blocked，非零码，reason 写明缺哪项。`publish_status=released` 由 K3 自己的发布记录承载（引用批次 attempt_id+hash），**不回写** K1 manifest。
  - 依据：D-011、蓝队 M6；场景：SCN-K3-001；验收：AC-K3-1。
- **FR-PUB-002 合并规则**：新版本 = 目标库原有内容 + 本批新增/更新（批次为中间产物、知识库目录为正式交付物，见 D-004b）。允许写范围=`kb.structure.md` 声明的托管页面路径与库级结构页/索引页；**未声明托管的路径一律保留、不删除**；未声明路径与批次内容同路径碰撞 → 硬失败（非零码、目标库零字节变化、reason=`path_collision_unmanaged`）。批次内证据型文件（`products/**` 页面、`_audit/**`）**逐字节复制**（断言源 sha256=目标 sha256），不重新渲染、不改 frontmatter、不重排锚点。
  - 依据：D-004/detail D2、蓝队 DB7；场景：SCN-K3-001/002；验收：AC-K3-1/AC-K3-3。
- **FR-PUB-003 目标目录处置**：目标知识库目录由运行参数显式提供。不存在或存在且为空 → 用 `default_publication_structure()` 建默认骨架并登记骨架 sha256；存在且非空但无有效结构声明 → 拒绝（非零码）。父目录必须存在。
  - 依据：D-013、grill G-2、蓝队 DB8；场景：SCN-K3-001；验收：AC-K3-5。
- **FR-PUB-004 固定入口与原子换版**：库根存在固定名字的**当前版本入口**（指针文件/目录约定由 build-plan 定，本契约固定：入口路径恒定、内容只指向一个版本目录）。换版步骤顺序：① 库级写锁（锁文件放目标库**父目录**）；② 在**库外同级隐藏目录下 `staging-<run_id>/`** 构造暂存版本目录（staging 落点已冻结并列入允许写位置清单）；③ 当前版本整份复制入库外同级隐藏目录的 LKG 槽位；④ 原子更新指针；⑤ 读回校验（入口解析到的版本 tree hash = 新 tree hash）。读者在任何时刻通过入口读到完整旧版或完整新版。**staging 清理责任**：发布进程在成功/失败/取消的 finally 中清理本次 staging；进程崩溃残留由下一次发布启动时检测（`staging-*` 超时）并清理，清理动作只动库外隐藏目录。
  - 依据：D-002/detail D1/D3、红队 N-1/N-4；场景：SCN-K3-001/003；验收：AC-K3-1。
- **FR-PUB-005 LKG 与回滚**：LKG 槽位、指针清单、发布记录、失败收据统一放目标库**外同级隐藏目录**，并全部列入"允许写位置清单"。指针清单内容：版本 id、tree hash、来源批次 attempt_id、写入时间。保留最近 1 个可回滚版本；成功发布后轮换旧 LKG；**LKG 不计入被验收 tree hash**。回滚命令全程持有与发布相同的库级写锁，步骤：读指针→校验槽位 tree hash→**把当前版本存入槽位（被换下的版本成为新的 LKG，回滚同样执行"备份当前→换版→轮换"）**→更新入口→读回校验；指针损坏/槽位缺失 → 非零码写明，不猜。no-op 发布不改指针，发布记录提示当前可回滚目标。
  - 依据：D-002、Talk R3 Q2、detail D3；场景：SCN-K3-007；验收：AC-K3-1。
- **FR-PUB-006 no-op**：本批合并结果与库现状整根 tree hash 相同 → 退出码 0，发布记录标 `no_op=true`，不轮换 LKG，不空写。
  - 依据：clarify C4；场景：SCN-K3-006；验收：AC-K3-1。
- **FR-PUB-007 失败收据**：发布/回滚失败必须写失败收据（库外同级隐藏目录），含 reason_code、三项成本（见 FR-COST）、批次 attempt_id、目标库指纹快照；不得为 null、不得缺字段。**收据落盘失败降级**：尽力落盘 + 同内容镜像写入 stdout/运行记录 + 专用 `reason_code=receipt_sink_unavailable`；AC-K3-2 观测到"收据文件缺失但运行记录含完整镜像"视为显式失败而非缺证据。
  - 依据：D-005、红队 N-4；场景：SCN-K3-003/008；验收：AC-K3-2。

- **FR-PUB-008 tree hash 算法（冻结）**：版本目录的 tree hash = 对目录内全部常规文件（相对 posix 路径、字典序排序、UTF-8）逐文件计算 sha256，再对每行 `相对路径:文件sha256\n` 拼接结果整体取 sha256。符号链接在版本目录内禁止出现（出现即校验失败）；库外同级隐藏目录与父目录锁文件不参与 hash；入口指针文件本身不属于版本目录。**本算法同时用于**等价断言（AC-K3-1）、no-op 判定（FR-PUB-006）、LKG 指针与验收绑定指纹，跨实现可复算。
  - 依据：红队 F7；验收：AC-K3-1/AC-K3-3。

### 成本度量（COST）

- **FR-COST-001 三项真实**：成功与失败运行共用一份 run 记录 schema：`elapsed_ms`、`provider_calls`、`provider_tokens` 三项真实非 null；真实发生的 0 合法但必须附 reason（`cache_hit` / `no_provider_call_yet` / `provider_unavailable`，复用 K1 词表，不新增第三套）；无法归因的 0 或与 reason 矛盾的计数判失败。
  - 依据：D-005、母任务 OI-26；场景：SCN-K3-008；验收：AC-K3-2。
- **FR-COST-002 承接编译侧**：发布命令启动时读批次 `_audit/run-metrics.json`，把编译侧三项承继进本次 run 记录（字段标 `inherited_from_compile`），发布段自身消耗另列字段。由此"编译已花调用后再失败"的运行被真实计量，发布段 0+reason 的真空满足被堵死。
  - 依据：detail D4、红队 N-3/蓝队 DB2；场景：SCN-K3-008；验收：AC-K3-2。
- **FR-COST-003 旧路径归属**：`publisher.py:113` 的 `observed_calls=null` 硬编码登记为**随 K4 删除旧 `commit` 路径时清除**；本卡新通道不复用该路径，不在本卡修复；本卡验收引用 F-002 实物基线（release2/release3 failure.json）作对照。
  - 依据：D-005 归属声明、PFACT-K3-006；验收：AC-K3-2 证据引用。

### 冻结物管理（FRZ）

- **FR-FRZ-001 三份冻结物**：① 89 份输入清单+逐文件 sha256（**恰 89 份 `.md`**，排除 `.DS_Store` 等；清单路径与指纹可复算）；② 改造前产物快照（release4）；③ 对照知识库快照（只读输入）。快照=不可变内容拷贝；清单=逐文件 sha256 列表。
  - 依据：D-006、母任务 S2；验收：AC-K3-5。
- **FR-FRZ-002 排除规则**：对照库快照与清单**跳过** `.` 开头文件与 `_gbrain/` 生成镜像（sync 会重写，导致 frozen_id 不稳定）；排除规则本身写入清单并参与 frozen_id 推导。
  - 依据：红队 N-9；验收：AC-K3-5。
- **FR-FRZ-003 frozen_id**：`freeze/<frozen_id>/manifest.json`；`frozen_id` = 清单内容确定性推导（如清单 sha256）；manifest 含三份根路径、文件数、逐文件 sha256、各自 tree hash、排除规则、生成时间。
  - 依据：D-006；验收：AC-K3-5。
- **FR-FRZ-004 齐备门与读取边界**：齐备检查是验收命令的 preflight：任一缺失、或 hash 复算不一致 → blocked，零逐题结论。**对照侧**：判定器只读 `freeze/<frozen_id>/` 下对照快照，触达对照活库路径即 blocked（preflight 断言）。**被验收侧**：仅允许两类读取——①取与发布相同的库级锁后读当前版本树指纹（FR-ACC-006）；②逐题判定时只读解析入口所指向的版本目录内容。两类之外的被验收库路径触达即 blocked。
  - 依据：D-006、蓝队 M4/DB12；验收：AC-K3-5。
- **FR-FRZ-005 指纹复用**：同一次运行中整库 tree hash 计算结果缓存复用（发布、LKG、验收共用一次计算），避免整库反复全量哈希。
  - 依据：蓝队 m1；归 build-plan 实现。

### 验收判定（ACC）

- **FR-ACC-001 独立验收命令**：验收是独立 CLI 入口（参数形态归 build-plan），不在发布时自动运行；输入=冻结问题集+三份冻结物+被验收树指纹；输出=逐题记录+verdict+成本三项。
  - 依据：D-007/Talk R3 Q3；验收：AC-K3-3。
- **FR-ACC-002 问题集生成（确定性）**：从冻结资料自动生成。规则：对每个模块（`products/<产品>/<模块>/`）出 **2 题**；题面从该模块页面的标题与参考块首行**确定性抽取**（同输入同题集）；问句用 **3 种固定模板**（"X 是什么"/"X 怎么配置"/"X 的参数有哪些"，模板名与措辞以本条款为准）。**模板选取**：模块内题目按页面路径字典序排列，第 i 题取模板表[i mod 3]。**缺料降级**：页面缺标题→用文件名 slug；缺参考块→该题改用该页叙述首句；某模块可抽取要素不足 2 题→出 1 题并记入 `degraded_modules` 清单（不使生成失败；degraded 模块仍计入模块数）。全部规则写入生成器并随冻结物登记 sha256；规则变更=新口径版本，不得静默替换。
  - 依据：clarify C2、D-008；验收：AC-K3-3/AC-K3-4。
- **FR-ACC-003 四结果与机器定义**：每题判定四结果，各自可执行定义：**答案命中**=判定器给出的答案能回溯到冻结输入的具体行区间+内容指纹一致（**不是**词面重合）；**定位有效**=判定器给出的定位（页面路径+块锚点）能在入口指向的版本目录中解析到存在的内容块；**出处正确**=该内容块附带的来源引用（source_uri+内容指纹+行区间）与冻结输入对应行按指纹一致；**对照未覆盖**=对照快照中按同一检索口径没有对应内容（不计我方优势）。
  - 依据：母任务 S8、红队 N-6；验收：AC-K3-3。
- **FR-ACC-004 汇总（冻结阈值）**：verdict 可执行规则：**硬失败题=0**（硬失败题定义=对照侧有答案但新库完全找不到，或找到的内容出处对不上原文）**且** 答案命中且出处正确率 **≥80%**；「对照未覆盖」题不计入分子也不计入分母；有效分母（非未覆盖题数）**=0 → verdict=fail（`no_effective_questions`）**；有效分母 **<10 → blocked（题集不足以判定）**。同一份逐题记录只能得出唯一结论。
  - 依据：clarify C1、D-007；验收：AC-K3-3。
- **FR-ACC-005 判定记录绑定**：逐题记录+verdict 绑定：被验收树指纹（tree hash）、问题集 sha256、判定口径版本、frozen_id；重放先校验四者，被验收对象已变 → 明确报"被测对象已变，不可复跑"，不产出新结论。
  - 依据：D-006 补充、红队 F-6；场景：SCN-K3-011；验收：AC-K3-3。
- **FR-ACC-006 并发与锁**：验收读取被验收树指纹前必须取与发布/回滚相同的库级锁；取不到锁 → 等待或报错，不得读到换版中间态。
  - 依据：蓝队 DB6；验收：AC-K3-1/AC-K3-3。
- **FR-ACC-007 区分度 fixture**：坏样本三类：缺表格的页 / 错出处链接的页 / 孤儿页；每类绑 **2 道必须判失败**的题+期望失败原因；样本与绑定关系随冻结物入库登记 sha256。通过条件=三类样本各自的绑定题全部判失败，且正确产物上同一批题不判失败。
  - 依据：clarify C3、D-008、红队 N-6；场景：SCN-K3-012；验收：AC-K3-4。
- **FR-ACC-008 问题集 preflight**：题数=0、题 id 重复、必填字段缺失 → blocked，不出逐题结论。
  - 依据：蓝队 DB11；验收：AC-K3-3。

### 负例注入（NEG）

- **FR-NEG-001 四类负例与断言**：写入中断（进程内异常注入 copytree/rename/校验点）、取消（固定检查点协作式取消）、校验失败（暂存区树哈希不符）、越界写入（fixture 批次含未声明路径）。每类注入后断言：当前版本整根 tree hash 等于旧版或新版之一（不存在第三种状态）；目标库零字节变化（对 blocked 类）。
  - 依据：D-009、母任务 S5；场景：SCN-K3-003/004/005；验收：AC-K3-1。
- **FR-NEG-002 覆盖声明**："写入中断/取消"只承诺进程内异常级；掉电/进程被杀（SIGKILL）不在覆盖范围（现有机械无 fsync，若要崩溃级须另立变更）。AC 措辞不得含混。
  - 依据：RISK-K3-6、蓝队 m3/DB10；验收：AC-K3-1 措辞。

### 数据状态与 CLI

- **FR-STA-001 五类状态沿用 K1**：`ready/known_empty/duplicate_alias/audit_only/资料未明确` 由 K1 判定并写入来源台账；发布侧只逐字节复制台账与页面，不重算、不改写；"资料未明确"不进事实分母（沿用 K1 口径）。
  - 依据：OI-10、K1 FR-AUD-003；验收：AC-K3-1（逐字节复制的差分断言）。
- **FR-CLI-001 三个入口**：提供发布、回滚、验收三个 CLI 入口；退出码语义：0=成功（含 no-op），非零=失败/blocked，且失败必有机器可读 reason。参数形态、子命令拼写归 build-plan。
  - 依据：D-002/D-007/grill G-2；验收：AC-K3-1/2/3。
- **FR-LED-001 缺陷台账与修复纪律**：验收/发布链路暴露的 K1/K2 缺陷先登记台账（append-only，库外同级隐藏目录，字段：id/severity/evidence/是否本卡修复/修复后新批次 hash），**只允许修"使批次无法发布或验收不成立"的阻塞级**；任何 K1/K2 修复必须产出新批次并全量重跑，**旧判定记录标 void、不得重放**；该次整跑 89 份的 provider 成本计入 AC-K3-2 成本账。
  - 依据：D-012、红队 N-8；场景：SCN-K3-001（修复后重跑路径）；验收：AC-K3-2/AC-K3-3。

## 6. 模块划分（产品职责）

- **发布通道**：白名单把关、合并构造、LKG/指针、入口原子换版、no-op、失败收据。
- **成本度量**：run 记录 schema、编译侧承接、reason 词表校验。
- **冻结物管理**：快照、清单、frozen_id、齐备门、只读快照断言。
- **验收判定**：问题集生成、四结果判定、汇总阈值、判定记录绑定、区分度 fixture。
- **库级互斥**：发布/回滚/验收共用的锁（放目标库父目录）。
- 实现文件划分归 build-plan；本卡不复用 `full_release.atomic_release` 入口与 `publisher.commit`（D-010）。

## 7. 关键实体

| 实体 | 内容要点 | 生命周期 |
| --- | --- | --- |
| 批次目录（K1/K2 产物） | `page-manifest.json`、`products/**`、`_audit/**` | K1 产出后只读；本卡不改写 |
| 目标知识库目录 | 用户显式指定；结构声明+托管路径清单 | 本卡唯一写入的库 |
| 当前版本入口 | 库根固定路径指针 → 版本目录 | 每次发布原子更新 |
| 版本目录 | 一次发布的整库内容 | 被入口指向；旧版由 LKG 槽位保留 |
| LKG 槽位/指针清单 | 库外同级隐藏目录；最近 1 版+指针 | 发布后轮换 |
| 发布记录/失败收据 | 新旧 tree hash、attempt_id、成本三项、reason | 库外同级隐藏目录，append-only |
| 冻结物/`frozen_id` | 三份快照+清单+manifest | 验收前冻结；不可变 |
| 问题集 | 每模块 2 题×3 模板；sha256 登记 | 随冻结物入库 |
| 逐题判定记录/verdict | 四结果+绑定（树指纹/题集 sha/口径版本） | 机器重放 |
| 坏样本 fixture | 三类×2 题绑定 | 随冻结物入库 |

## 8. 数据和生命周期

- **批次→库**：批次（not_released 中间产物）→ 发布（白名单+合并+LKG+入口）→ 库（released 态，发布记录承载，不回写 K1 manifest）。
- **失败运行**：失败收据含成本与 reason；可重跑恢复。
- **验收**：冻结 → preflight（齐备+只读断言+指纹绑定校验）→ 逐题判定 → 汇总 → verdict；重放先校验绑定，不一致即"不可复跑"。
- **回滚**：指针→槽位→整包换回→入口更新；回滚本身也是一次运行（记成本）。

## 9. 兼容性预留

- **K1/K2 消费方**：manifest 语义零改动；`publish_status=released` 词表保留给 K3 记录语义（不回写）。
- **旧发布路径**：`publisher.commit`/`atomic_release` 保持现状不动（前者随 K4 处置）；新通道与旧代码并存至 K4。
- **既有知识库**：只读对照快照输入；永不写入（NG-010）。
- **扩展边界**：本卡不预留检索层/多格式输入/崩溃级一致性接口。

## 10. 明确不做与默认必须成立

### 明确不做（继承 decision-log NG，本卡不重新论证）

NG-001 不做问答/RAG/前端；NG-002 主会话不重读量取证；NG-003 不改 K1 编译语义/K2 导航/K4 删码；NG-004 不修停摆流水线；NG-005 不引自证绿灯（含不复用待删自证产物作发布判据）；NG-006 本阶段不承诺 commit/merge/push/cleanup；NG-007 不引向量库/图库/服务化/多格式；NG-008 不新增人工闸门；NG-009 不接 gbrain/检索层/索引配置；NG-010 不写既有 1347 页知识库；NG-011 发布与验收不调 LLM（问题集由程序确定性生成）。

### 默认必须成立

- 允许写位置清单 = 目标库内声明路径 + 库外同级隐藏目录（LKG/指针/记录/收据）+ 父目录锁文件；清单之外零写入。
- 证据型文件逐字节复制（源 sha256=目标 sha256）。
- 判定器只读冻结快照。
- 验收与发布/回滚同锁互斥。
- 批次白名单四字段显式判定（FR-PUB-001）。
- 「资料未明确」不写成结论、不进分母。

## 11. 验收标准

**场景**：以 89 份冻结输入跑一次 K1/K2 编译产出合法批次 → 发布进指定知识库目录 → 注入四类负例 → 用冻结问题集做逐题对照判定 → 重放校验。

**数据来源**：89 份输入清单（恰 89 份 .md+逐文件 sha256）；改造前产物快照（release4，14 MB/108 md，已在盘）；对照知识库只读快照（1347 md，排除 `_gbrain/` 与 `.` 开头文件）；被验收树指纹；F-002 实物基线（release2/release3 failure.json）。

| AC | 方法 / oracle | 通过 | 失败 |
| --- | --- | --- | --- |
| AC-K3-1 原子发布与回滚 | 四类负例机器注入（FR-NEG-001）+ 整根断言：入口解析版本 tree hash ∈ {旧版， 新版} | 四类负例全通过；一条命令回滚成功且全程可读 | 任一负例出现第三种状态/半成品/blocked 类动了库字节 |
| AC-K3-2 失败显式化与成本 | 注入失败运行读 run 记录+失败收据；对照 F-002 实物 | 成功/失败运行三项非 null；真 0 带 reason；失败运行承接编译侧真实消耗 | 任一 null、**虚报（计数与 reason 矛盾或无法归因，定义见 FR-COST-001）**、0 无 reason、未承接编译侧 |
| AC-K3-3 判定记录可复跑 | 同一（题集 sha+树指纹+口径版本+frozen_id）机器重放逐题比对 | 逐题一致；同一份记录按 FR-ACC-004 只能得出唯一结论 | 不可复跑/逐题缺失/汇总可被人为翻案/被测对象已变仍出结论 |
| AC-K3-4 问题集有效性 | 三类坏样本（各 2 绑定题）+ 正确产物双向跑 | 坏样本绑定题全判失败；正确产物同一批题不误判 | 任一样本绑定题漏判/误判正确产物 |
| AC-K3-5 冻结物齐备 | preflight 复算 frozen_id 与逐文件 sha256（含排除规则） | 三份齐备、复算一致；判定器未触达活库 | 任一缺失/不一致仍出逐题结论/读了活库 |

## 12. 风险、未决与交接

### 风险（继承 + 本阶段状态）

- **RISK-K3-2**：问题集机器生成与母任务 OPEN-002/ADR-0014 冲突——**用户维持**（C2 再次确认）；本规格按"规则确定性+sha256 登记+双向验证"最大化其可辩护性；冲突声明随 spec 进入 build-plan，不静默。
- **RISK-K3-4**：本卡 verify-code 需真跑一次 89 份 K1/K2 编译（C5 已定时点）；provider 成本计入 AC-K3-2 成本账。
- **RISK-K3-1**（全自动无人工闸门）：保留，由 AC-K3-1/AC-K3-2 压制，与 decision-log 一致。
- **RISK-K3-3**（固定入口方案下读者缺失窗口已消除）：关闭为"已缓解"，入口指针方案使读者在任何时刻可读到完整版本。
- **RISK-K3-5/RISK-K3-6/RISK-K3-8**：保留，口径已写死（LKG 占一份磁盘；不承诺崩溃级；tree hash 单次计算复用+算法已冻结 FR-PUB-008）。
- **RISK-K3-7**：母任务 PRD 与 ADR-0013 未按 R-027 修订——交接事实，归用户/母任务层。

### 未决项（本阶段处置）

- OPEN-K3-4 → 已由 C1 关闭（FR-ACC-004）。OPEN-K3-5 → C3 关闭（FR-ACC-007）。OPEN-K3-6 → C2 关闭（FR-ACC-002）。OPEN-K3-3 → 归 build-plan（参数形态）。OPEN-K3-7 → 用户/母任务层。DEF-K3-3 → C5 关闭（verify-code 真跑全链路，见 §12 风险节 RISK-K3-4 与 §13 交接）。DEF-K3-1 → 用户 owner 不变。

### 交接给 build-plan 的边界

- 冻结：命令参数形态、模块文件划分、LKG 槽位目录名、入口文件格式选型、锁实现、坏样本 fixture 的具体构造脚本——**只能引用本 spec 的 FR 执行，不得改动口径**；如需改阈值/模板/样本类型，回 make-decision。
- verify-code 依赖：真跑一次 89 份编译（provider 配置可用性需在 plan 阶段确认）。

## 13. 业务影响与回归范围

- `digest` 命令族新增发布/回滚/验收入口（K1 的 FR-CLI-001 只允许"不新增子命令"——本卡为其下游卡，命令形态由 build-plan 与 K1 口径对齐后确定，若冲突回 make-decision 增量裁决）。
- 既有测试不绑定新入口，零回归面；旧发布路径测试原样保留至 K4。
- 产物面：库外同级隐藏目录（LKG/记录/收据）为新增磁盘占用面，需 `.gitignore` 类约定归 build-plan。

## 14. 阶段执行记录（build-spec）

- step 1 read-decision-log：读 decision-log（approved）+ K1/K2 spec 接口节 + 调研取证结论；建立来源映射（第 3 节表）。
- step 2 conditional-spec-research：**skipped**——PFACT-K3-001…007 已覆盖全部接口/数据/状态事实（证据：调研取证一 #1-#6 + 主会话补证），无新 gap；按技能要求记录跳过原因。
- step 3 spec-clarify：**trigger=true，一轮批次 5 问已收真实答复**（C1 阈值/C2 题集规则/C3 坏样本/C4 no-op/C5 时点），全部按推荐口径冻结；无 dependent 问题遗留。
- step 4 spec-specify：本文件。
- step 5/6 simplicity-guard / plan-ceo-review：主会话自检——无新工程方案入 spec（无文件清单/代码符号/测试命令）；产品方向零 invention（逐条可回溯到 decision-log 或 C1-C5 答复）。
- step 7-9 UI 路径：`non_ui`，N/A + reason（decision-log UI applicability fact）。
- step 10 freeze-spec：本文件即冻结稿。
- step 11 review-frozen-spec：见下节审查记录。
- step 12 处置：见下节。
- step 13 stage-end-spec-analyze：见第 15 节。
- step 14/15 发布与复盘：官方 outcome 依赖宿主 bridge，记录真实状态。

## 15. 审查记录与阶段末自检

### review-frozen-spec（step 11）· 真实执行，结果 = `available-with-failures`（不是 pass）

- 执行方式：红/蓝两路独立子代理只读审查（同 make-decision 既定做法），输入包 `review/task9-spec-packet.md`；红队 12 条 finding（blocking F1/F2），蓝队 9 条 finding（blocking B1=与 F3 同源）。全文：`review/task9-spec-red.md`（`cde972831233…`）、`review/task9-spec-blue.md`（`1ed431066066…`）。
- provider 事实：本轮经宿主子代理执行，未走 wh-review provider；`unavailable` 不伪装成 pass。

| finding | 等级 | 处置 | 落点 |
| --- | --- | --- | --- |
| F1/B3 判定器读取边界自相矛盾（禁活库误伤被验收库） | blocking | **fixed**：FR-FRZ-004 拆为对照侧（禁活库）/被验收侧（仅两类读取） | FR-FRZ-004 |
| F2 staging 落点未定义 | blocking | **fixed**：staging 冻结为库外同级隐藏目录 `staging-<run_id>/`，入允许写清单，含清理责任 | FR-PUB-004 |
| F3/B1 缺陷台账（D-012）沉默丢弃 | major | **fixed**：新增 FR-LED-001（台账+只修阻塞级+修复须新批次全量重跑+旧判定 void+成本入账） | FR-LED-001 |
| F4 全未覆盖时分母 0/0 | major | **fixed**：有效分母=0→fail；<10→blocked | FR-ACC-004 |
| F5 定位有效/出处正确无机器定义 | major | **fixed**：四结果各一行可执行定义 | FR-ACC-003 |
| F6 模板选取/缺料降级缺失 | major | **fixed**：i mod 3 选取+降级规则+degraded_modules 清单 | FR-ACC-002 |
| F7 tree hash 构造未冻结 | major | **fixed**：FR-PUB-008 冻结算法（排序+逐文件 sha256+拼接式；软链禁止；跨实现可复算） | FR-PUB-008 |
| F8 写入面无 AC 承接 | major | **fixed**：AC-K3-1 增写入面差分 oracle（父目录整树快照，仅清单内可增改） | §11 AC-K3-1 |
| B2 回滚取锁 / 回滚后槽位 | major | **fixed**：FR-PUB-005 回滚全程同锁+被换下版本成为新 LKG+no-op 不改指针 | FR-PUB-005 |
| F12 收据落盘失败无降级 | minor | **fixed**：尽力落盘+stdout/运行记录镜像+`receipt_sink_unavailable` | FR-PUB-007 |
| F9 no-op 回滚退穿语义 | minor | **fixed**：回滚永远以指针为准，no-op 记录提示可回滚目标 | FR-PUB-005 |
| F10 "校验三者"实为四项 | minor | **fixed**：改"四者" | FR-ACC-005 |
| F11 三模板文案疑自增 | minor | **rejected_invalid**：三模板文案（是什么/怎么配置/参数有哪些）逐字来自用户 C2 所选选项，非自增；已在 FR-ACC-002 标注"以本条款为准" | — |
| 蓝 minor（C5 落点/STA 挂 AC/SCN-004 判据/虚报定义） | minor | **fixed** 四处 | §12/FR-STA-001/SCN-K3-004/AC-K3-2 |

### stage-end-spec-analyze（step 13）· 主会话语义自检

- 决策→规格覆盖：D-001…D-013+D-004b 全部有落点；OI-01…16 全部关闭；C1–C5 忠实冻结；NG-001…11 全部继承。
- 必交 10 项齐（蓝队独立复核 9/10→修复后 10/10）；5 条 AC 均含可机读 oracle 与失败条件。
- 无 gap 需回 make-decision；无新 scope invention；无工程实现泄漏（无文件清单/代码符号/测试命令）。

### 阶段末六段大白话总结（交 build-plan）

1. **本阶段做了什么**：把已批准的决策变成可测试规格——12 条场景、29 条 FR（PUB 8/COST 3/FRZ 5/ACC 8/NEG 2/STA 1/CLI 1/LED 1）、5 条带 oracle 的 AC、实体生命周期、11 条非目标；一轮 spec-clarify（5 问全收）+ 一轮红蓝审查（21 条 finding 全部处置）。
2. **需求覆盖**：母任务 FR-K3-1…5、S2/S5/S8 与用户 28 条 R 全部落规格；16 个 OI 终态可机读。
3. **上游对齐**：K1 manifest 白名单四字段显式等于；K2 navigation 仅 generated_ok；tree hash 算法跨实现可复算；与 decision-log 零冲突（审查确认）。
4. **本阶段修复**：两处 blocking 自相矛盾（验收读取边界、staging 落点）+ 一条决策沉默丢弃（缺陷台账）+ 验收可执行性一组洞（分母 0/0、四结果机器定义、模板选取、tree hash 算法、写入面差分）。
5. **剩余风险**：RISK-K3-2（出题机器生成与 ADR 冲突，用户维持，随 spec 进 build-plan）、RISK-K3-4（verify-code 需真跑 89 份，provider 可用性 plan 阶段确认）、RISK-K3-6（不承诺崩溃级）、RISK-K3-7（母任务 PRD/ADR-0013 未修订，归用户）。
6. **下一阶段边界**：build-plan 只做工程拆分——命令参数形态、模块文件划分、staging/LKG 目录名、锁实现、坏样本构造脚本、生成器实现；**只能引用执行本规格，不得改动阈值/模板/样本类型/算法**；改动须回 make-decision。

### 发布与复盘（step 14/15）

- 官方 stage outcome 依赖宿主 Stage Agent bridge，本会话无 bridge → 记 `unavailable（executor_absent）`，同 make-decision；材料与确认真实完成，不伪装。
- stage-reflection judgment 按 v2 schema 备好（六区块，status=degraded），公共入口要求 executor source/timing/output hash → 记 `unavailable`；judgment 要点并入本记录。

