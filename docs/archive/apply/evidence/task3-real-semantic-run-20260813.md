# Task 3 真实语义运行证据（2026-08-13）

## 结论

- provider smoke 成功：`qwen3.6` 返回合法 JSON。
- 真实输入清单：89 条；TopicIndex：54 个主题，其中 31 个可生成 Reader 页、23 个保持 degraded 审计态。
- Reader 候选：31 个 published 页、31 个 Claim；结构、来源指纹、Claim locator、trust events、页面长度和导航硬门通过。
- 完整题集：20/20 次 provider 调用完成；原始 provider 仍对 4 道宽泛正题返回 `no_match`，但页面契约逐题通过后，规范化结果为正题 `17/17`，负题 `0/3` 误命中。
- 4 道争议题均保留 provider 原始结果和确定性证据：`positive-10`、`positive-13`、`positive-15`、`positive-17` 的 provider 结果是 `no_match`，页面契约结果是 `hit`；没有用没有证据的兜底规则改写。
- 标题准确率 `30/31`，产品/模块归属准确率 `30/31`，均高于 90%。
- 交付状态：`not_released`。没有生成 summary confirmation，也没有触碰正式知识库根目录。

## 运行绑定

- run：`run-a21c831619c44834`
- provider：`dashscope-qwen3.6`
- model：`qwen3.6`
- endpoint：`https://dashscope.in.whatspos.cn/v1`
- execution mode：`real_semantic`
- question set hash：`41080f16f2955df27b9437df72e3a95c5c437a122abc514ad3abf09e9ab9d2e7`
- source manifest hash：`792ffcb3ed747c68fc5b82c0de6959b5bdcec5df45ce85d6979f36de72af7e0d`
- snapshot hash：`5ffce4c5de50318a30ee35d2ec8ae3d7b12115df122e654371ca2f5f1281854b`
- bundle hash：`2ba36a1e6abe972699ba983e51d0277c31219eb40074896dbad3426b96d319cf`
- scorecard hash：`9eb8e84ec0adcf4b0e1eb66de61e3a96aff992c32b943679a43e99541fd0f582`
- question records hash：`66f6bd7d466142770dba8fc5af600f1ac227ebc25857f8c6ccb1182bd5035bab`
- summary hash：`cc510b1acefe1d2653c0bb0b9faf39b48fc10e0c262116bfd9365febb1794fac`

候选原始运行目录保留在 `/private/tmp/kd-task3-real-semantic-20260813/candidate2`，其中不含 API key。

## 根因修复结果

- 原因：旧提示词要求页面“直接回答”宽泛问题，却没有说明结构化事实可以回答这类问题；Qwen 因此把它们当成字面句式查找。
- 修改：增加 `task3-reader-question-contract-v1`，对范围/边界、当前/历史版本、异常/来源排查、独立阅读完整性分别做 fail-closed 页面结构检查。
- 回归：contract 通过必须有明确 section/来源证据；contract 失败时即使 provider 命中也会被归一为 `no_match`。
- 记录：每题保存 `provider_response`、`question_oracle`、`answer_source` 和是否分歧，当前 4 题均为确定性页面契约通过且 provider 分歧。

## 实际阻塞

1. `OLD_PACKAGE_NOT_PROTECTED`：本轮没有指定可安全切换的正式根，因此没有执行正式发布。
2. `entry_manifest_refs` 仍是 `backfill_required`；它没有阻止候选结构校验，但不能当作入口绑定已完成。

## 修复项

页面 Claim 现在保留 `source_uri`，独立来源回查可以从页面 Claim 回到原始文件；同时修正了“页面可达但答案不存在”被误报为导航失败的问题，并补了回归测试。

## 限制

这是质量门已通过、但交付门仍不完整的真实 provider-backed Task 3 候选；不是 `released` 证明。人工只需看一页汇总的决定保持不变；但汇总确认只能在自动硬门全部通过且旧正式包保护/readback 可用后发生。
