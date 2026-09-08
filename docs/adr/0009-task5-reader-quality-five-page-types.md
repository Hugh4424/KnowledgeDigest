# ADR-0009: Task5 五类业务页面与读者质量边界

- 状态：`proposed`；等待本轮 make-decision 最终确认
- 日期：2026-08-19
- 范围：仅 `task5-reader-quality-compiler-redesign`

## 背景

上一轮产物的主要问题不是目录不够整齐，而是没有按读者问题组织答案：产品、模块、对象、场景、边界没有形成可达路由，页面类型被压成 procedure，Reader 也没有把日常答案和审计回查分开。本任务要求五个评价维度都严格高于 CompanyBrain，因此页面投影必须先表达读者用途，再落到来源证据。

## 决定

Task5 的 Reader 页面类型采用五类业务用途：

- `positioning`：定位
- `concept`：概念
- `operation`：操作
- `diagnosis`：诊断
- `experience`：经验

五类是 Task5 的页面投影合同，不是五个事实来源桶；同一来源可以支撑多个页面投影，但每条正文 Claim 必须保留来源 ownership 和精确回查链。Task2/Task3 的历史三类 page type 记录不被改写，CompanyBrain 只作为路由、页面合同和关系建模的方法参考，不作为当前业务事实来源。

Reader/Audit 仍分离：空源、冲突、unsupported、ambiguous、unknown 和 lineage 不完整不能进入对应 Reader case。`source_not_documented` 只沿用 ADR-0006 的严格审计特例；它允许同页其他证据充分的内容进入 Reader，但不回答异常专属问题。人工只做自动五维汇总确认，不做逐页人工验收；交付状态仍遵循 ADR-0008 的 `released/not_released` 门。

## 取舍

- 保留上一轮三类 page type：实现更简单，但会继续把定位、概念、诊断和经验压成操作页，无法证明五维读者质量。
- 复制 CompanyBrain 的页面和事实：短期可读，但会把 CompanyBrain 的内部冲突和旧事实带入当前 89 条证据，破坏 lineage。
- 只用固定模板或关键词评分：容易得到机械绿灯，不能证明页面真的回答业务问题。

## 后果

页面编译前需要冻结问题/场景 case、页面类型和 Claim 投影关系；Audit 需要同时记录支持、冲突、缺失和不可回答状态。具体字段、section、样本矩阵和实现命令留给用户最终确认后的 build-spec，不在本 ADR 偷补。

