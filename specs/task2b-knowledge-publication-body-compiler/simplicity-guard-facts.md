# Stage-owned advisory fact: simplicity-guard

- **stage**: `build-spec`
- **trigger**: `simplicity_check`
- **subject**: 当前 `spec.md`
- **spec_sha256**: `c0edc9f4d7108a04d86be509e24a48328ecdffb82f2c12b779d3eafe52ada69c`
- **mode**: read-only advisory；不是 stage-result、provider verdict 或实现许可
- **result**: `pass`

## 四阶梯检查

- **P0 必要性**：Task 2-B 原始需求明确要求三类正文编译、section 影响判断、机器发布门和失败隔离，能力有直接需求依据。
- **P1 直接复用**：复用 Task 1 TopicIndex、Task 2-A Reader Bundle、现有稳定主题身份、来源/Claim 溯源和 Reader/Audit/Archive 分层。
- **P2 改造复用**：正文只向既有 Reader 容器补受控 section；影响闭包和整页兜底沿用既有状态/历史保护，不另建导航、证据或发布系统。
- **P3 最小新增**：仅新增 PRD 明确要求且现有职责未覆盖的 Structure Normalizer、PageDraft、OKF Concept Compiler 和 Publication Gate 行为；不新增数据库、图谱、调度器、永久候选队列、全局复制率硬门或 UI。

## 结论

当前规格未发现应删除的范围、重复建设或投机性长期能力；没有 finding。若下游新增不属于上述 P0–P3 证据的抽象，应删除或回到 make-decision，不得借 build-plan 补产品范围。
