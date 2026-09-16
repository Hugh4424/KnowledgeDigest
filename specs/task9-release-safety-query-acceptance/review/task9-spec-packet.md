# task9 / K3 规格审查包（build-spec review 输入）

## 审查对象
- 规格：`/Users/Hugh/Hugh/Project/KnowledgeDigest-task9-release-safety-query-acceptance/specs/task9-release-safety-query-acceptance/spec.md`（只读）
- 上游决策：同目录 `decision-log.md`（approved，只读）；K1/K2 spec 在 `specs/archive/task7-semantic-layer-compiler/`、`task8-entry-navigation/`（只读）

## 背景 30 秒
K3 = 发布安全 + 真实查询集验收。方向已定：整库原子换版+库根固定入口指针；合并规则=库内原有内容+本批新增/更新（未声明路径保留、碰撞硬失败、证据页逐字节复制）；LKG/指针/失败收据放库外同级隐藏目录；失败成本三项真实且承接编译侧；三份冻结物（89 份恰数/release4/对照库只读快照，排除 .DS_Store 与 _gbrain/）；问题集每模块 2 题×3 模板确定性生成；汇总=硬失败 0+命中率≥80%+未覆盖不计分；坏样本三类各绑 2 必失败题；no-op 允许；verify-code 真跑 89 份。不接 gbrain/检索层/既有库写入/人工闸门/LLM。

## 红队任务（对抗）
找会让 AC 真空满足、不可执行、或自相矛盾的地方：阈值 80% 的可判真性；"每模块 2 题"在模块划分变动时的稳定性；tree hash 断言与"未声明路径保留"的组合漏洞；LKG 轮换与 no-op 的交互；失败收据与"清单之外零写入"的边界；四结果判定的机器可执行性；任何与 decision-log 冲突或超出其范围的新 scope。

## 蓝队任务（完整性）
对照 build-spec 必交 10 项（速读目标/非目标与延期/场景含空错取消权限边界竞态/状态转换与可观察成功失败恢复/稳定 ID/FR 链 source+scenario+AC/AC 含方法 oracle 通过失败证据/边界接口实体数据生命周期/假设风险 unknown owner/显式排除与下阶段交接）逐条核对；核对每条 AC 是否有可机读 oracle；核对 16 个 OI 与 D-001…D-013 是否全部落到 spec；核对 C1-C5 答复是否被忠实冻结。

## 硬约束
- 只读，不改任何文件；不调用 provider；不写 review fact 之外的东西。
- 输出到指定文件，每条 finding 一行：`severity | 位置(节/FR/AC 号) | 问题（大白话） | 建议`；severity ∈ blocking|major|minor；末尾 ≤500 字总结+blocking 编号。
- 这是 advice，不是 pass 门；宁少而真。
