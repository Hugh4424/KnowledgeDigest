# Phase P1 — 89 条全量 Reader 编译

## 目标

在新隔离输出目录中，把 89 条来源编译成稳定主题、可读 Reader 和可回放 Audit；不触碰旧正式结果、CompanyBrain 或旧 pilot。

## 允许改动

- 新增 `config/task4-reader-quality.v1.json`
- 新增 `src/knowledge_digest/task4_reader_quality.py`
- 新增 `tests/acceptance/test_task4_full_compiler.py`
- 修改 `src/knowledge_digest/page_layout.py` 的 Task4 通用渲染 seam

## 覆盖范围

FR-SOURCE-001/002、FR-READER-001/002/003、FR-FAIL-001；对应 AC-SOURCE、AC-READER、AC-FAIL 全部标准 ID。

## 非目标

不改 `topic_axis.py`、`pipeline.py`、`reader_compiler.py`、题集、CompanyBrain、旧 pilot 和正式知识库；不在本 phase 判定优于 CompanyBrain。

## 测试路线

原计划：`feature + backend-testing`。实际边界仍是本地 Python adapter/renderer/config/acceptance，无 API、数据库、部署或浏览器链路，因此不重路由。

- T001 RED：先放可导入但明确 `not_implemented` 的 stub，再运行 `uv run --frozen pytest -q tests/acceptance/test_task4_full_compiler.py`，必须因目标断言失败而非 setup/import 失败。
- T002 GREEN：同一命令、同一 oracle 退出 0；验证 89 条 manifest、稳定 topic、唯一 Claim、Reader body/route、Audit 回查和失败隔离。

## 停止条件

需要改变产品范围、题集、CompanyBrain、正式发布语义或既有 TopicIndex 合同；或出现旧正式产物被改写、失败被伪装成功。

## 预期阶段结论

交给 P2 的是 candidate Reader bundle、source/topic/Claim/Audit 证据和真实失败状态；不交接“已超过 CompanyBrain”。
