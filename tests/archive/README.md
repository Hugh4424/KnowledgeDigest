# 历史测试

这里保留已退役实现对应的测试材料。它们不属于当前 `pytest` 回归入口：旧 Reader/S1–S6 测试依赖已删除的 `knowledge_digest.cli`，Phase 3/4 测试依赖已退役的 agentmemory/embedding 模块。

当前 active 测试仍在 `tests/acceptance/`，覆盖 semantic compiler、Reader projection、navigation、publish 和 acceptance 入口。归档测试只有在恢复对应旧实现或做历史重放时才应显式调用。
