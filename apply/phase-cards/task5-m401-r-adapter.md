# Task5：M401-R authenticated promotion adapter

## 目标

把现有 WorkflowHub `review-record` 的 authenticated canonical review 结果，收敛成 Task5 当前 v4.7 要求的 M401-R attempt、promotion receipt 和 implementation successor。通用 WorkflowHub 不承载 Task5 业务 schema；adapter 只负责跨边界绑定和原样复制。

## 允许修改

- `src/knowledge_digest/m401_r_adapter.py`
- `scripts/task5_m401_r_adapter.py`
- `tests/acceptance/test_task5_m401_r_adapter.py`
- 本 Phase Card

## 覆盖 AC 与非目标

- 覆盖当前 M401-R 的身份、字节、finding disposition、promotion 和 handoff binding。
- 不调用 provider，不读取 raw/CompanyBrain，不修改 WorkflowHub core、原始资料或 Downloads。
- 不把 review unavailable/partial/未处置 finding 转换为通过。

## 测试路线

- RED：缺失 finding disposition、snapshot/material 漂移、旧 promotion 冲突必须失败。
- GREEN：当前 M401 attempt + available semantic review + 完整 disposition 生成 attempt-local refs，并通过 compiler successor validator。
- backend/fullstack：本地文件事务和跨仓库 canonical review bytes；不涉及 UI。

## 停止条件

- review 不是当前 authenticated snapshot/material，或 terminal status 不是 semantic。
- provider 结果 unavailable/partial，或 finding 没有显式 disposition。
- promotion 目标已经存在但字节不一致。

## 执行事实（2026-09-08）

- RED：旧实现会在 M401-R attempt 内额外写入 `workflowhub-attempt.json`、`workflowhub-report.md`、`finding-dispositions.json`，却缺少合同要求的 `attempt.json` 与 `inverse.patch`；allowlist 断言先失败。
- 修复：只写 `review-result.json`、`M401-R-review-receipt.json`、`attempt.json`、`inverse.patch`；外部 WorkflowHub attempt/report/dispositions 只读并以原始 ref/hash 绑定；promotion 前执行 `git apply --check --reverse`。
- 当前 M401 v35：`uv run --frozen digest --gate M401 ...` 通过；snapshot=`23ebac7da58c0d6e5a99a1c448744f6521123308`，material=`3ddd3bad65b25c898d91be15fc408f80f6bda0f0e14e27edb130c8e596a0e99a`，packet SHA=`d32549ed7300375afca76b14fd7c57c3cbc093ae9208fa02e45217762182cc27`；尚未 promotion。
- 验证：adapter focused `5 passed`；全量 `902 passed, 3 skipped`；compileall 通过；真实 source manifest/89 条闭包测试 `1 passed`。
- 未完成：当前 snapshot/material 尚无 authenticated `mini_task.implementation` Review，因此 M401-R promotion、WorkflowHub successor 和 M402 真实 provider/Downloads 运行仍未完成；不复用旧 v26 released 候选。
- 2026-09-08 契约复核发现上游/Task5 canonical bytes 分层缺口：WorkflowHub review result/attempt/provider output 由官方 writer 生成的是保留字段顺序的 2-space JSON + LF，Task5 gate 使用递归排序紧凑 JSON + LF；adapter 原先用 Task5 规则读取上游，真实 producer 会被错误拒绝。另发现本地 `review-result.json` 原样保存 `wh-review-result.v1`，不符合当前 spec 要求的 `workflowhub-mini-task-review-result.v1` projection，且 provider output 只看 caller 内嵌结果不足以证明 authenticated provenance。
- 修复：上游 result/attempt 按 WorkflowHub writer bytes 校验；要求 result/attempt 共享 `mini-task/implementation` 的 contract/semantic identity；验证每个 completed provider attempt 的 attempt/provider/schema/content/content hash 和 JSON findings；从已绑定 WorkflowHub facts 确定性生成本地 `workflowhub-mini-task-review-result.v1`（不改写 handoff 的上游 result refs），receipt 的 result hash 改为本地 projection bytes。新增缺 identity、provider output hash 和 projection/receipt hash 回归。
- 本轮验证：`uv run --frozen pytest -q tests/acceptance/test_task5_m401_r_adapter.py` → `7 passed`；`python -m compileall -q src/knowledge_digest/m401_r_adapter.py scripts/task5_m401_r_adapter.py tests/acceptance/test_task5_m401_r_adapter.py` 与 `git diff --check` 通过；全量 `uv run --frozen pytest -q` → `904 passed, 3 skipped in 53.26s`。
- 当前边界仍未变：没有当前 authenticated WorkflowHub review，未生成 M401-R/M402 promotion，未调用真实 Qwen/Jina、raw、CompanyBrain 或 Downloads；正式状态仍 `not_released`。

- 2026-09-08 根因修复：promotion view 冲突会发生在 attempt 已完整写入、固定 view 仍指向旧身份时；原 adapter 只能重新创建 attempt，无法安全恢复。新增显式 `resume_existing_attempt + replace_existing_promotion` 恢复路径：先逐字节复核四项不可变 attempt、inverse patch 和当前 authenticated review，再用 staged replacement 更新三个固定 view；默认路径仍对冲突 fail-closed。
- 2026-09-08 RED/GREEN：新增恢复后替换旧 promotion 的回归，先得到 `TypeError`（接口缺失），实现后 `uv run --frozen pytest -q tests/acceptance/test_task5_m401_r_adapter.py` → `8 passed`；`compileall`、`git diff --check` 通过。该测试只证明 adapter recovery contract，不证明 M402 或 released。
- 2026-09-08 路由：test-routing-advisor 依赖在当前技能目录不可用；按实际 changed files 选择 backend/file-transaction route，覆盖 adapter → immutable attempt → promotion view → handoff validator；不涉及 UI、raw、CompanyBrain 或 provider。
- 当前仍未执行：真实 M401-R promotion、M402 89 条运行、五项 CompanyBrain 对比、surface QA、release/close。下一步是对已验证的 v49 attempt 执行显式 recovery promotion，再在固定 refs 通过校验后启动 M402。
