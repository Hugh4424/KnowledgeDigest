# mini-task tasks：语义完整性门禁

| ID | 任务 | AC |
| --- | --- | --- |
| T01 | 写入逐来源输入长度、上限和截断状态 | 01 |
| T02 | Reader 拒绝截断候选并保留完整回退 | 02,03,04 |
| T03 | 补充回归测试、旧 manifest 和跨工件一致性断言 | 01-04 |
| T04 | 对全部 89 篇真实语料重跑并与 CompanyBrain 对比 | 05 |
| T05 | 一次 implementation review，修复有效 finding | all |

顺序：`T01 → T02 → T03 → T04 → T05`。

完成定义：截断候选不再进入 Reader；相关测试和完整 pytest 通过；全部 89 篇真实资料有新目录、新报告、新对比；mini-task 按授权 close 并清理 worktree/branch。
