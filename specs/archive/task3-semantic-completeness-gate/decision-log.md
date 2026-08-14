# Decision Log

## 原始需求

| ID | 原始需求/事实 | 来源 | 处理 |
| --- | --- | --- | --- |
| R-001 | 真实资料测试必须可读、结构化、不能把不完整结果伪装成已消化。 | 当前 Task 3 目标与真实运行复盘 | D-001 |
| R-002 | 现有语义编译器对单篇超过 9000 字的来源只送前 9000 字；真实语料 49/89 篇超过该上限。 | `/Users/Hugh/Downloads/confluence 原始数据` 与 `scripts/task3_semantic_compile.py` | D-001 |
| R-003 | 失败或降级必须明确记录，不能静默通过。 | KnowledgeDigest 质量合同、当前用户要求 | D-001 |

## 关键事实

- 当前 Reader 编译器会保留完整原文作为 fidelity-only 回退，但已有语义候选会覆盖回退正文。
- 现有 prompt 虽要求模型说明输入被截断，但机器端没有据此阻止候选进入 Reader。
- 继续增加自动重放或无上限分块会重新引入用户已经指出的调用浪费和长时间无反馈风险。

## 决定 D-001

### 选择

选择 A：长文达到语义输入上限时，不接受该次语义候选；保留完整来源的 fidelity-only 页面，并在语义审计和 Reader source manifest 中明确记录 `semantic_truncated_fallback`。

### 大白话理由

模型只看到了半篇，就不能把它说成整理完了。完整原文虽然不如语义摘要好读，但至少不丢内容；读者和后续任务也能看见这篇资料需要重新处理。

### 后果与风险

- 好处：不会把半篇资料伪装成完整知识，调用次数不增加，失败边界清楚。
- 代价：长文暂时是清理后的完整原文页，不是语义摘要，Reader 的语义覆盖率会下降。
- 风险：如果未来把上限调高，仍需重新运行并用新的输入长度证据验证；本 mini-task 不自动拆块或追加调用。

## 延期交接

- `DEFER-001`：未来若要完整消化超长文，另行设计“有预算、有进度、有合并校验”的分块编译，不在本 mini-task 偷加调用。
- 下游交接：读取 `reports/semantic-compile.json`、`audit/semantic-manifest.json`、Reader `audit/source-manifest.json` 的降级字段；`semantic_truncated_fallback` 不是发布成功，也不是人工验收通过。
- 本 mini-task 不重走 make-decision、不修改 CompanyBrain、不改变 `released/not_released` 语义。
