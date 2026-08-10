# plan-ceo-review 事实 — Task 2-A（advisory，只读）

## 五项检查

1. **用户问题与假设分离**：spec §3 只陈述问题（控制面不是读者产品、结构不稳则语义编译放大问题）；事实与假设全部进 PFACT（verified/inferred/unknown 分列）。§3 无推断混入。通过。
2. **最窄可行范围与既有杠杆**：范围被 D1 压缩为结构合同（正文归 2-B）；杠杆是复用既有 S1–S6、TopicIndex/ProductGazetteer 和官方 OKF parser。通过。
3. **与至少一个可信替代比较**：decision-log D1 拒绝「结构+正文」（语义门提前）、「只骨架」（验收 2/6/8 不满足）；D2 拒绝「直接 OKF-inspired」（验收 8 不满足）。spec §2/§12 继承这些取舍。通过。
4. **会推翻方向的失败前提**：外部 parser 无法固定版本 → 自动降级 OKF-inspired（FR-SMOKE-002）；入口门禁不过 → backfill + not_released（FR-ENTRY-001）。两个前提都有已冻结的失败路径，不会静默失败。通过。
5. **时机、影响半径与推荐**：结构合同必须在 2-B 语义编译前冻结（否则 2-B 输出形态漂移）；影响半径是后续 2-B/2-C/3 全部复用 bundle 合同 + 现有 Reader 输出形态；推荐按本 spec 推进 build-plan。

## 结论

方向成立、范围最小、失败路径已冻结。无阻断项。
