# task9 build-plan 蓝队审查（完整性）

- 审查对象：plan.md（`aefa29db…`）、tasks.md；上游 spec.md（frozen `1dd9fad1…`）、decision-log.md（approved）只读。
- 蓝队范围：29 条 FR 卡承接、AC-K3-1…5 oracle 卡、plan-task.v4 必填字段、traceability 一致性、D-001…D-013+D-004b 入卡。
- finding 行格式：severity | 位置 | 问题 | 建议。

## Findings

major | plan.md「Requirement and Verification Traceability」表 | 卡号系统性错位：白名单行挂 T002R/G+T003R/G（T002 实为 tree hash，白名单只 T003）；合并行挂 T004R/G（T004 实为 sidecar/锁）；入口/LKG 行把回滚挂 T008R/G（T008 实为 no-op，回滚在 T010）；no-op 行挂 T009R/G（T009 实为收据）；收据行挂 T010R/G | 按 tasks.md 实际卡号重排该表；build-code 按表找 gate_cmd 会被送去错的 `-k` 选择子，误导执行。

major | tasks.md FR-ACC-006（验收并发与锁） | 无任何卡断言「accept 取与发布/回滚同一把库级锁、取不到不得读到换版中间态」：T004 锁卡只覆盖发布侧争用，T013 只测冻结只读边界，T017R 不测锁；仅 T017G 动作里有一句「锁内读指纹」无可执行 oracle | 在 T013R 或 T017R 增加锁断言（持锁时 accept 阻塞/报错 + 不得读到中间态），并在 plan traceability 表给 FR-ACC-006 补一行；这是 frozen FR 且挂 AC-K3-1/AC-K3-3，零卡承接属覆盖漏洞。

minor | tasks.md FR-STA-001 / FR-COST-003 | 两条 FR 无卡承接：FR-STA-001（五类状态沿用 K1、台账逐字节复制、「资料未明确」不进分母）只在 T005 字节相等断言沾边，「不进分母」无验收侧断言；FR-COST-003 要求「验收引用 F-002 实物基线（release2/release3 failure.json）作对照」未落到任何 oracle | T005 oracle 补「发布后库内来源台账与批次逐字节一致」断言；T011 oracle 补 F-002 基线引用登记（哪怕只登记路径+sha256 到记录字段）。

minor | tasks.md FR-ACC-001 | 「独立验收命令」无显式卡/行：现散在 T001（入口）与 T017G（accept 编排），traceability 表无 FR-ACC-001 行 | 在 T017 卡 FR 字段显式列 FR-ACC-001，traceability 补行，防 build-code 漏掉「不在发布时自动运行」的边界断言（T021E2E 可顺带断言发布流程不触发验收）。

minor | plan.md Quick Read 行 20 vs tasks.md | plan 称「六阶段 26 个行为对」，tasks.md 实为 21 对 RED/GREEN（T021 即聚合对，packet 口径同为 21 对+1 聚合）| 统一口径为 21 对；数字漂移会让执行者怀疑漏卡而回头排查。

minor | tasks.md 全部卡 | plan-task.v4 必填字段不齐：仅 T001R 具备全字段；T002R–T021R 普遍缺 Phase、design_state（多数也缺并行）；所有 GREEN 卡缺 versioned_refs/source_refs/依赖/并行/FR/AC/精确文件，T002G–T021G 未写 gate_cmd（仅 T001G 写「同 T001R」）| GREEN 卡统一补 `gate_cmd：同 T<nnn>R` 并补 Phase/design_state/FR/AC；RED 卡补 Phase/design_state。卡片自身内容可用，属模板合规缺口。

minor | tasks.md T020R 依赖 | 只挂 T009，但「修复走新批次后旧判定记录标 void 且重放拒绝」依赖 T017 的判定记录绑定/重放机制；漏依赖在并行编排时可能倒序执行 | T020 依赖补 T017。

minor | tasks.md source_refs | D-001、D-003、D-007、D-010 四条 decision 无卡显式承接（仅 T021 聚合行写「D-001…D-013 全链」）：D-007（验收独立命令）最自然落点是 T017，D-010（不复用旧入口）已落 plan Code Anchors 但卡级未挂 | 在 T017 source_refs 补 D-007，范围级决策（D-001/D-003/D-010）在 traceability 表显式标注「归 T021 聚合」，避免被误判为沉默丢弃。

## 总结（≤500 字）

29 条 FR 中 24 条有卡承接且 oracle 可机读，AC-K3-1…5 全部有 oracle 卡（AC-K3-1=T007/T010/T019，AC-K3-2=T009/T011/T020，AC-K3-3=T015/T016/T017，AC-K3-4=T018，AC-K3-5=T012/T013），六阶段依赖链 P1→P2→P4→P5→P6 与 plan 声明一致，无执行性死锁；D-004b/D-005/D-006/D-008/D-009/D-011/D-012/D-013 均已挂到具体卡。真正的覆盖漏洞是 FR-ACC-006（验收同锁）零卡零 oracle，frozen FR 级缺口，列 major；plan.md traceability 表卡号对不上 tasks.md 实际编号（白名单/合并/入口/回滚/no-op/收据六行错位），列 major，其余为模板字段缺漏与口径小漂移（26 vs 21 对、GREEN 卡缺 gate_cmd、T020 漏依赖 T017、FR-STA-001/FR-COST-003 无卡），均可低成本修复。blocking 编号：无（0 条）。本审查为 advice 不是 pass 门，build-code 可在补表与补锁断言后直接开工。
