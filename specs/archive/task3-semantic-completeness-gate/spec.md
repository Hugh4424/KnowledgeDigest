# mini-task spec：语义完整性门禁

## 目标

当语义编译器因单篇输入超过 `max_chars_per_source` 而只看到原文前段时，KnowledgeDigest 不得采用该语义候选覆盖完整原文。系统必须保留完整来源的 Reader 回退，并把原因写入可回查审计。

## 用户流程与页面范围

1. 语义编译器扫描来源并记录每篇实际字符数、上限和是否截断。
2. 超过上限的来源不写入可被 Reader 采用的语义成功项；对应来源进入明确的语义失败/降级清单。
3. Reader 编译器读取语义清单；若某来源被标记为截断，即使候选文件存在且指纹匹配，也只使用完整原文的 fidelity-only 清理结果。
4. Reader 页面继续按产品→模块→知识页组织，来源覆盖和完整性审计继续可回查。

## 状态

- `semantic_candidate`：输入完整、指纹匹配、内容完整性检查通过。
- `semantic_truncated_fallback`：来源超过语义输入上限，Reader 使用完整来源回退。
- `semantic_failed`：模型调用、解析或其它语义失败，Reader 使用完整来源回退。
- 包级仍由现有 `candidate/not_released` 合同控制；不新增项目状态。

语义输入上限统一由 `max_chars_per_source` 提供，默认值为 9000 个 Unicode 字符。Reader 读取完整来源实际字符数，并优先使用语义 manifest/report 中记录的同一上限；旧 manifest 没有该字段时使用默认值 9000。超过上限但没有截断记录时，也按保守降级处理。

## 成功边界

- 不存在“输入被截断但仍以 `semantic_candidate` 进入 Reader”的来源。
- 每个被截断来源在语义报告、语义 manifest、Reader source manifest 中都有相同的相对路径、source URI、字符数与上限；跨工件字段一致性必须有自动化断言。
- Reader 回退使用完整原文指纹，来源内容不丢失；现有结构、链接、泄漏和 300 行检查继续通过。
- 不增加自动重放，不把一次截断输入拆成隐形多次调用。

## 失败边界

- 语义 manifest 缺少截断信息但候选来源长度超过默认上限：Reader 必须拒绝该候选并记录保守降级。
- 来源指纹不匹配、manifest 与候选冲突或审计无法读取：拒绝候选，不覆盖完整原文回退。
- 完整原文无法读取或为空：保留现有失败审计和 `not_released` 语义。

## 非目标与延期

- 不在本 mini-task 设计长文分块摘要、跨块合并、追加重试或后台队列。
- 不改变产品/模块分类规则、CompanyBrain、人工验收流程或正式发布状态。
- 长文语义精炼延期到 `DEFER-001`，由后续任务另行决策和预算。

## 验收条件

- AC-01：语义报告记录 `max_chars_per_source`、`truncated_count` 和逐来源状态。
- AC-02：Reader 不采用 manifest 标记为截断的候选，完整回退状态可见；旧 manifest 超过默认上限也保守降级。
- AC-03：自动化测试断言语义报告、语义 manifest、Reader source manifest 的截断字段一致。
- AC-04：完整来源指纹和关键内容仍通过现有保真检查。
- AC-05：聚焦测试、完整 pytest、真实 89 篇资料重测和 CompanyBrain 对比均留存结果。
