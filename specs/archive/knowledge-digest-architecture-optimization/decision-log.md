# KnowledgeDigest 架构优化决策

## 问题与目标
修复真实 89 篇语料暴露的跨批次 target identity 冲突、巨页、重复 Summary/Evidence 和不可恢复批处理问题；在不移动标准 src-layout 的前提下做轻量职责分层，保持内容、Evidence、Provenance 和 fail-closed 合同。

## 决策
1. 保留 src/knowledge_digest 标准 Python src-layout，不做目录搬家。只按真实职责抽出稳定身份、最终页面布局、批次运行三个深模块。来源：用户“轻量分层”与代码事实。
2. 分批只是执行手段，不保留现有 draft-N/cluster-N 语义。硬约束是稳定主题身份、失败批次可重放、已成功批次可恢复、最终合并不重复。来源：89 篇 DeepSeek 基线与方向盲审。
3. 正式输出为主题页和来源索引。来源索引只保存来源到主题页的相对链接，不复制原文、claim 或 Evidence，不替代 Provenance。来源：用户明确选择。
4. 主题内容超限时确定性生成 Part 1..N；每个最终 Markdown 页面包含 Summary/Evidence/Provenance 后仍不超过 300 行。禁止截断；全部 claim 恰好归属一个 part。来源：用户明确 300 行与无损合同。
5. 不丢内容用机器门禁判定：89 个来源全部 accounted；有效来源可从索引到达至少一个主题 part；输入有效 claim fingerprint 多重集与输出 Evidence 对账；provenance/coverage/validation 继续通过；无断链、无截断、无重复结构。最终验收不用 LLM，也不要求 no-LLM 与 DeepSeek claim 数相等。
6. embedding 不作为本任务前提；不可用时保持整次 Jaccard 回退。保留 LLM 产品分支，但最终验证零 LLM HTTP 调用。

## 影响范围
主要触及 ingest/cluster/draft/writeback/pipeline/CLI 周边的 identity、layout、source index、batch receipt seam；保持现有公共 digest/CLI/config/report 向后兼容。

## 非目标
不新增 CAS、journal、scheduler、daemon、vector DB、provider 路由框架、持久重试队列；agentmemory 不进入正式 pipeline/CLI；不删除 Evidence/Provenance；不移动 src-layout；不改 embedding 阈值或采用门。

## 风险与处理
分页会改变页面路径和数量：提供确定性 topic/part identity 与来源索引。增量重排可能产生旧 part：写前归档并移除过期 part。分批 receipt 可能过度复杂：仅保存 manifest、固定主题/重复来源计划、批次状态和运行报告引用，不做调度框架。

## 被拒方案
整体目录重构：无根因证据且维护面更大。每来源一页：不符合用户主题阅读目标。来源附录复制 claims/原文：重复且成本高。保留现有 draft-N/cluster-N：已被真实巨页故障否定。最终继续跑 LLM 验收：耗时高且用户明确取消。

## 文档判断
CONTEXT.md 已补充主题页、主题分页、来源索引术语。ADR 不需要：输出布局可逆，CONTEXT 足以解释，未引入难逆基础设施。旧“只产生 split suggestion”由新规格显式 supersede 为最终落盘硬上限。

## 未决项
无需要用户继续选择的方向问题；具体函数切分、命名和测试夹具交由 build-spec/build-plan 在上述边界内确定。
