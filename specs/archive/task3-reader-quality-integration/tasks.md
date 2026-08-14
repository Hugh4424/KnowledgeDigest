# mini-task tasks：Reader 质量整合

| ID | 任务 | AC |
| --- | --- | --- |
| T01 | 来源扫描、产品/模块映射和 unclassified/general 兜底 | 01,03,07 |
| T02 | 正文清理、Reader 投影和超长拆分 | 04,05,06 |
| T03 | 产品 overview、知识类型入口、模块 index、根导航 | 01,02,06 |
| T04 | 接入 `task3_full_release.py --raw-input` | 07,09 |
| T05 | 失败边界和旧包保护测试 | 07,08 |
| T06 | 接口形状、80 分代理、相关测试和完整 pytest | 01-09 |
| T07 | 真实资料运行并与 CompanyBrain 对比 | 01-09 |
| T08 | 一次 implementation wh-review，修复有效 findings | all |

顺序：`T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08`。

设计审查结果：一次 `mini_task.design` 已完成；major finding 已通过兜底和拆分修复，minor findings 已通过 80 分口径、最小接口和过程元数据处置闭合。不得机械重复设计审查。

完成定义：相关 acceptance 与完整 pytest 通过；真实运行有独立 output、source manifest、质量报告、比较报告和降级说明；能回答产品层级、overview、模块入口、来源覆盖、Reader 泄漏和正文是否仍是原文堆放；wh-review findings 原样留存。
