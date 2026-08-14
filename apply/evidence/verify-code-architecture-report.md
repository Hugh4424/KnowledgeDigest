# verify-code 架构验收（当前快照）

## 反向链路

原始需求 R-001～R-005 → `decision-log.md` 的最终确认 → `spec.md` 的 FR/AC → `plan.md` 的 P1/P2/P3 → `tasks.md` 的 T001～T013 → 当前实现和 acceptance tests。

用户最终确认的核心含义已保持：

1. 先冻结 89 条输入和全部版本/配置事实。
2. 从同一个 TopicIndex 生成唯一 Reader 导航；失败内容只进 Audit。
3. Related 只有有依据才生成，旧路径必须有 alias/deprecated 结果。
4. 自动执行 17+3、15/17、0/3、两个 90% 门；人工只看一页汇总，不逐页、不逐题、不查来源链。
5. `released/not_released` 是整包交付状态；页级仍是 `published/degraded`；不写 `human_reviewed`。
6. 失败、取消、未知、离线和并发冲突都保留旧正式包并停在 `not_released`；最终交给 Closeout 的只是文档、归档、清理和恢复演练。

## 当前实现检查

- P1：`reader_bundle.py` 的 semantic 输入绑定 TopicIndex、Claim、fixture selection；验证阶段也重新检查 Claim/source/trust。Related target 必须是另一个已知 Topic，locator 必须是 `lines:` 格式；old-path split fail-loud，并写实际 alias/deprecated stub。
- P2：`full_release.py` 重新读取候选文件和报告，检查 89 条 manifest、run id、source/Claim 指纹、trust events、页长、导航、质量 scorecard hash、Reader hash、comparison binding、确认文件 hash 和正式根 readback。发布状态投影不一致或回滚失败会停在 `not_released`，并保留备份及恢复说明。
- P3：comparison 直接读取 Task3 `bundle/audit/reports`，CompanyBrain 没有共享质量合同时为 `N/A`；入口对异常状态 fail-fast，JSON replay 不具备把结果升级成 released 的权限。
- 本轮遗漏修复：Task3 质量结果现在绑定仓库中的冻结 Task0 题集原文、入口、目标说明和 `question_set_hash`；semantic 候选必须有完整 quality replay、provider/config/response 回放和逐调用 request/response hash，并由外部冻结 `expected_source_manifest` 绑定来源；trust 事件必须与 `audit/trust-signals` 的完整事件数组和页面 managed-content hash 一致；locked copy 使用 `symlinks=True` 并在 stage 复查，软链接、FIFO 和设备节点不能进入正式根；comparison 的三方 evidence 还必须有非空 `saved_integrity`，Task3 必须有 `run_id/bundle_hash`。
- Task2-A 兼容：正式 `source_count` 旧语义恢复；Task2-A acceptance 继续通过。
- 真实输入盘点：见 `apply/evidence/verify-code-real-input-inventory-20260813.md`；当前已有可绑定的 Task3 候选根 `candidate2`，并由 `run-a21c831619c44834`、89 条 manifest、snapshot hash 和 bundle hash 绑定。它证明候选质量和交付硬门，不替代正式根保护/readback。

## AC 当前结论

| AC | 当前结论 | 证据和限制 |
| --- | --- | --- |
| AC-01 | pass | 89 条 manifest、TopicIndex、题集、provider/config、预算和候选 Reader/Audit 均由同一 run/snapshot 绑定；Task1 控制面 49 passed |
| AC-02 | pass | P1 正常/降级/失败隔离测试；真实语料仍未验收 |
| AC-03 | pass | Home→index→product/module/page、来源入口和断链负例 |
| AC-04 | pass | Related provenance、双向、无关系、自引用/未知目标负例 |
| AC-05 | pass | 真实 17+3 完成；正题 17/17、负题误命中 0/3；4 个 provider 分歧保留原始响应和页面契约证据 |
| AC-06 | pass | 候选交付硬门通过；标题和归属均 30/31（96.77%），页长、Claim、结构、导航和来源链可回放 |
| AC-07 | pass | 候选已生成一页 summary，包含运行、17+3、90%、硬失败、警告、未知、模式和旧包保护；无需逐页/逐题/逐来源链验收 |
| AC-08 | pass | hard failure/unknown/warning/缺确认和状态投影测试 |
| AC-09 | unknown | 确认校验合同已有测试，但本次没有 summary confirmation；不能把“可确认”写成“已确认” |
| AC-10 | unknown | 故障注入和旧包保护通过；真实 affected replay 未运行 |
| AC-11 | pass | alias/deprecated 实际文件、目标解析和 tamper 负例 |
| AC-12 | pass | Task2/CompanyBrain/Task3 三方固定八维报告已生成；每维 comparable/N/A，有 binding、saved_integrity、局限且明确 `not_a_release_decision` |
| AC-13 | pass | fail-fast handoff、deferred/risk 和不可改写状态测试 |

`unknown` 不是通过。当前仍为 unknown 的是 AC-09（没有 summary confirmation）和 AC-10（尚未执行真实 affected replay）；WorkflowHub provider review 和正式根 readback 也不可用。质量门通过不等于包级 `released`。

## 风险处置

- 已修复：semantic 验证 fail-open、Related 任意 ID、old-path 覆盖/split、Task2-A source_count 回归、质量 scorecard 可篡改、来源 manifest 只验数量、状态面不一致、回滚失败不可恢复、Task3 comparison/入口断接。
- accepted risk：自动读者可能漏掉人工更容易发现的表达问题；这是用户已确认的“人工只看汇总”取舍，继续由固定题集、机器硬门和未知阻断控制。
- deferred：正式 release readback、真实 affected replay、Closeout 文档同步/归档/清理/恢复演练；CompanyBrain 没有共享质量合同的维度继续标 N/A。

## 质量事实

- 真实 Task1 89 条回归：`49 passed`。
- 相关集成（带真实语料）：`211 passed, 3 skipped`。
- 全仓（带真实语料）：`634 passed, 3 skipped`。
- 真实 Task3 semantic：20/20 provider calls；17/17 正题、0/3 负题误命中；标题/归属 30/31；质量和候选交付硬门通过。
- `git diff --check`：通过。
- `python -m compileall -q`：通过。
- WorkflowHub provider phase/final review：`unavailable`，既有尝试没有可信终态；不能写成 clean review。
- 本轮第一次独立只读审查发现 4 项实现问题，均已修复；最终同范围复审为 `clean`。本地测试/复审不是 WorkflowHub provider review。即使所有 JSON hash 自洽，也不能单靠普通本地文件证明 provider/来源没有被有权限的写入者伪造；因此真实 semantic receipt、外部冻结 manifest 和正式 readback 仍是硬边界。

结论：本轮根因修复、fixture 回归、真实 89 条控制面和 Task3 全量语义质量均通过；仍因没有可安全绑定的旧正式根/readback、没有 summary confirmation、真实 affected replay 未执行且 WorkflowHub provider review unavailable，verify-code 保持 `incomplete`，不能进入 close，也不能宣称 `released`。
