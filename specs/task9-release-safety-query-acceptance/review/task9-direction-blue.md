# task9 / K3 方向审查 · 蓝队（构建性：可实施性 + 完整性）

范围：审查已收敛方向（packet 第 9-18 行）对母任务 K3 的 5 条 FR/AC、S2/S5/S8 与 K1/K2 交接接口的覆盖。只读取证，未改仓库。
取证基线：`full_release.py`、`publisher.py`、`semantic_audit.py`、`semantic_nav_check.py`、`semantic_cli.py`、`semantic_navigation.py`、`semantic_compiler.py`、`config/task0-question-set.v1.json`、`config/task4-question-oracle.v1.json`、K1/K2 spec 与母任务 PRD/decision-log、磁盘事实。

## 逐条核对（FR/AC 覆盖结论）

- FR-K3-1 原子发布与回滚：**不足**。切换本身可用（`atomic_release` 两次 `os.replace` + 读回校验 + 失败自动恢复），但「保留最近 1 个可回滚版本」「一条命令回滚」没有落点（B1）；发布单元与既有实现的前置不匹配（B2）。
- FR-K3-2 失败显式化与成本度量：**不足但可补**。K1 已有精确词表（`_metrics`，reason=cache_hit/no_provider_call_yet/provider_unavailable），发布/切换失败路径完全没有任何成本三元组（M1）。
- FR-K3-3 判定记录可复跑：**不足**。判定记录载体、逐题四结果的可执行定义、汇总通过条件全是「待 R3」（OI-06 open），且判据两侧只有三份冻结物、没有冻结「新产物」侧（M2、B3）。
- FR-K3-4 问题集有效性：**方向对、来源错**。双向验证（能查坏产物 + 不误判正确结果）是对的，但「从资料自动生成题目」与 ADR-0014 / OPEN-002 冲突，且会系统性削弱可区分度（M3）。
- FR-K3-5 冻结物齐备：**部分缺载体**。89 份与 release4 在磁盘上真实存在（已验：89 份 md、`/Users/Hugh/Downloads/KnowledgeDigest-task5-m402-20260908.release4` 108 md），但 CompanyBrain 的「snapshot ID」在方向里没有载体，也没有「齐备即拦下验收」的前置检查（M4、m1）。
- S2/S5/S8 与 K1/K2 交接：S5 的「读者与 gbrain 只见完整版本」没有可观察对象定义（M5）；K1 交接（`page-manifest.json`）与 K2 交接（`navigation`）被引用但**取值边界未冻结**，且 `publish_status=released` 的写入方在代码里被明确禁止（M6）。

## Findings

B1 | `full_release.py:1142-1273`（stage/rollback 命名 1196-1197、finally 1269-1273）| packet 第 3/21 行说 `atomic_release`「支持保留旧版」，实际上它把旧版丢在随机名 `.task3-rollback-<uuid>` 下、既不建指针也不清理（成功路径 `restored=False`，所以不删），既没有「最近 1 个 last-known-good 槽位」，也没有任何一条回滚命令能确定性找到它；发布 N 次就攒 N 份整库副本 | 方向必须明确：last-known-good 用固定路径（如 `<publish-root>.lkg/`）+ 一份指针记录（含 tree hash、被替换版本 hash、时间），成功发布后把旧 LKG 轮换掉；回滚命令只读指针、按 hash 校验后整包换回，并在锁内完成。

B2 | `full_release.py:37-43,145-178,268-312`；`publisher.py:33-56,189-190` | 现有两条发布路径都不能直接承载「整库原子 + 新独立发布根」：`atomic_release` 硬要求 formal root 是 task3 bundle（`bundle/README.md`、`bundle/index.md`、`audit/source-manifest.json`、`reports/projection-report.json`、`reports/exit-manifest.json`），还要求一份 24 小时内的 `SummaryConfirmation` 绑定 task3 release-summary；`publisher.commit` 相反，要求目标不存在或为空且不留旧版。K1/K2 产物是「页面 + Home/Index + `_audit/`」，两者都不满足 | 复用前必须先落一个决定：把 `atomic_release` 的必需路径与「发布确认」参数化（或抽出只做「复制→校验→锁内两次 replace→LKG 轮换」的核心），否则等于为了复用去复活 ADR-0013 已明确废除的 bundle 形态，并顺带把 OI-02 已否决的人工确认闸门带回来。

B3 | `decision-log.md:283-314`（OI-06/OI-08）；母任务 PRD K3 表 FR-K3-3；`docs/adr/0014` | 「谁在什么时候触发一次验收」至今没有答案：J6-J8 只有角色名，没有触发命令（发布前/发布后/K4 合并后？）、没有判定记录落盘位置、没有「结论是否阻塞合并」；更关键的是 FR-K3-3 要求的「汇总通过条件可执行」在任何材料里都没有阈值——同一份逐题记录，判「通过」还是「失败」取决于人怎么解释，AC-K3-3 的「机器重放逐题一致」因此在汇总层直接不成立 | R3 必须冻结三件事并写进验收标准：①触发点与命令（建议 `digest publish` 之后跑 `digest accept --question-set <frozen> --frozen <3 份清单>`，产出 `acceptance/<run_id>/verdict.json`）；②汇总规则（逐题四结果如何合成 pass/fail，例如「答案命中且出处正确占比 ≥ 冻结阈值，且『对照未覆盖』不计入分子；任一硬失败题为 fail」）；③门禁语义（谁来读这个 verdict，是否阻塞合并）。

M1 | `publisher.py:96-132`（111-113 硬编码 null）；`full_release.py:1247-1263`（失败 JSON 只有 reason/rollback_path/old_package_hash/install_error）；对照 `semantic_compiler.py:1383-1421` | FR-K3-2 指定的「发布/切换失败运行」这条路径上，耗时/调用数/token 三个字段连容器都没有：`publisher.quarantine` 的 failure.json 硬编码 `observed_calls/provider_identity/audit_ref = null`，`atomic_release` 的 failure JSON 只有原因与回滚路径。K1 已有一套可用词表（`_metrics` + reason 三值 + `_audit/run-metrics.json`），但只在编译路径生效 | 发布命令在启动时就开一份 run 记录，成功与失败共用同一 schema（`elapsed_ms/provider_calls/provider_tokens` + `reasons`），失败路径从同一处写；删掉硬编码 null，改由调用方注入真实计数；「真 0 带 reason」的校验器复用 K1 的 reason 词表，避免出现第三套词表。

M2 | packet 第 13 行；`full_release.py:296`；`semantic_compiler.py:341-342` | 判据只冻结了「输入 89 份 + 改造前产物 + 对照库」三样，没有冻结被验收的**新产物**侧。反例：第一次验收判定 12/20 命中，然后把发布根重新发布（或回滚 LKG）再重放，三份冻结物一字未变、逐题结果却变了——AC-K3-3 的「同一问题集+三份冻结物下重放一致」无法复现 | 判定记录里把新产物侧也钉死：被验收根的 tree hash（或逐文件 sha256 清单）、问题集文件 sha256、判定器版本/口径 hash；重放时先按 hash 校验，不一致就明确报「被测对象已变，不可复跑」，而不是静默给出新结论。

M3 | packet 第 18 行；`docs/adr/0014`（Consequences：human-authored question set）；母任务 PRD OPEN-002；对照 `config/task0-question-set.v1.json`、`config/task4-question-oracle.v1.json` | 「从资料自动生成题目」不只是流程争议，它会直接打穿 FR-K3-4：题目来源与被测内容同源，自动生成天然偏向「照原文能答」的问题，最可能的结果就是 AC-K3-4 要防的「全过」；在已知坏产物上做双向验证只能证明「题库能查坏产物」，不能证明题目代表真实读者需求。反例：自动生成的 20 题全部是「X 是什么/怎么用」，坏产物只需保留标题与首段即全过，好产物与坏产物不可区分 | 维持 ADR-0014 口径：题目由人出（或模型起草、人逐题确认后冻结），冻结时记录出题人与冻结 hash；自动生成只能作为候选池。机制可复用已有资产，省一半工作：沿用 `task0-question-set.v1.json` 的 schema/hash 规则与 `task4-question-oracle.v1.json` 的「每题期望页 + answer_terms」oracle 行，只丢掉五维比较/证书那一层。

M4 | packet 第 5 行；母任务 S2③（「记录其 ID」）；磁盘事实：CompanyBrain 1347 md，`/Users/Hugh/Hugh/Knowledge/CompanyBrain` 无任何快照/ID 记录 | 方向对三份冻结物都只说「内容快照 + 逐文件 sha256」，没有说冷冻副本放哪、清单与冻结 ID 写进哪份文件、验收记录如何引用它；S2 明确要求的 CompanyBrain「snapshot ID」在方向里没有对应物。反例：出题时读的是今天的 CompanyBrain A，判定时用户手改了几页变成 B，对照侧内容悄悄变了，而「对照未覆盖不计我方优势」这句话无法被审计 | 冻结脚本产出 `freeze/<frozen_id>/manifest.json`（三份冻结物各自的根路径、文件数、逐文件 sha256、汇总 tree hash、frozen_id=清单内容推导）并与快照内容一起放在不可变目录；验收命令把 frozen_id + 三份 tree hash 写进 `verdict.json`；齐备检查做成验收的前置门（缺一即 blocked，不产出任何逐题结论）。

M5 | packet 第 10/15 行；母任务 S5 与 AC-K3-1（「读者与 gbrain 只见完整新版本或完整旧版本」）；`docs/adr/0013` | 方向把发布目标改成独立发布根，但没有定义 AC-K3-1 的**观察对象**是谁：gbrain 现在读的是 CompanyBrain（ADR-0013 的语义层），独立根它根本看不到。反例：四类负例全跑完，「读者与 gbrain 从未见到半成品」成立，但那是因为它们从来什么都没看见——这条 AC 被真空满足，负例验证失去意义 | 在验收标准里写死观察口径：负例注入期间与之后，以「发布根路径」为观察对象做断言（整根要么等于旧 tree hash 要么等于新 tree hash，逐文件比对），并明确 gbrain/读者接入独立根是 DEF-K3-2/DEF-K3-3 的延期项、本卡只用「发布根内容完整」与其等价替代。

M6 | `semantic_audit.py:829-838`（publish_status=released 直接 ValueError）；`semantic_nav_check.py:607`；K2 spec SCN-K2-008 与状态覆盖清单（generated_ok/blocked）；`semantic_cli.py:183-184`（只判 `!= blocked`）| K1/K2 交接接口被引用但取值边界没冻结，两处会漏：①`navigation_status` 词表是 generated_ok|blocked，而 `semantic_cli` 的放行判断是「不等于 blocked 就继续」，照抄这个写法会让缺字段或异常批次混过去，必须写成「显式等于 generated_ok 才放行」；②`publish_status=released` 保留给 K3，但写 manifest 的权威入口 `write_audit` 明确禁止 released，方向没说 K3 由谁、在哪个文件里做这次状态转换（直接改 manifest？还是另出一份 release receipt 不动 manifest？） | 发布前置条件写成字段级白名单（`run_status == complete` 且 `publish_status == not_released` 且 `navigation.navigation_status == generated_ok` 且 `blockers` 为空数组），缺任一即 blocked 并写明 reason；同时冻结「谁写 released」：建议不动 K1 manifest 的既有语义，K3 在自己发布根写 `releases/<release_id>/release-manifest.json`（引用批次 manifest 的 attempt_id + hash），manifest 回写作为可选记录并在规格里写明由 K3 拥有。

m1 | packet 第 5 行；`full_release.py:1174-1190` | FR-K3-5 的「齐备检查」在方向里只是一个愿望，没有命令/门禁位置；`atomic_release` 每次调用都自己重算 `_tree_hash(candidate)`（整库读一遍），若验收也各算一遍，整库会被反复全量哈希 | 把「冻结齐备 + 三份 hash 复算」做成验收命令的 preflight（一致才允许出逐题结论），并在同一次运行里缓存 tree hash 结果供发布与验收复用。

m2 | packet 第 8 行；`tests/acceptance/test_task3_quality_release.py:815-875` | 「已知坏产物」这个区分度基线在方向里没有定义：谁造、造几类、放在哪。没有它，Q9 选的「双向验证」在 build 阶段无法落地，容易被简化成「跑一遍没全过就算有效」 | 把坏产物 fixture 固定成一小套可复算样本（例如「缺表格的页」「错出处链接的页」「无入口的孤儿页」三类，各带期望判定），随冻结物一起入库并登记 hash，区分度检查直接对这套样本跑。

m3 | `full_release.py`（grep fsync 零命中）vs `publisher.py:157-215`（逐文件 fsync + fsync 目录）| AC-K3-1 的四类负例都是「进程内异常」，没有覆盖进程被杀/掉电：`atomic_release` 全程不 fsync，第一次 replace 与第二次 replace 之间崩溃可能留下 formal 缺失或 stage 未落盘的中间态 | 若把「写入中断」理解到崩溃级别，需要在复制后 fsync 暂存树与文件、两次 replace 前后 fsync 父目录（可参照 `publisher.commit` 的做法）；若决定不做崩溃级保证，就在验收标准里写明只覆盖异常注入，别让 AC 措辞含混。

## 总结（≤500 字）

方向的主干是对的：整库原子、锁内切换、失败自动恢复、独立发布根、三份冻结物带 sha256、失败成本必须真实非 null，这些都能在现有代码里找到落点，不必从零造。但按当前文字直接开工，会在三处卡死。

**blocking：B1、B2、B3。**

- B1（最要紧）：说好的「保留最近 1 个可回滚版本 + 一条命令回滚」在代码里不存在——`atomic_release` 把旧版丢在随机名 `.task3-rollback-<uuid>` 下、不建指针也不清理，回滚命令无处可查。FR-K3-1 的两条 AC（回滚可用、只见完整新旧版本）都挂在这上面，必须先定 LKG 固定槽位与指针。
- B2：现有两条发布路径都接不上：`atomic_release` 要求 task3 bundle 五个必需文件 + 24 小时内的人工确认记录，`publisher.commit` 要求空目录且不留旧版；直接复用等于复活 ADR-0013 已废除的 bundle 形态，还会把 OI-02 否决的人工闸门带回来。
- B3：「谁在什么时候触发一次验收」和「汇总通过条件」仍是空的（OI-06/OI-08 open）。没有触发命令与阈值，FR-K3-3 的「机器重放逐题一致」在汇总层不成立——同一份记录可以被判成通过也可以被判成失败。

另两处必须同时修，否则 AC 会被真空满足或不可复跑：M2（只冻结三样、没冻新产物，重放不可复现）与 M5（观察对象未定义，负例下「读者与 gbrain 只见完整版本」因为没有可见对象而自动成立）。

M3 的自动出题建议在 R3 明确回退到「人出题 + 冻结 hash」，机制可复用 `task0-question-set.v1.json` 的 schema/hash 与 `task4-question-oracle.v1.json` 的 oracle 行，成本不高。
