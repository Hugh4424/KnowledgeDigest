# ADR-0010: Task5 逐 case 严格质量门与分层状态

- 状态：`proposed`；等待本轮 make-decision 最终确认
- 日期：2026-08-19
- 范围：仅 `task5-reader-quality-compiler-redesign`

## 背景

如果只写“质量要高于 CompanyBrain”“切片通过后再全量”“来源缺失要审计”，实现者仍可以用总分、默认页面类型、跳过全量或模糊负证据把问题藏起来。Task5 的目标必须能被逐问题/场景证伪，同时不能因为早期切片失败就把用户要求的 89 条全量偷偷延期。

## 决定

1. 五个质量维度按用户原始要求固定：问题/场景路由、产品/模块/对象/场景/边界分类、业务化答案正文、定位/概念/操作/诊断/经验页面类型、Reader 可见与 Audit 可回查。
2. 每个质量 case 的每个适用维度都必须 `KD_WIN` 才算严格高于 CompanyBrain；`TIE` 不算通过，`CB_WIN`、`UNKNOWN`、`INVALID`、`CB_MISSING` 阻断；`N/A` 只允许双方都不适用。
3. quality case 与完整性 guard case 分离：前者证明质量胜出，后者证明空源、重复/冲突、媒体/表格/链接、Claim ownership 和特殊审计不会泄漏或丢失。guard case 没有 CompanyBrain baseline 时不伪造胜出，但失败阻断发布。
4. 垂直切片先做风险覆盖；无论切片结果如何，当前任务继续处理 89 条全量。切片失败的全量只能是 `candidate/not_released`，不能进入正式 Reader/released。
5. 来源、证据、问题、发布四层状态分开保存；`source_not_documented` 只能由完整冻结快照负证据审计触发，且只表达异常规则未被来源记录，不生成领域 Claim，异常专属问题保持 `not_answerable`。

## 取舍

- 允许总分或平局通过：运行简单，但不能证明“五项都高于”。
- 切片失败就停止全量：成本低，但违反当前任务必须完成 89 条的范围，也丢失最有价值的失败诊断。
- 用一个总状态代替分层状态：文件少，但会把空源、冲突、重复和未回答混为一谈。

## 后果

需要冻结 quality/guard case inventory、CompanyBrain 对照页、页面最小回答合同、状态优先级和 Audit 负证据。实现阶段仍可选择 JSON 字段名和命令，但不能改变这些语义边界。

