# ADR-0012：Task5 接回 provider-backed semantic compiler

- 状态：proposed（mini-task design review 后进入实现）
- 日期：2026-08-20
- 范围：Task5 `reader-quality-compiler-redesign` 修复入口

## 背景

Task5 的原始代码库仍有 `src/knowledge_digest/llm.py` 和 `embedding.py`，但当前 Task5 runtime 没有调用它们。真实候选因此主要是文件整理和原文投影：目录更整齐，正文却没有经过业务语义编译，embedding 也没有参与问题/场景路由。已有 evaluator 还会读取静态 baseline 的 `strict_advantage` 和 case 中预写的答案文案，不能证明新生成的知识真实胜过 CompanyBrain。

用户要求：只使用 `/Users/Hugh/Downloads/confluence 原始数据` 作为知识事实来源，参考 CompanyBrain 的问题/场景入口和页面组织，使用 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8` 以及 embedding，并在实现审查、测试和真实质量门都通过后才重新做 89 条真实运行。`mini_task.design` 的 `terminal-clean` 结果只作可选 advisory，不阻断继续推进。

## 决策

Task5 修复入口采用 provider-required 编译链：

```text
89 raw sources
  -> snapshot/block/claim ledger
  -> Qwen typed semantic compile
  -> calibrated jina embedding query/source route
  -> five page-type projection
  -> Reader/Audit lineage gate
  -> actual five-dimension comparison
  -> Downloads candidate/not_released or released
```

1. LLM 只消费当前 raw snapshot 的受信 Block/Claim 输入，返回 typed JSON，不直接写 Markdown。
2. typed output 必须包含五轴、page type、槽位正文和 Claim refs；受保护数字、路径、命令、URL、限制和条件必须保真。
3. embedding 既要 probe，也必须参与 quality case 和 related route；route ledger 保存 query、候选、分数、rank、selected/reason 和 provider identity。不能回退到 Jaccard 混用。
4. provider、typed contract、lineage 或 route 失败只写 Audit；provider-required 模式禁止 `full-source` Reader 和 raw-copy fallback。
5. CompanyBrain 只作为冻结只读对照 snapshot，baseline/case 不允许预写 verdict 或答案；五维结果从实际 Reader/Audit 和 snapshot 重算。
6. slice 与 full 共用同一质量门；slice 失败仍处理 89 条，但保持 `not_released`。
7. provider 配置优先级是显式 CLI > `~/.config/knowledge-digest/config.json`；v2 配置中的 `api_key` 优先，`api_key_env` 仅作兼容回退；最终输出根目录是 CLI 指定的 Downloads 新目录。

## 五维比较的可比性修正

实现审查发现“CompanyBrain 没有 Task5 同形结构”不能直接等于四个维度的 `false`。当前 evaluator 使用同一份可观察 rubric 对两边重算：正文原子命中形成 `content_score`，实际结构证据形成 `structure_score`，两者等权得到每维 `0-100` 分。KD 读取本次 route/projection/Reader/Audit/RenderLedger；CompanyBrain 读取 hash 绑定 Markdown 快照和结构标记。Reader-Audit 需要 claim-level Audit/render ledger，CompanyBrain 没有时只记录该实际结构缺口。

每个维度独立比较 `kd_score > cb_score` 才输出 `KD_WIN`；`TIE`、`CB_WIN`、`UNKNOWN`、`CB_MISSING` 均阻断。QualityCase 和 baseline 禁止写入分数、verdict、答案正文或 `strict_advantage`；结果 schema 为 `task5-quality-result.v3`，不使用跨维总分抵消。

## 为什么不直接改正式 digest 管线

正式 S1–S6 是稳定的本地知识发布管线，用户当前要求是修复 Task5 的真实结果，不是重做所有 Digest 行为。将 provider 接线隔离在 Task5 可保留 Task4、旧正式包、CompanyBrain 和原始输入不变，也让失败的真实实验不会覆盖用户已有知识库。

## 代价与风险

- provider 依赖会让真实运行因凭据、网络、模型响应或 calibration 不可用而阻断；这是需要公开的真实失败，不用离线整理伪装成功。
- 89 条逐源 typed compile 和 embedding route 会消耗调用预算，因此 preflight 必须先计算预算，run identity 必须绑定配置和 prompt/schema。
- provider 输出的语义质量仍可能不足，所以五维 case 必须读取实际 Reader/Audit，并把 `TIE/UNKNOWN/CB_MISSING` 保持为不通过。
- 与普通 mini-task 相比范围较重；接受的唯一原因是用户明确要求在同一 Task5、同一 89 条原始语料上修复，且本 ADR 固定不扩大到正式管线、数据库、CompanyBrain 写入或新任务。

## 回滚和失败边界

失败只保留本次 Audit/staging/evidence，旧 Task4/CompanyBrain/正式 Reader 不变。未通过 provider 或 lineage 的来源不进入 Reader；任何质量或 source closure 硬门失败都保持 `candidate/not_released`。不通过删除、reset 或覆盖来“回滚”。

## 验收依据

- 设计：`specs/task5-reader-quality-compiler-redesign/decision-log.md` 的 D-016–D-024 和 design review dispositions。
- 规格：同目录 `spec.md` 的 Repair revision v2/v2.1 与 AC-RP-001–AC-RP-013。
- 计划：同目录 `plan.md` 的 Repair phases R1–R5。
- 真实边界：原始目录只读，CompanyBrain 只读，最终候选输出为 Downloads 新目录。

## 实现补充：provider 输出稳定性

历史验证曾使用 qwen3.6；当前生效运行固定使用 `~/.config/knowledge-digest/config.json` 中的 `qwen3.8` 和 Jina `jina-embeddings`。验证还表明：全量 89 条来源的 Qwen 请求必须在冻结 prompt 后有界并发，否则会把正常运行误判为卡死；Qwen 的 Claim 引用矩阵不能直接信任。

因此实现采用两层边界：模型只负责基于当前 Claim 写 typed 页面，编译器再从已接受的正文、槽位、五轴和已有 Claim 中补齐逐句引用与 required-atom evidence。补齐只选择与正文共享事实锚点的现有 Claim，不增加事实、不把 Audit 原文复制进 Reader；无法证明的正文仍保持 Audit-only/blocked。输出长度也受页面级限制，避免 provider JSON 截断伪装成成功。
