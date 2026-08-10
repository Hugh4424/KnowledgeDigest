# spec-clarify 事实 — Task 2-A（build-spec 阶段）

## 分类结果

| 陈述类别 | 内容 | 处理 |
| --- | --- | --- |
| 上游锁定决定 | D1 只做结构合同；D2 承诺 OKF-compatible + 固定 parser + 失败降级；D3 fixture 用真实样本人工整理 | 全部原样继承进 spec（FR/AC 直接绑定），不改名、不再问 |
| 上游明确遗留 | OPEN-001 具体 parser commit（owner=build-code）；OPEN-002 具体样本片段（owner=build-code）；OPEN-003 Task1 receipt 冲突（owner=产品维护者，Task 3 前） | 按上游语义记录为 spec OPEN-01/02/03，不进用户决策队列 |
| 新歧义 | 无 | 见下方十维检查 |

## 十维完整性检查

| 维度 | 覆盖情况 |
| --- | --- |
| 用户旅程 | SCN-001..007 覆盖操作者（生成/入口/重复运行）、读者（归因反查）、维护者（round-trip） |
| 页面/表面范围 | Reader Bundle 布局（FR-BUNDLE-001..006）、豁免清单固定 |
| 数据和状态转换 | frontmatter 合同、三层状态、受管 hash、易变字段规则（FR-FRONT/FR-STATUS） |
| 成功边界 | AC-01..08 全部可判真假，带通过/失败条件 |
| 失败边界 | smoke 失败→降级、入口缺失→backfill+not_released、标题/描述无候选→degraded、无证据不写 verified/stale_after |
| 权限/角色 | N/A — 本地单写者、无权限体系；actor 约定（verified/human:) 已按 §6.9 冻结 |
| 集成和外部效应 | 外部 OKF parser smoke（零网络、固定版本）；不引入外部运行时 |
| 非目标 | §12 逐条继承 R-009 与 decision-log 拒绝方案 |
| 延期交接 | OPEN-01/02/03 带 owner、处理 Stage、关闭条件 |
| 验收/可观察证据 | 每条 AC 有验证方法、通过条件、失败条件、证据类型 |

## 独立变化检验

候选歧义逐一检验，全部落入「锁定决定」或「上游遗留」：

- 命名（OKF-compatible vs inspired）→ D2 已锁定。
- fixture 来源（真实 vs 虚构 vs 自动投影）→ D3 已锁定。
- 范围（结构 vs 结构+正文 vs 只骨架）→ D1 已锁定。
- `okf_version` 声明条件 → FR-BUNDLE-004/FR-SMOKE-002 由 PRD §6.9.7/8 直接派生。
- 具体 parser commit、具体样本片段 → 上游明示 build-code 决定（不影响合同形状）。

## 结论

- 无 material ambiguity：不需要用户决策卡。
- 跳过理由：所有会影响范围、验收、接口、数据、安全或运维的轴均已被 PRD §6.8/§6.9 冻结或由 D1–D3 真实用户回答锁定；两个 `unknown` PFACT（OPEN-01/02）是上游明确委托 build-code 的选材细节，不改变合同。
