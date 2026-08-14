# mini-task plan：语义完整性门禁

## 实现步骤

1. 在语义编译器建立逐来源输入长度/截断清单，并把上限写入 manifest/report。
2. 将截断来源从语义成功项中排除；保留明确的 `semantic_truncated_fallback` 事实。
3. Reader 编译器读取该清单；拒绝截断候选，完整回退并写入 source manifest 和失败审计。
4. 增加 fixture 覆盖：正常语义候选、截断候选、旧 manifest 无字段但超限、指纹冲突、完整回退、审计不可读、完整原文为空/不可读，以及三份清单字段一致性。
5. 先用既有 qwen3.6 小批量、零重放规则重新生成独立语义候选；再对全部 89 篇真实资料跑 Reader 管线，最后生成新的 Reader 与 CompanyBrain 对比。
6. 固定本 mini-task 快照，完成一次 design review 和一次 implementation review；有效问题在本任务内修复，然后按授权 close、清理。

## 文件边界

- 修改 `scripts/task3_semantic_compile.py`。
- 修改 `src/knowledge_digest/reader_compiler.py`。
- 修改/新增 `tests/acceptance/test_task3_quality_release.py` 的相关测试。
- 不修改 CompanyBrain、不改正式发布状态、不重走 make-decision。

## 回滚

仅回滚本 mini-task 分支提交；保留已生成的真实运行证据和旧 Reader 候选，不覆盖旧目录。
