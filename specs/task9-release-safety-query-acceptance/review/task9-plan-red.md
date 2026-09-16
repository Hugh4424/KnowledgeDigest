# 红队审查 · task9 build-plan（plan.md + tasks.md）

- 输入：`kd-task9-plan-packet.md`；审查对象 plan.md / tasks.md；上游 spec.md（frozen）/ decision-log.md 只读对照。
- 性质：advice，不是 pass 门。宁少而真，共 11 条 finding（blocking 2 / major 3 / minor 6）。

## Findings

blocking | plan.md DEC-K3-002（Solution Design/Technical Decisions）| plan 把"允许写范围"从 spec FR-PUB-002 的"`kb.structure.md` 声明的托管路径+库级结构页/索引页"悄悄扩成"骨架声明 ∪ 本批 manifest 页面集"，即批次页面即使未被骨架声明也自动可写 | 这是把 spec §10"默认必须成立"的硬失败边界（SCN-K3-005 越界写入=blocked）放松了：按 plan，一个落在两集合之外但出现在 manifest 的页面不再算越界。spec 明确"只能引用执行、不得改口径"。要么回 make-decision 增量裁决，要么让骨架声明真正覆盖 products/ 布局（如发布时把 manifest 页面登记进 kb.structure.md 声明再判定），并把判定顺序写进卡。

blocking | tasks.md T012G / plan.md File Boundary | freeze() 实现了"三份冻结物"但没有任何入口能调用它：pyproject 只注册 publish/rollback/accept 三个脚本，accept 入口输入已是 freeze 目录或 frozen_id；T017G accept() 编排也不含 freeze | FR-FRZ-001…005 在真实环境不可执行，verify-code 全链路第一步就断。plan 必须显式给出 freeze 的调用形态（第四个命令、accept 的子模式或独立函数+脚本），否则 build-code 只能猜。

major | plan.md Traceability 表 + tasks.md 全卡 | FR-ACC-006（验收取与发布同一把库级锁，取不到不得读中间态）没有独立卡，traceability 表也未列；只在 T017G 动作里出现"锁内读指纹"半句话，无 RED 断言 | 补一对 RED/GREEN（或并入 T017R 并写明 oracle：锁被占时 accept 报错/等待且不产出指纹），并把 FR-ACC-006 写回 traceability 表。

major | plan.md Traceability 表 | FR-STA-001（五类状态台账逐字节复制、"资料未明确"不进事实分母）无卡承接、表中缺席；T005R 的逐字节断言只覆盖 products/** 页面，未点名来源台账的复制与不改写 | T005 或新增卡补台账（_audit 下来源清单）逐字节复制断言；至少把 FR-STA-001 挂到 T005R/G 并在 traceability 表登记。

major | plan.md Traceability 表 vs tasks.md | 表内卡号过期：FR-PUB-001 白名单写成 T002R/G、T003R/G，实际 T002=tree hash、T003=白名单；FR-PUB-004/005 的"回滚"标 T008R/G，实际 T008=no-op、回滚=T010；T009/T010/T011… 全部错位 | 按 tasks.md 现行编号重排 traceability 表；executor 按表索引会读错卡，这是可执行的依赖错误源。

minor | plan.md Quick Read | "六阶段 26 个行为对"与 tasks.md 实际 21 对（T001–T021）不符；packet 摘要也称 21+1 | 统一数字。

minor | plan.md DEC-K3-005 vs spec.md SCN-K3-004 | staging 落点 plan 冻结为 `.<KB>.kd/staging/<run_id>/`，spec 机器判据措辞是"无本次 `staging-<run_id>` 残留"；spec 虽把目录名归 build-plan，但判据字符串需与冻结布局逐字对齐，否则 SCN-K3-004 断言写不出来 | 在 plan 里给出 SCN-K3-004 判据的最终机读措辞（按 sidecar 布局改写）。

minor | plan.md DEC-K3-003 | `current` 符号链接未指定相对/绝对目标。绝对路径在库目录被移动/改名时即断，且把机器路径泄漏进 vault；Obsidian 对 vault 内相对符号链接的跟随是方案成立的前提，plan 未验证也未写明 | 明确用相对目标（`../.<KB>.kd/versions/<vid>`），并在 T007R 断言 os.readlink 结果为相对路径；补一条 Obsidian 实测记录（哪怕人工）。

minor | plan.md Module responsibilities / T019R | "协作式取消"需要信号接入点，kb_publish 职责与 publish() 流程均未提信号处理；CLI 一次性命令收到 SIGINT 时检查点如何触发未定义 | 在 DEC 或 T019 动作里写明取消信号→检查点抛 Cancelled 的机制与测试注入方式。

minor | tasks.md T001R | RED oracle 是"三脚本入口存在、`--help` 可执行"，但 console script 由 pyproject 注册后需 uv 环境 re-sync 才生成；plan 未提这一执行步骤，且 RED 阶段"不改 pyproject"时该测试失败原因是环境缺脚本而非行为缺失 | T001G 动作补"pyproject 改动后需 `uv sync`/重新冻结环境"一句；T001R oracle 改为直接调用 `kb_publish.main(["--help"])` 的进程内断言，脚本存在性作为附加断言。

minor | spec FR-COST-003（plan 无卡）| F-002 实物基线对照是 AC-K3-2 的证据引用，plan 无卡、verify-code 也未登记该对照步骤 | 在 T021R 或 verify-code 交接清单里补一句 F-002 对照读取的登记，避免 AC-K3-2 证据断链。（可接受为 plan 外，但需显式声明归属）

## 总结（≤500 字）

 plan 整体骨架可执行：复用边界清楚、DO NOT TOUCH 尊重、阶段依赖大体顺。但有两处 blocking 必须在 build-code 前处置：① DEC-K3-002 把允许写范围从"骨架声明"扩成"骨架∪manifest 页面集"，与 spec FR-PUB-002/§10/SCN-K3-005 的越界硬失败口径直接冲突——这不是命名级 plan 权限，是判定口径变更，须回 make-decision 或改为"发布时先把 manifest 页面登记进结构声明"；② freeze() 无 CLI 入口，三个注册脚本都不指向它，FRZ 五条 FR 在真实环境无法执行。三处 major 均为"可追溯性断链"：FR-ACC-006 无卡无 oracle、FR-STA-001 无卡、traceability 表卡号与 tasks.md 现行编号系统性错位（T002/T003/T008…），executor 按表索引会读错卡。minor 集中在工程细节：staging 判据措辞、current 链接相对性、取消信号入口、T001 console script 的 uv re-sync、数字 26 vs 21。 blocking 编号：B-1（DEC-K3-002 写权扩张）、B-2（freeze 无入口）。
