# simplicity-guard 事实 — Task 2-A（advisory，只读）

## 四阶梯检查

| 项目 | 阶梯 | 结论 |
| --- | --- | --- |
| OKF-compatible 结构合同整体 | P0 成立 | 对应 R-001..R-009、PRD §6.8/§6.9 冻结合同与已发生故障（Task2 输出审计），不是投机能力 |
| 复用既有模块（identity/jsonl/errors 按引用复用；navigation/publication/page_layout/provenance 不修改） | P1 | PRD 交付物明确「现有模块的最小 OKF profile writer/validator」；本计划 DEC-001 选择隔离新模块 API，复用稳定 identity/jsonl/error 事实，不改旧 Reader/navigation/publication/page_layout/provenance，也不新增通用 repository/service 层 |
| vendored 外部 parser | P2 复用 | 复用 GoogleCloudPlatform/knowledge-catalog 官方最小读取面（document/index/paths），不重写解析器 |
| PyYAML 依赖 | P3 最小新增 | PRD 强制固定版本 safe_load/safe_dump；这是唯一新增运行依赖且为合同硬约束 |
| 可选示例配置（okf.example.json） | 未纳入 FR | PRD 标注「可选」，spec 未把它写成需求，避免不必要产物 |

## 删除/缩小/复用观察

- 可删除：无 — spec 未包含任何超出冻结合同的新能力。
- 可缩小：无 — 结构合同范围已被 D1 压缩到最小（正文语义归 2-B）。
- 可复用：外部 parser、既有导航/写回模块、Task 0/1 audit records。

## 结论

无 revise_required 项：spec 全部要求都能回到 PRD/decision-log 必要性证据，没有 scope creep、重复能力或投机抽象。
