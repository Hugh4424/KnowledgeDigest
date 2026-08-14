# Task 3 phase review status

当前快照的独立只读复核提出过真实遗漏，已在本轮修复并补了负向测试：

- P1：semantic 验证重新绑定 Claim、来源和 trust events；Related 目标/locator 受约束；old-path split 不再静默覆盖；Task2-A 的 source_count 旧语义恢复。
- P2：质量 scorecard、source manifest、候选 run、Claim 来源链、状态投影和确认时效均重新绑定；回滚失败保留可操作备份说明。
- P3：入口对中间异常状态 fail-fast；JSON replay 不再升级为 released；Task3 comparison 支持实际候选根并绑定 run/bundle hash；CompanyBrain 无共享质量合同时保持 N/A。
- 本轮补漏：冻结题集原文/hash、逐题结果重算、页面 managed-content hash、来源/Claim trust fingerprint、manifest/config/provider/response replay、人工确认主体、comparison 三方结构和状态投影、特殊节点都已加 fail-closed 校验；semantic release 还要求外部冻结 source manifest 作为 `expected_source_manifest`，没有它就不能放行。最后补上了 comparison binding 的 `run_id/bundle_hash` 和三方 `saved_integrity` 非空结构门。

WorkflowHub provider phase review：已修正 `/Users/Hugh/.config/workflowhub/config.json` 中 `mini_task.design/implementation` 的错误 mode，`node skills/wh-review/scripts/wh-review-cli.mjs doctor` 实际返回 `status=ok`。随后按当前 Task3 资料重新调用 `verify-code`，真实返回 `incomplete`、`snapshot_or_material_identity_unavailable`，没有生成 attempt；当前 TaskHandle 没有绑定可审查的工作区快照。因此仍为 `unavailable`，没有把 pytest 通过写成独立 review 通过，也没有宣称 clean review。

本轮按同一 WorkflowHub `wh-review` 路径先做只读 doctor；第一次暴露 mode 配置错误，修正后 doctor 已通过；后续真实 review 因当前 TaskHandle 没有可绑定 workspace identity 而返回 incomplete。随后做了边界清晰的本地只读独立审查，结果会与本文件和 `quality/verify.json` 同步，仍不等于 WorkflowHub provider pass。

前一轮独立只读复核发现上述遗漏；本轮已修复并重新跑回归，最终同范围独立只读复审为 `clean`。这不等于 WorkflowHub provider review 通过。

真实 89 条原始语料已用于 Task1 控制面回归（49 passed），并完成 Task3 全量语义/provider：20/20 调用、17/17 正题、0/3 负题误命中、标题和归属均 30/31。质量门已通过，但 summary confirmation、旧正式根保护/readback 和 WorkflowHub provider review 仍不可用；本文件不是 released 证据。

本轮正式交付边界复审又发现并修复三点：首次空目标补了真实安装后的 locked readback；批次拆分场景中“父失败、子成功”不再重复重放；非法旧 formal tree hash 会直接停止 replay。对应 acceptance 负例已加入；修复后专项 P1/P2/P3 为 `9/57/9 passed`，相关聚合 `216 passed, 3 skipped`，全仓 `639 passed, 3 skipped`；回执快照 hash 为 `28e20517ef4f7b8fbfef2de9a7af0dbf958089f90cb57556ff8053e0de6ff0e9`。
