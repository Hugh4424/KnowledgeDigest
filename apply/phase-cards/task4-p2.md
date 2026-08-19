# Phase P2 — 全量机器质量与 17+3 批量对照

## 目标

消费 P1 candidate，生成 89 条机器质量报告和一张固定 20 行（17+3）对照表；条件不全时只输出 `undecidable/not_released`。

## 允许改动

- 新增 `scripts/task4_reader_quality.py`
- 新增 `tests/acceptance/test_task4_full_quality.py`
- 修改 `src/knowledge_digest/task4_reader_quality.py`
- 只增加 `src/knowledge_digest/reader_quality.py` 的 Task4 复用 seam

## 覆盖范围

FR-QUALITY-001/002/003/004/005、FR-FAIL-001；对应 AC-QUALITY-001..005 和 AC-FAIL-002。

## 非目标

不改冻结题集、CompanyBrain、Task3 正式质量门、旧 pilot；不逐页人工、不引入额外状态服务；机器通过不代替正式人工结论。

## 测试路线

原计划：`feature + backend-testing`。实际边界仍是本地 Python module/CLI/report/acceptance，无 API、数据库、部署或浏览器链路，因此不重路由。

- T003 RED：质量 contract stub 返回明确 `not_implemented`，运行 `uv run --frozen pytest -q tests/acceptance/test_task4_full_quality.py`，必须因质量行为断言失败。
- T004 GREEN：同一命令退出 0；逐行检查 20 行字段、session/order/context/network/baseline receipt、三轴公式、人工状态和 fail-closed。
- T005 FINAL：只运行一次计划中的 aggregate；记录退出码和覆盖限制，不把测试绿写成业务优于结论。

## 停止条件

需要改题集/比较协议/CompanyBrain、共享评测上下文、把 `candidate` 或 `continue` 变成 `released`，或关键证据缺失。

## 预期阶段结论

交给 verify-code 的是当前实现、测试、机器报告、20 行表、根因记录和真实运行合同；最终是否优于 CompanyBrain，必须看真实 89 条运行和正式人工证据。
