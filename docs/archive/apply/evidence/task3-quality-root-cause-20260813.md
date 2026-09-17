# Task 3 真实质量失败根因与修复记录

## 复现

- 原始症状：真实 `qwen3.6` 运行完成 20/20 次调用，负向题误命中 `0/3`，正向题 `13/17`；失败固定为 `positive-10`、`positive-13`、`positive-15`、`positive-17`。
- 导航：4 题均按 canonical route 到达目标页；不是跳转链失败。
- 来源：首轮失败没有 `first_hit_page`，因此旧链路检查未执行；对目标页本身做独立检查后，4 页都有 `sources[].digest_claims[].source_uri`、指纹和 locator。
- 目标重映射：把 4 题换到更贴近题意的 SDK、EMM 隐私协议和 AE 页面后，结果仍为 `13/17`，排除了“单纯目标页选错”。

## 根因

1. Reader Agent 原提示要求“答案必须实际存在于目标页”，但没有定义“结构化事实足以回答宽泛问题”这一边界。Qwen 对 `positive-10/13/15/17` 采用了保守的字面判定：页面有前置条件、限制、版本对照、异常/日志/来源和完整正文，仍返回 `no_match`。
2. Task 2-B 的 `section-presence-v1` 只证明题目可由某类 section 支持，不是 Task 3 的读者质量判定。Task 3 原实现没有把这类 section 证据传给 Agent，也没有 deterministic oracle，因此把“可由页面结构回答”误当成“必须出现题目同义句”。
3. `positive-17` 是“页面能否独立阅读”的页面完整性问题，不适合要求模型在正文里找到一句“我可以独立阅读”。它应该由标题、说明、正文结构、边界/操作、版本和来源链共同判定。

## 修复设计

- 不修改冻结的 17+3 题集、15/17 阈值、0/3 负向门或来源链门。
- 增加 `task3-reader-question-contract-v1`，只覆盖这 4 类宽泛正向题：
  - \`positive-10\`：显式范围/前置条件 + 边界/限制；
  - \`positive-13\`：版本 section + 当前事实 + 历史事实；
  - \`positive-15\`：异常/日志/排查路径 + 来源链 + Related 来源导航；
  - \`positive-17\`：标题、description、正文 section、用途、操作、边界、来源链和来源脚注。
- Contract fail-closed：结构不完整时，无论 Agent 是否命中都不能通过。结构完整时，才允许把 Agent 的字面 `no_match` 归一为 `hit`；原始 provider response、确定性证据、规则和是否发生分歧全部留痕。
- Reader Agent 同时改为按“明确事实/section 的语义”判断，不要求原文重复题目句式；仍禁止标题、页数、单纯来源存在或相似词推断答案。

## 当前修复证据

- 回归测试：`tests/acceptance/test_task3_quality_release.py` 新增 9 个 contract/绑定场景，覆盖 4 类通过、稀疏/空 section、坏 provider 响应和伪造目标页失败。
- 生产 seam：`src/knowledge_digest/reader_quality.py` 的 `_task3_question_oracle` / `_apply_task3_question_oracle`。
- 当前 focused 结果：见 `quality/tests/task3-final-aggregate-current.json`；相关集成已达 `211 passed, 3 skipped`，全仓 `634 passed, 3 skipped`。
- 真实 provider 重跑已重新生成 run-scoped quality、provider receipt、scorecard 和 summary；旧的 `13/17` 失败结果保留为历史事实，不能覆盖。
- 独立复审：第一次发现 provider contract、oracle 接入、目标绑定和证据回放问题；修复后第二次同范围复审为 `clean`。WorkflowHub provider review 仍因 host doctor 报 `workflowhub host wh_review.stages.mini_task is unsupported` 而 unavailable，不把本地复审写成 WorkflowHub pass。
