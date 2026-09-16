# task9 / K3 计划审查包（build-plan review 输入）

## 审查对象（只读）
- `/Users/Hugh/Hugh/Project/KnowledgeDigest-task9-release-safety-query-acceptance/specs/task9-release-safety-query-acceptance/plan.md`
- `/Users/Hugh/Hugh/Project/KnowledgeDigest-task9-release-safety-query-acceptance/specs/task9-release-safety-query-acceptance/tasks.md`
- 上游（只读）：同目录 `spec.md`、`decision-log.md`

## 背景 30 秒
K3=发布通道+验收判定器。计划要点：两个新模块（kb_publish.py/kb_accept.py）+ 三个新 CLI 脚本；sidecar（库外同级隐藏目录）承载 versions/staging/lkg/releases/receipts/ledger/freeze；库根 `current` 符号链接作固定入口（rename 原子换）；tree hash 按 spec FR-PUB-008 新写；托管路径集=骨架声明∪批次 manifest 页面集；21 对 RED/GREEN 卡 + 1 聚合卡分 6 相位；全离线。

## 红队任务（对抗）
找：plan 与 spec/decision 的口径漂移；卡片 oracle 不可机读；RED/GREEN 对无法对应同一 gate_cmd；遗漏的 spec FR（29 条全覆盖吗）；DO NOT TOUCH 边界被悄悄突破；sidecar/符号链接方案在 macOS 的实际坑（Obsidian 跟随相对符号链接、rename 原子性、锁父目录与 sidecar 竞争）；阶段依赖错误导致无法执行。

## 蓝队任务（完整性）
逐条核对 29 条 FR 是否都有卡承接（列出无卡 FR）；AC-K3-1…5 是否都有 oracle 卡；plan-task.v4 必填字段是否齐（ID/Phase/design_state/versioned_refs/source_refs/依赖/并行/FR/AC/动作/精确文件/gate_cmd）；traceability 表与卡片一致性；decision 中 D-001…D-013+D-004b 是否全部入卡。

## 硬约束
只读不改；不调 provider；输出 finding 行 `severity | 位置 | 问题（大白话） | 建议`，severity ∈ blocking|major|minor；末尾 ≤500 字总结+blocking 编号；宁少而真；这是 advice 不是 pass 门。
