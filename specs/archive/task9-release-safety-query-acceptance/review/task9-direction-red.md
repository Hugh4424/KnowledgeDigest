# KnowledgeDigest task9 / K3 方向审查 · 红队（对抗性）

范围：`specs/task9-release-safety-query-acceptance/decision-log.md`（OI-01…OI-14、Talk R1/R2「已选方向」）与母任务 PRD K3。所有代码引用均为只读核对所得。总结论：**方向里 6 条会直接导致验收无效或核心目标落空，必须回到 Talk Round 3 重新裁决，不能按现态进 spec/plan。**

## Findings

F-1 | blocking | OI-14 / Talk R2 Q10；ADR-0014:9；母任务 PRD K3「依赖」（用户参与出题 OPEN-002） | 让被验收系统从 89 份资料自己出题＝自己出卷自己考：题目和答案同源，对照侧能答的题不会出现；决策记录自己已标为争议项、OI-14 仍 open，方向包却写成「已收敛方向 9」 | 回 A（用户出题后冻结）或 A+B（用户出题、模型只润色且逐题确认）；题目须可追溯到真实读者提问，禁止由被验收语料生成
F-2 | blocking | OI-11；PRD FR-K3-1:84、FR-K1-3:48；ADR-0013；K1 RISK-007 / DEF-002；packet 事实 27 | 独立发布根 +「不写 gbrain 配置与索引」＝知识只落到没人检索的目录；FR-K3-1「读者与 gbrain 只见完整新版」、FR-K1-3「gbrain 按 slug 可检索」在方向里没有任何一步能证明，而 OI-11 的反例只查「不写 CompanyBrain」、从不查「gbrain 看得到」→ 验收可全绿但根本没交出去 | 二选一写死：(a) 诚实降级——交付物止于发布根，FR-K3-1/FR-K1-3 的 gbrain 子句改成「发布根路径按 gbrain slug 规则可解析」并像 DEF-002 一样登记未验证；(b) 明确发布根→CompanyBrain/gbrain 的登记步骤与触发时点
F-3 | blocking | full_release.py:1142-1154、37-43、166-173；ADR-0014（删除自证机器）；NG-005 | 「复用/改造 atomic_release」复用的是 Task5 自证栈：入口 `release_decision(...)!="released"` 依赖 `PreparedFullRelease`/`SummaryConfirmation`，「完整包」判据 `_FORMAL_ROOT_REQUIRED_PATHS` 还要求 `reports/projection-report.json`、`reports/exit-manifest.json`——正是 ADR-0014 要删的自证产物；而真实 K1 批次布局（README+products+_audit）永远判 invalid | 只搬「两次 os.replace + 失败恢复」机械；另建 K3 前置（candidate=K1 `not_released+complete` 且 K2 `generated_ok`；formal 完整性＝发布根自己的结构声明）；`release_decision`/`SummaryConfirmation`/`_FORMAL_ROOT_REQUIRED_PATHS` 明写不复用
F-4 | blocking | full_release.py:1225-1232 | 「整库原子」实为两步 rename：1226 先把 formal 挪走、1228 才把 stage 挪进来，中间该路径**不存在**；换进来后还要读回全树哈希+校验（1230-1232），失败才回退 → 未被判定合格的新版本已对读者可见 | 用一次原子交换（macOS `renamex_np(RENAME_SWAP)` / Linux `renameat2(RENAME_EXCHANGE)`），或在发布根外放稳定入口（`current` 指针）供读者/检索层只认入口；读回校验必须在切换前对 stage 完成
F-5 | blocking | full_release.py:1219-1276（成功路径 restored 恒 False）；tests/acceptance/test_task3_quality_release.py:885 | 「保留最近 1 版」落不了地：成功时 `.task3-rollback-<uuid>` 不删、每次发布新增一个、名字是随机 UUID，既无裁剪也无「谁是最新」的指针 → 磁盘无界增长，「一条命令回滚」不知道回哪版 | 加确定性 LKG 指针（固定名目录或 `.kd-lkg` 记录 tree_hash+路径），发布成功在同一把锁内裁剪到 1 版；回滚命令只读该指针且与发布共用锁
F-6 | blocking | OI-05；AC-K3-3；OI-13（允许修 K1/K2） | 三份冻结物不含「本次被验收的批次/发布树哈希」，而范围又允许边验收边修 K1/K2 → 判定记录不与具体产物绑定，「机器重放逐题一致」可在另一份产物上成立，改到通过无法被发现 | 冻结物加「候选批次树哈希 + 发布根树哈希」，逐题记录回写这两个哈希；任何 K1/K2 修复产出新批次并强制全量重跑、旧记录作废
F-7 | major | OI-04；publisher.py:113；full_release.py:1249-1267、1278-1281 | 「失败三项真实非 null」在所选链路上没有落点：atomic_release 失败只写无耗时/调用/token 的 failure json；commit 的 quarantine 把 `observed_calls` 硬编码 null；锁争用被 1278 行吞成 not_released，连原因码都不留 | 定唯一失败收据写入器，复用 K1 FR-AUD-005 词表（耗时/provider_calls/token/cache_hits/blockers）；发布步骤 0 次调用写 `no_provider_call_yet`；not_released 必带 reason_code；锁争用单列 `release_lock_busy`
F-8 | major | full_release.py:1196-1218；semantic_audit.py:835-837 | 发布状态有两个互不认识的账本：K1 manifest `publish_status`（`build_audit` 直接 `raise ValueError("...use not_released")`）与发布根 `digest_release_status`/receipt；回滚后谁改回 not_released 未定义 → 批次说 released、发布根是旧版 | 指定唯一权威（建议只落发布根）；批次 manifest 恒 `not_released` 不当发布账本；spec 写死回滚对两处账本的处理与对账检查
F-9 | major | OI-06 open；AC-K3-3 | 「四结果逐题判定 + 机器重放逐题一致」没定评委：模型判则版本/采样一变重放不一致；脚本判则「答案命中」没有可执行定义；评委身份与判据未冻结 | 「定位有效/出处正确/对照未覆盖」做成纯机械判据（89 份输入指纹+行区间）；「答案命中」用模型但强制记录 prompt/模型/参数/响应哈希并允许缓存重放；评委身份进冻结清单
F-10 | major | OI-09；AC-K3-4；F-001 快照（release4 已确认在盘） | 「不冤枉好」的「好」由谁定义没写：手搓好样本只证明脚本会跑；oracle 若就是 CompanyBrain（参赛方之一）则仍是循环；坏样本手搓则任何问题集都能查到 | oracle 固定为 89 份输入的指纹+行区间；坏样本用真 release4（0 表格、95/99 同质入口）；双向验证必须留坏/好两侧统计
F-11 | major | OI-05；CompanyBrain `_gbrain/pages`（509 文件）；release4 含 `.DS_Store` | 整树快照会把 gbrain 生成镜像 `_gbrain/pages/**`（每次 sync 重写）和 `.DS_Store` 冻进去 → 清单重算必然对不上，「冻结 ID 由清单确定性导出」不稳定 | 冻结定义写排除项（`_gbrain/`、`.`开头）；只对正式知识层（task4 口径 838/716）取哈希；记录排除规则本身；快照整树 `chmod -R a-w` 让「不可变」可检查
F-12 | major | OI-13/Q7；`/Users/Hugh/Downloads/KD测试` 实测为空 | 「先记录再修」没有额度与停止规则；且磁盘上没有真实 K1 批次，验收必须先真跑一次 89 份 provider 编译，这步成本/失败归因不在本卡成本口径内，暴露缺陷后「修 K1」极易变成重做 K1 | 缺陷台账+硬上限（只修「使批次无法发布」的阻塞级，不动页面语义/导航生成）；修复即产新批次并全量重跑；把真跑一次 K1/K2 的 provider 成本写进计划与 AC-K3-2 分母
F-13 | major | full_release.py:1172-1174；publisher.py:66-70；lock.py:14-35 | 并发保护不统一：atomic_release 锁 formal 的**父目录**，commit 锁 `.{name}.lock`/`task5.lock`（O_EXCL），两套互不排斥；flock 仅同机同 FS 有效；回滚/裁剪用哪把锁未定 | 一个发布根一把 realpath 规范化后的锁，发布/回滚/裁剪共用；锁记录 run_id/pid/host，残留锁显式报错而非静默 not_released；跨机/NFS 并发写进限制
F-14 | major | full_release.py:1193；无 statvfs/ENOSPC 预检；实测磁盘余量 160Gi/单库 14M | 每次发布整库复制，成功后旧版又不裁剪（F-5）→ 峰值最多 3 份整库；ENOSPC 时 copytree 的 OSError 被 1278 行吞成 not_released，无原因码无成本记录 | 发布前 `shutil.disk_usage` 预检（≥2×树+余量）给 `release_no_space`；先裁剪后复制使峰值≤2 份；失败收据落 cost/reason
F-15 | major | full_release.py:1226-1228；发布根读者=Obsidian | 未考虑发布时读者/编辑器正打开着发布根：整个目录被 rename 走再换进来，编辑器仍持有旧 inode，切换瞬间保存的编辑落进 `.task3-rollback-*`，随后被「只留 1 版」裁剪删掉 → 用户改动静默丢失 | 发布根定位为只读交付区（结构声明+文档写死禁止编辑），读者入口用稳定指针指向带版本目录；裁剪前检测 rollback 副本内的新增/修改并显式报错而非删除
F-16 | major | full_release.py:1241；packet 事实 27；PRD FR-K3-1「回滚可查性不中断」 | 回滚只 rename 文件树，检索层索引不回退：发布后 gbrain 已按新 slug 建索引，回滚后这些 slug 指向不存在的文件（或继续返回被撤下的坏页）；方向把 gbrain 排除在外，这句验收无人能证 | 回滚验收加「检索侧状态」：要么给出「回滚后必须重跑 gbrain sync」的显式命令与成功判据，要么把可查性缩到「发布根内路径可解析」并登记降级
F-17 | major | PRD FR-K3-1:84；K1 PFACT-003（gbrain slug 删全部非 ASCII、同 slug 按导入覆盖、root 名不影响 slug） | 写权边界是文件系统边界，gbrain 是**按 slug 覆盖**的索引边界：发布根登记进 gbrain 后，`products/emm/foo.md` 会顶掉 CompanyBrain 同 slug 的检索结果——一个字节没写 CB，却改了它的可查性；方向四类负例不覆盖这种索引层混合 | 发布前对「CompanyBrain 冻结快照 + 发布根」做 slug 合并冲突模拟，冲突即 fail closed；不可避免时给发布根 slug 加命名空间前缀，并把冲突列为 AC-K3-1 第 5 类负例
F-18 | minor | OI-03/Q3；AC-K3-2 reason 词表 | 「保留 1 版＝占一份额外磁盘」与实现不符（见 F-5 实为每次一份）；「回滚期间可查性不中断」与「只留 1 版」在并发时争同一个 rollback 目录 | 把「发布 N 次后 rollback 目录数恒为 1」「回滚与裁剪不互相破坏」写成机读断言，不停留在叙述

## Counterexample（最强 5 条，均可复现）

C-1（对应 F-3）：用现有 `atomic_release` 跑第二次发布。formal 已是 K1 批次目录 → `inspect_formal_root` 缺 `bundle/index.md`、`bundle/README.md`、`audit/source-manifest.json`、`reports/projection-report.json`、`reports/exit-manifest.json` → `status=invalid`、`protected=False` → 直接 `not_released`。「发布一条、回滚一条」从第二次发布起永久失败。
C-2（F-4）：gbrain 全量 sync 与发布并发。它按路径边走边读，前半读到旧 inode、后半读到新 inode → 索引里同一产品半新半旧，正是 AC-K3-1 判失败的「混合版本」。
C-3（F-2）：发布根 100% 通过验收，gbrain 里一条 KD 页面都搜不到；用户问产品问题仍只得到 CompanyBrain 旧页 → T-002=A「可替代 CompanyBrain」未达成，而验收报告全绿。
C-4（F-6）：第 1 轮验收 3 题失败 → 顺手改 K1 产品归属 → 第 2 轮全过；两次判定记录都「逐题一致」，但第 2 次是另一份被改过的产物，K1 验收结论被悄悄改写。
C-5（F-5）：连发 5 次 → 父目录 5 个随机 UUID 的 `.task3-rollback-*`，回滚命令只能靠 mtime 猜，猜错回到更旧版本；磁盘占满后下一次发布 ENOSPC 失败且无记录。

## 总结（≤500 字）

**blocking 条目：F-1、F-2、F-3、F-4、F-5、F-6。**

方向本身能落地的只有「整库为单位换版」这一条大原则；6 条 blocking 里有 4 条是**机制自相矛盾**，2 条是**验收自证**，按现态进 spec 会产出一个绿的但没用的结果。

最关键三条：
1. **F-2「真的交出去」落空**。独立发布根 + gbrain 零触碰，使 FR-K3-1 的 gbrain 子句与 FR-K1-3 的「gbrain 可检索」都没有任何验收步骤能证明；OI-11 的反例只保护「不写 CompanyBrain」，方向包却把这条列为已收敛。必须明确：本卡交付物是否止于发布根，以及发布根何时、以什么步骤进入检索层。
2. **F-3 复用点选错**。`atomic_release` 的自证栈与「完整包」判据（依赖 K4 要删的 `projection-report.json`/`exit-manifest.json`）正好是 ADR-0014 删掉的东西；且它对 K1 批次布局必然判 invalid —— 现有测试全部是 Task5 bundle 形状，未覆盖 K1 批次形状。要么只搬 rename 机械，要么先说清新的 formal 判据（OI-12 目前 open）。
3. **F-4/F-5 发布安全承诺不成立**。「原子」实为两次 rename 中间有路径缺失窗口，且校验在切换之后；「保留 1 版」实为每次发布留一份、无 LKG 指针、无裁剪。AC-K3-1「只见完整版本 + 一条命令回滚」按现实现无法通过。

次级但同样会误判：F-6（判定记录不绑定产物哈希＋允许边验收边修 K1/K2＝改到通过）、F-7（失败成本无落点、锁争用被吞）、F-17（索引层 slug 覆盖＝写权边界被绕过）。

建议：F-1/F-2/F-3 必须由用户重新裁决后再写 spec；F-4/F-5/F-6 需在 spec 里给出可机读判据与负例，否则 AC-K3-1/AC-K3-3 不能声明通过。
