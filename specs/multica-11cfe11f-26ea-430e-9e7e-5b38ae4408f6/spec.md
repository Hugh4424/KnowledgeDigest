# 多轮 rethink 与单写入恢复规格

**功能名**：KnowledgeDigest Phase 2 动态加固
**状态**：待正式审查
**上游依据**：accepted make-decision；用户已选择 `spec-clarify` A：可解释规则表。

## 速读卡

- **一句话需求**：按本地可解释规则只给高风险内容启用最多 3 轮 rethink，并用单写入锁与持久 prepare/commit 状态保证中断后安全重跑。
- **核心改动点**：风险规则可回放；高风险每个知识簇最多 3 轮；相邻轮正文规范化后完全相同即停止；单库第二个写入请求明确拒绝；中断重跑不重复、不丢页。
- **最大影响面**：S4 草稿生成、`pipeline.py` 编排、`writeback.py` 正式写回和 `_digest` 运行状态。
- **验收信号**：风险和轮次记录完整；高风险有硬上限；第二个写入得到 `CONCURRENT_WRITER_NOT_ALLOWED` 且正式 KB 不变；模拟中断后重跑最终只保留一份页面、归档和历史记录。

## 1. 已锁定的上游决定

以下内容继承上游 accepted decision，不重新解释、不重新提问：

- D1：使用内容驱动的本地风险规则，不使用固定总开关，不使用模型 judge；每次运行记录本地信号和选择的路径。
- D2：高风险内容最多 3 轮 rethink；只有规范化摘要正文与紧邻上一完成轮逐字节相同才提前停止。
- D3：同一知识库当前只允许一个写入者；第二个请求在 mutation 前失败，错误码为 `CONCURRENT_WRITER_NOT_ALLOWED`，不静默排队。
- D4：在既有写回路径外增加持久 `prepare` / `commit` 状态；稳定运行标识支持恢复或安全重做。
- D5：接受 rethink 收益和成本尚未实测的风险；延期并发成功、CAS 自动重试、调度器、daemon、外部索引同步、模型 judge 和超过 3 轮。
- 本阶段继续复用本地手动 `digest(new_dir, kb_dir)`、现有 S1-S6、文件锁、fsync、原子替换、来源审计和归档机制；不引入新 CLI 参数或新外部服务。

本阶段已澄清的单一决策轴：风险路由使用**可解释规则表**。规则保留每个信号、命中的规则和最终风险等级，便于回放；阈值固定在本版本规则表中，仅沿用已有 `max_doc_lines` 配置作为长文阈值，不增加另一套用户配置。

### 1.1 决策材料分类

- **locked upstream decisions**：D1-D5，已在本节逐条继承；未重新提问。
- **upstream unresolved items**：数值阈值、质量/成本记录、回退阈值、恢复状态位置/身份和测试夹具；本规格已给出首版实现口径，收益是否成立仍保留为 `unmeasured` 风险。
- **newly discovered ambiguities**：风险信号必须在生成前取得，以及输入单元的计算方式；本规格用 preflight 信号和 `input_unit` 数据契约消除，不改变上游范围。
- **clarification result**：用户在本 Issue 的澄清回复中选择 A，风险路由使用可解释规则表。该回复属于本阶段的用户输入，不是仓库实现证据；因此下游实现仍需按本规格补齐测试证据。

## 2. 问题、目标和边界

### 2.1 当前问题

当前 S4 只生成一版草稿；风险不同的内容承担相同成本。当前运行标识是随机的，正式写回虽有单文件原子替换，但没有持久的写入阶段状态。进程在多页写回或历史记录更新中被强制终止时，重跑可能重复追加归档/历史记录，或留下页面与记录不一致。

### 2.2 目标

1. 每个可处理知识簇在生成前得到可解释的 `low`、`medium` 或 `high` 路由。
2. `low`、`medium` 只执行 1 轮；`high` 最多执行 3 轮；所有轮次都保留原始输入、上一版草稿和质量结果。
3. 相邻两轮正文在统一换行后的 UTF-8 字节完全相同，立即停止，不再调用下一轮。
4. 任一轮违反来源、覆盖或忠实性硬约束时，不得提交该轮；回退到最近一版有效结果，首轮也无效时使用现有逐条 claim fallback。
5. 同一 `kb_dir` 同时只允许一个写入执行者。第二个执行者在 S5 之前失败，不修改正式页、归档、队列、来源索引或历史。
6. 写入前生成持久 prepare 状态和完整暂存输出；commit 过程被中断后，下一次相同输入自动从暂存状态继续，最终结果不重复、不丢页。
7. 报告质量、轮次、成本和恢复状态，明确“收益未测量”这一已接受风险；不自动声称 rethink 带来质量提升。

### 2.3 本期不做

1. 不做并发写入成功、CAS compare/retry 或冲突自动重试。
2. 不做 scheduler、watch、daemon、常驻进程、持久重试队列、告警系统或外部索引同步。
3. 不做模型 judge；风险判断只使用本地规则。
4. 不允许超过 3 轮；不提供无限轮数或用户侧轮数开关。
5. 不改变 `digest(new_dir, kb_dir)` 的调用形态，不新增恢复 CLI；恢复由稳定运行标识和状态文件自动完成。
6. 不重做 S1-S3、来源溯源、90 天归档和长文无损分页；只接入已有产物。

## 3. 用户场景

### SC-001 低/中风险单轮

- **角色**：手动运行 digest 的用户。
- **前置条件**：输入、知识库结构和现有 S1-S3 产物合法；规则没有命中 high。
- **操作**：运行 `digest new_dir kb_dir`。
- **结果**：生成 1 轮草稿，报告路由等级、信号、轮次和成本；沿用既有 faithfulness、provenance 和原子写回。

### SC-002 高风险三轮上限

- **前置条件**：命中任一 high 规则，且每轮正文都不同。
- **操作**：运行 digest。
- **结果**：最多完成 3 轮；第 3 轮完成后以 `max_rounds` 结束，绝不产生第 4 次生成调用。

### SC-003 相邻轮收敛

- **前置条件**：某高风险簇第 2 轮规范化正文与第 1 轮相同。
- **结果**：状态为 `converged`，轮数为 2，不执行第 3 轮；保留第 2 轮的质量和成本记录。

### SC-004 质量回退

- **前置条件**：新一轮的来源覆盖、组件覆盖或 faithfulness 不满足硬约束。
- **结果**：不提交坏轮；使用最近一版有效轮。若没有有效轮，使用现有逐条 claim fallback；报告 `fallback` 原因，不静默写入坏正文。质量指标只进入报告，不改变 D2 的收敛与轮数规则。

### SC-005 第二个写入者

- **前置条件**：一个 digest 已取得 `kb_dir` 写入锁并进入 prepare 或 commit。
- **操作**：第二个 digest 指向同一 `kb_dir`。
- **结果**：立即返回 `CONCURRENT_WRITER_NOT_ALLOWED`；不排队、不等待、不改变正式 KB。

### SC-006 中断后恢复

- **前置条件**：prepare 已持久化，commit 在写入若干目标后被强制终止。
- **操作**：使用相同 `new_dir`、`kb_dir` 和配置再次运行。
- **结果**：识别同一 `run_id`，复用已生成的暂存输出，不重新调用 rethink；已完成目标按期望指纹跳过，未完成目标继续提交；最终页面、归档和记录各一份。

### SC-007 已完成运行幂等重跑

- **前置条件**：同一稳定 `run_id` 已是 `committed`。
- **操作**：再次运行相同输入。
- **结果**：返回成功并标记 `already_committed`，不增加页面、归档、claim-history 或 source-index 重复记录。

### SC-008 状态损坏

- **前置条件**：恢复状态缺字段、暂存文件缺失或哈希不匹配。
- **结果**：返回 `RECOVERY_STATE_INVALID` 或 `RECOVERY_OUTPUT_MISSING`，保留诊断，不猜测、不覆盖正式页；用户修复/清理状态后再重跑。

### SC-009 dry-run

- **前置条件**：用户传入 `--dry-run`。
- **结果**：计算风险、轮次计划、质量/成本预估和写入计划，只写本次审计报告；不取得写入锁，不创建 recovery commit 状态，不修改正式页、归档、队列、来源索引和历史。
  - dry-run 不执行模型生成，因此质量字段（coverage、retained input、unsupported claim rate、faithfulness）统一为 `null`，不伪造预测值；成本部分只报告计划调用数和上限，实际 token、耗时和质量字段留给正式运行。

## 4. 功能需求

### 域 A：风险路由

- **FR-RISK-001**：系统必须为每个进入 S4 的知识簇生成一个 `RiskDecision`，且等级只能是 `low`、`medium`、`high`。来源：D1。
  - **场景**：Given 簇已有 S2/S3 产物，When 进入 S4，Then 运行记录包含完整信号、规则命中和等级。
- **FR-RISK-002**：系统必须使用以下生成前可取得的本地信号，不调用模型 judge：`cluster_tier`、`action`、`source_count`、`target_page_count`、`source_line_count`、`structured_line_ratio`、`coverage_risk`、`estimated_claim_count` 和 `estimated_component_count`。`target_page_count` 来自 S3，`max_doc_lines` 是全局配置常数，不是逐簇信号；其他估算来自 S1 原文和确定性组件预扫描；`estimated_claim_count` 与 `estimated_component_count` 是 content size/density 的具体度量。来源：D1；用户选择 A。
- **FR-RISK-003**：`structured_line_ratio` 必须定义为：含 FAQ、错误码、参数、URL、表格分隔符或代码围栏标记的非空来源行数 ÷ 非空来源行数；无非空行时为 `0`。`estimated_component_count` 是确定性组件预扫描得到的组件数；`estimated_claim_count` 是去除空行和明确 unsupported 行后，每条来源行先计为一个候选 claim unit 的数量。规则只读本地文本，不丢弃这些行。
- **FR-RISK-004**：high 规则必须是硬触发，命中任一即为 `high`：
  1. `action == merge_multiple`；这是现有 `retrieve` 对“至少保留两个相关目标页”的规范枚举值，不使用未映射的泛称 `merge`；
  2. `target_page_count >= 2`；这是对 `merge_multiple` 的防御性别名：当前 `retrieve` 中两者由同一“至少两个选中目标页”事实产生，命中时应同时记录两个规则名；保留该项用于防止未来上游数据映射漂移；
  3. `source_count >= 3`；
  4. `source_line_count > max_doc_lines`；
  5. `structured_line_ratio >= 0.30`；
  6. `coverage_risk == true`，即来源清单含无效来源、非 `passed|verified|ok` 状态，或 revise/merge 目标缺失；
  7. `cluster_tier == needs_review`。
  `cluster_tier` 的现有枚举为 `auto`、`needs_review`、`insufficient_signal`；`insufficient_signal` 先由 FR-RISK-007 门禁，不进入本规则生成路径。将 `needs_review` 保守映射为 high 是有意的成本取舍：它本已需要人工介入，先给它完整硬上限；只有新 `risk_rule_version` 经过真实样本校准后才能降为 medium。`coverage_complete` 是每轮生成后的硬校验，不参与生成前分级。
- **FR-RISK-005**：没有命中 high 时，命中任一 medium 规则即为 `medium`：
  1. `action == revise`；
  2. `source_count == 2`；
  3. `0.15 <= structured_line_ratio < 0.30`；
  4. `0.75 * max_doc_lines < source_line_count <= max_doc_lines`；
  5. `estimated_claim_count >= 8` 或 `estimated_component_count >= 5`。这两个数是 `risk-rules-v1` 的首版未校准阈值：它们选在高于单条/单组件的简单输入、又不依赖模型语义判断的位置，作为保守的确定性分层边界；不是来自实测分布，也不是质量保证。后续真实样本校准不在本期范围；只有新的规则版本才能改变它们。
  其余为 `low`。
- **FR-RISK-006**：规则输出必须包含 `rules_triggered`、`risk_level`、`max_rounds` 和 `decision_reason`；`max_rounds` 对 `low`/`medium` 为 1，对 `high` 为 3。规则版本写入 `risk_rule_version`，本规格首版为 `risk-rules-v1`。
- **FR-RISK-007**：`insufficient_signal` 簇不得进入生成或写回；它只沿用现有队列行为。若上游产物被错误传入，记录失败并不写正式页。

### 域 B：rethink 循环

- **FR-RETHINK-001**：系统必须按 `max_rounds` 执行生成轮次；每轮输入都包含原始来源全文、目标页旧正文（如有）、风险决策和上一轮草稿，不能只把上一轮正文当作下一轮唯一输入。风险决策在生成前由 preflight 信号计算；每轮生成后的实际 coverage 只做硬校验，不反向改变本次 `max_rounds`。来源：D2。
- **FR-RETHINK-002**：每轮必须生成可验证的正文、claims、coverage mapping、faithfulness 状态和质量指标；缺少任一硬约束字段的轮次视为无效候选。实际 `coverage_complete` 在本轮生成后计算；它不是风险路由的前置输入。
- **FR-RETHINK-003**：正文比较前只做换行归一：`CRLF` 转 `LF`，孤立 `CR` 转 `LF`；保留其他字符、空格、大小写、Unicode 和末尾换行。相邻两轮归一后的 UTF-8 字节完全相同即 `converged`，提前停止。
- **FR-RETHINK-004**：高风险最多 3 轮，低/中风险最多 1 轮；任何异常路径都不能突破上限。第 3 轮仍不同则以 `max_rounds` 结束。
- **FR-RETHINK-005**：每轮必须记录可解释质量事实：`coverage_ratio`（越高越好）、`retained_input_unit_ratio`（越高越好）、`unsupported_claim_rate`（越低越好）和 faithfulness 状态。它们只用于报告、回放和后续评估，不构成额外的轮次选择或自动质量裁判；不引入不可解释的总分。
- **FR-RETHINK-006**：每次生成调用都占用一个 `round_number`，包括违反来源校验、覆盖完整性或 faithfulness 硬约束的无效候选；无效候选记录 `status=invalid`，不得成为选中结果，也不能触发收敛。只要仍有轮次预算就继续生成，收敛只比较相邻且均为有效的完成轮；达到 `max_rounds` 后选择最近一版有效轮并记录 `fallback_reason`，首轮到上限都无有效结果时走现有 fallback。该回退只保护硬约束，不因质量指标变差而增加新的停止条件；不自动禁用后续运行。
- **FR-RETHINK-007**：首轮无有效结果时，必须沿用现有逐条 claim 拼接 fallback；只有 fallback 也无法通过来源和覆盖门禁时，才按既有失败语义返回，不写正式页。
- **FR-RETHINK-008**：每个簇必须记录 `rounds[]`，每轮至少包含 `round_number`、`status`、`body_sha256`、`candidate_claim_count`、`final_claim_count`、`unsupported_claim_count`、`unsupported_claim_rate`、`coverage_ratio`、`retained_input_unit_ratio`、`faithfulness_status`、`input_chars`、`output_chars`、`provider_input_tokens`、`provider_output_tokens`、`elapsed_ms` 和 `stop_reason`。没有 provider token 数据时字段值为 `null`，不得伪造为 0。
- **FR-RETHINK-009**：运行级成本必须包含 `generator_calls`、`total_input_chars`、`total_output_chars`、`total_provider_tokens`（可为 `null`）、`round_count` 和 `cost_ceiling_sum`；每簇的 `cost_ceiling` 对 high 为 3 calls、对其他等级为 1 call；运行级报告使用 `cost_ceiling_sum`，等于所有可处理簇的每簇上限之和，另记录实际 `generator_calls`。质量收益未测量时报告 `benefit_status: unmeasured`，不能宣称收益。

### 域 C：单写入与恢复状态

- **FR-RECOVERY-001**：系统必须在任何正式 KB mutation 前取得 `kb_dir` 专属写入锁；锁文件记录 `schema_version`、`run_id`、`execution_id`、`pid`、`started_at` 和 `target_kb`。`execution_id` 是每次命令调用新生成的 UUID，用来区分同一稳定 `run_id` 的不同执行实例；锁接管时必须同时核对锁中的 `run_id` 与状态中的 `run_id`，新的接管实例写入新的 `execution_id` 并递增 `recovery_attempts`。第二个不同执行者必须返回 `CONCURRENT_WRITER_NOT_ALLOWED`，不等待、不排队、不修改正式 KB。来源：D3。
- **FR-RECOVERY-002**：锁只保护本地单进程写入，不实现跨机器锁、CAS 或自动重试。锁残留时，只有在记录的进程已退出且 recovery 状态为 `prepared` 或 `committing` 时，下一次相同运行才可接管；进程仍存活时必须拒绝。实现和运维说明必须先按锁记录的 `pid` 检查进程是否仍存在，并确认该进程没有仍存活的子进程/同一运行的写入子任务；不能仅凭锁文件时间判断。进程已退出但状态为 `failed`、状态文件缺失或锁内容无法解析时，必须返回 `RECOVERY_STATE_INVALID`，不自动清理；确认没有活动进程且正式 KB 已人工核对后，用户可删除对应的精确 recovery 状态和锁文件，再按原命令重跑。
- **FR-RECOVERY-003**：`run_id` 必须稳定。它由规范化输入清单（相对路径、内容 SHA-256、来源清单）、S4/S5 配置和 `recovery_schema_version` 的规范 JSON 计算 SHA-256，再取固定长度标识。相同输入在未改变内容和配置时得到相同 `run_id`。
- **FR-RECOVERY-004**：系统必须使用 `_digest/recovery/<run_id>.json` 保存单份状态，状态至少包含 `schema_version`、`run_id`、`input_manifest_hash`、`status`、`prepared_at`、`committing_at`、`committed_at`、`plan_hash`、`staged_outputs`、`completed_outputs`、`recovery_attempts` 和 `last_error`。状态只能通过临时文件、flush、fsync、原子替换更新。
- **FR-RECOVERY-005**：prepare 阶段必须在正式写回前完成，并生成一个封闭、去重后的事务清单，覆盖本次运行的全部正式 KB 副作用：页面文件、页面归档内容、归档 `records.jsonl`、`claim-history.jsonl`、`source-index.jsonl`、现有队列和 `pending-review.jsonl`、`source-snapshots.jsonl`，以及归档清理产生的每一个过期归档内容文件删除。最终运行报告属于 recovery 审计投影，不是正式 KB 事务项：commit 完成后根据已提交状态原子生成；commit 失败时仍先写入可读失败报告，但不得把状态标为 `committed`。每个清单项必须包含 `operation`（`replace` 或 `delete`）、`kind`、`relative_target`、`staged_path`（delete 时为 `null`）、`size_bytes`、`before_sha256`（目标不存在时为 `null`）和 `after_sha256`（delete 时为 `null`）；delete 项是显式 tombstone，不以“缺少暂存文件”隐含删除。所有 replace 暂存内容和清单 fsync 后，才把状态标为 `prepared`；prepare 失败不得进入 commit。
- **FR-RECOVERY-006**：commit 阶段必须把 `prepared` 状态改为 `committing`，按封闭事务清单逐项处理；每完成一项就持久更新 `completed_outputs`。对 replace 项，目标当前 SHA-256 等于 `after_sha256` 时视为已完成并跳过，等于 `before_sha256` 时才可用同一暂存内容原子替换；两者都不相等时返回 `RECOVERY_STATE_INVALID`，不得覆盖目标，也不发起 CAS 重试。对 delete 项，目标不存在时视为完成，目标仍等于 `before_sha256` 时才删除，否则返回 `RECOVERY_STATE_INVALID`。所有目标完成后状态改为 `committed`，再释放锁。
- **FR-RECOVERY-007**：进程在 commit 任意位置终止后，后续相同运行必须复用现有暂存输出，不重新执行 S1-S4、模型调用或 rethink；已完成项跳过，未完成项继续。相同 `run_id` 的 claim-history、归档记录和运行报告必须按 `run_id` 去重，不能重复追加。
- **FR-RECOVERY-008**：`committed` 状态的相同运行再次执行时必须返回 `already_committed`，不产生新页面、归档、队列、来源索引或历史记录。若状态与暂存文件、事务清单或目标基线不一致，返回 `RECOVERY_STATE_INVALID`；不得自行猜测恢复。
- **FR-RECOVERY-009**：暂存文件缺失、SHA-256 不匹配、状态 JSON 无法解析或 `run_id`/输入清单不一致时，返回 `RECOVERY_OUTPUT_MISSING` 或 `RECOVERY_STATE_INVALID`，保留诊断，不覆盖正式页。现有命令失败输出继续包含阶段、失败输入和可重跑提示。
- **FR-RECOVERY-010**：恢复状态和锁属于 `_digest` 运行审计，不属于正式知识页；`--dry-run` 不创建 recovery 状态，不取得写入锁。

### 域 D：兼容与数据安全

- **FR-SAFE-001**：继续使用现有临时文件、fsync、原子 rename/replace、归档而非物理删除、来源状态检查和覆盖映射；新流程不得绕过 S6 provenance 门禁。
- **FR-SAFE-002**：任何路由、rethink、prepare、commit 或恢复失败都必须保留可读 run report 和恢复诊断；失败不得被标记为 `written` 或 `committed`。
- **FR-SAFE-003**：现有 `digest(new_dir, kb_dir)`、`--dry-run`、`--config`、`--max-doc-lines` 和既有退出码保持兼容；不得新增要求用户手工传 `--resume` 或 `--run-id`。
- **FR-SAFE-004**：来源、FAQ、错误码、参数、表格、代码块、长文和 90 天归档语义保持 Phase 0/1 验收结果；rethink 只可改进候选正文，不可借机删掉未覆盖内容。

## 5. 数据契约

### 5.1 RiskDecision

示例中的 `max_doc_lines` 是 `DigestSettings` 的全局配置快照，仅为回放记录输入条件；它不是逐簇可配置的风险信号，也不允许被单独覆盖。

```json
{
  "risk_rule_version": "risk-rules-v1",
  "risk_level": "high",
  "max_rounds": 3,
  "max_doc_lines": 300,
  "rules_triggered": ["action.merge_multiple", "source_line_count.over_max"],
  "signals": {
    "cluster_tier": "auto",
    "action": "merge_multiple",
    "source_count": 3,
    "target_page_count": 2,
    "source_line_count": 412,
    "structured_line_ratio": 0.34,
    "coverage_risk": false,
    "estimated_claim_count": 12,
    "estimated_component_count": 7
  },
  "decision_reason": "high: merge_multiple; source_line_count.over_max"
}
```

### 5.2 PreflightSignal 与输入单元

风险路由只读取生成前信号。`target_page_count` 来自 S3 的 `target_paths`；`estimated_component_count` 来自与现有 split 规则相同的只读预扫描；`estimated_claim_count` 是去空行和明确 unsupported 行后的候选 claim unit 数。`coverage_risk` 在生成前只表示来源状态无效或 revise/merge 缺少目标；生成后的 `coverage_complete` 由实际 `coverage_mapping` 和 `component_coverage` 计算。

一个 `input_unit` 是一条唯一的 `(raw_id, input_fragment)` 映射；`eligible_input_units` 是本轮输入中所有有效来源的这些映射，`retained_input_unit_ratio` = 有 `output_page` 且未被标记 `omitted` 的 input unit 数 ÷ eligible input unit 总数。无 eligible unit 时该比率为 `1.0`。

### 5.3 RethinkResult

```json
{
  "status": "converged",
  "selected_round": 2,
  "round_count": 2,
  "max_rounds": 3,
  "benefit_status": "unmeasured",
  "rounds": [
    {
      "round_number": 1,
      "status": "valid",
      "body_sha256": "...",
      "candidate_claim_count": 10,
      "final_claim_count": 9,
      "unsupported_claim_count": 1,
      "unsupported_claim_rate": 0.1,
      "coverage_ratio": 1.0,
      "retained_input_unit_ratio": 1.0,
      "faithfulness_status": "passed",
      "input_chars": 1200,
      "output_chars": 850,
      "provider_input_tokens": null,
      "provider_output_tokens": null,
      "elapsed_ms": 12,
      "stop_reason": null
    }
  ],
  "fallback_reason": null
}
```

`unsupported_claim_rate` = `unsupported_claim_count / candidate_claim_count`；分母为 0 时为 `0`。`body_sha256` 只用于审计和恢复核对，不作为质量判断的唯一依据。所有 hash 为实际 UTF-8 字节 SHA-256。

### 5.4 RecoveryState

`status` 只能是 `prepared`、`committing`、`committed` 或 `failed`。`staged_outputs` 是封闭、去重的事务清单，每项必须包含 `operation`、`relative_target`、`staged_path`、`kind`、`size_bytes`、`before_sha256` 和 `after_sha256`；`delete` 项的 `staged_path` 与 `after_sha256` 为 `null`，并作为显式 tombstone。清单必须覆盖页面、页面归档内容、归档记录、claim-history、source-index、队列/pending-review、source-snapshots 和全部归档清理删除；最终运行报告在 commit 后从状态生成，不属于此清单。`completed_outputs` 记录每项的目标、operation、完成状态和核对过的目标哈希。状态文件不得包含 API key、原始 secret 或 provider 私有路径。

### 5.5 状态转换

```text
preflight_validated (event) -> prepared -> committing -> committed
                 \-> failed
committing --(process stop)--> committing --(same stable run)--> committed
```

`preflight_validated` 是写入状态前的校验事件，不是 `RecoveryState.status` 值。只有锁持有者能从 `prepared` 进入 `committing`；只有封闭事务清单全部完成才能进入 `committed`。`failed` 不代表正式写入成功。

## 6. 模块边界

- `config.py`：保留现有设置；提供固定 `risk-rules-v1` 常量和版本，不增加独立风险 CLI 参数。
- `pipeline.py`：先用 S1-S3 产物和来源原文做 preflight，计算生成前风险路由；再按簇执行 rethink，并在每轮后计算实际 coverage 硬校验；将风险、轮次和成本写入 report；把现有 writeback 的页面、归档、来源、历史和队列输出先汇总为暂存清单，只有 commit 阶段才调用正式替换。
- `draft.py` / `faithfulness.py`：复用现有 claims、coverage、faithfulness 和 fallback；提供每轮可重复调用的生成边界，不改变来源规则。
- `writeback.py`：保留现有页面归档和原子写入；补充批量暂存、期望哈希核对和恢复提交所需的确定性输出。现有直接写回函数不得在 prepare 阶段修改正式页；若保留旧函数供测试，必须由新 commit 适配层统一调用。
- 新的 recovery 辅助模块：只负责 lock、状态 JSON、暂存输出和恢复，不实现 CAS、队列、调度或外部同步。
- `cli.py`：保持现有参数和退出码；将稳定运行、并发拒绝和恢复错误映射到现有错误输出格式。
- `tests/acceptance/`：增加规则、轮次、锁、状态恢复和幂等验收；保留全部 Phase 0/1 回归。

## 7. 失败语义与安全边界

- `CONCURRENT_WRITER_NOT_ALLOWED`：同库锁被其他活动执行持有；退出码沿用写入失败类别，标准错误必须包含错误码、`kb_dir` 作为失败输入和“关闭已有运行后重试”的提示；不等待、不排队。
- `RECOVERY_STATE_INVALID`：状态格式、身份或哈希关系不可信；不写正式页，保留状态和报告。
- `RECOVERY_OUTPUT_MISSING`：状态引用的暂存文件不存在或内容变化；不写正式页，保留诊断。
- `RETHINK_OUTPUT_INVALID`：单轮候选不合格；有上一有效轮时回退并继续，首轮使用现有 fallback；没有安全结果时沿用现有 faithfulness 失败退出。
- prepare 失败：不进入 commit，不改变正式页。
- commit 中断：不把半完成状态报告成成功；下一次相同运行继续暂存提交。
- 状态或暂存文件被外部删除/修改：停止恢复，要求先修复状态；不自动清理未知文件。用户若要清理，只能在确认对应进程已退出且正式 KB 已核对后删除该 `run_id` 的 recovery 状态和锁文件；不需要新 CLI。

## 8. 验收标准

- [ ] **AC-001**：给定一个仅命中 low 规则的 `new` 单页簇，生成调用数为 1、`max_rounds=1`、report 有完整 RiskDecision；不产生第 2 轮。← FR-RISK-001, FR-RISK-006, FR-RETHINK-004
- [ ] **AC-002**：分别构造 `revise`、双来源、0.15 边界、0.75 行数边界和 8 claims 场景；所有夹具固定 `cluster_tier=auto`、`coverage_risk=false`，并明确不命中其他 high 条件（`action`、`source_count`、`target_page_count`、`source_line_count`、`structured_line_ratio`）；未命中 high 时准确判为 medium；其余判为 low。← FR-RISK-004, FR-RISK-005
- [ ] **AC-003**：分别触发 `merge_multiple`、多目标、3 来源、超 `max_doc_lines`、结构化行比例 0.30、coverage_risk 和 `cluster_tier=needs_review`；每个场景准确判为 high 且最多 3 轮。← FR-RISK-004
- [ ] **AC-004**：高风险连续产生 3 个不同正文，验证只调用 3 轮；第 3 轮之后不存在第 4 次调用，状态为 `max_rounds`。← FR-RETHINK-004
- [ ] **AC-005**：高风险第 2 轮与第 1 轮在 CRLF/LF 归一后 UTF-8 字节相同，验证轮数为 2、状态为 `converged`、不调用第 3 轮；仅空格或正文字符变化不能误判收敛。← FR-RETHINK-003
- [ ] **AC-006**：对 high 簇注入一个覆盖不完整、来源无效或 faithfulness 失败的第 2 轮候选，再提供第 3 轮有效候选；验证坏轮计入轮次预算、继续生成但不参与收敛或选中，最多调用 3 轮，最终只写有效结果；首轮到上限都失败时验证现有逐条 claim fallback。← FR-RETHINK-006, FR-RETHINK-007
- [ ] **AC-007**：每轮和运行级报告包含规则、轮数、输入/输出字符、可用 token、耗时、质量指标、停止原因和 `benefit_status=unmeasured`；无 token 时为 `null`，不伪造成本。← FR-RETHINK-008, FR-RETHINK-009
- [ ] **AC-008**：启动两个指向同一 `kb_dir` 的写入执行；第二个返回 `CONCURRENT_WRITER_NOT_ALLOWED`，且正式页面、归档、队列、source-index、claim-history 均与启动前相同。← FR-RECOVERY-001, FR-RECOVERY-002
- [ ] **AC-009**：在 prepare 状态持久化后检查正式 KB，验证页面、归档、队列、来源索引和历史均未改变；暂存输出和状态存在且哈希正确。← FR-RECOVERY-004, FR-RECOVERY-005
- [ ] **AC-010**：在 commit 完成部分目标后注入强制终止，再用同一输入运行；验证不重新调用 S1-S4/rethink，已完成目标按 `after_sha256` 跳过，未完成目标仅在当前值仍等于 `before_sha256` 时提交，最终所有期望文件存在且哈希正确。← FR-RECOVERY-006, FR-RECOVERY-007
- [ ] **AC-011**：对 `committed` 的相同稳定运行重复执行；验证返回 `already_committed`，页面、归档、claim-history 和 source-index 不增加重复记录。← FR-RECOVERY-008
- [ ] **AC-012**：删除暂存文件、篡改暂存内容、破坏 JSON、改变输入清单或在 prepare 后修改目标文件后恢复；验证返回 `RECOVERY_OUTPUT_MISSING`/`RECOVERY_STATE_INVALID`，正式 KB 不被覆盖。← FR-RECOVERY-006, FR-RECOVERY-009
- [ ] **AC-013**：dry-run 触发 high 规则并产生多轮计划；验证正式目录、归档、队列、来源索引、历史和 recovery 状态均不改变，报告仍包含路由和成本计划。← FR-RECOVERY-010, FR-SAFE-003
- [ ] **AC-014**：运行既有 `python -m pytest tests/acceptance/test_phase0_digest.py -q` 与 `python -m pytest tests/acceptance/test_phase1_loss_prevention.py -q`，全部通过；FAQ、错误码、参数、链接、长文、来源快照、归档和结构 fail-closed 语义无回归。← FR-SAFE-001, FR-SAFE-004
- [ ] **AC-015**：对全部明确不做项做静态检查：无新 scheduler/daemon、CAS 自动重试、模型 judge、恢复 CLI、外部同步或超过 3 轮要求。← 2.3
- [ ] **AC-016**：给定被判为 `insufficient_signal` 的簇，验证不生成 RiskDecision、不执行 rethink、不生成正式页、归档、claim-history 或 source-index；只保留现有 `insufficient_signal` queue entry，并记录可诊断的跳过原因。← FR-RISK-007
- [ ] **AC-017**：在归档清理已生成 delete tombstone、但清单尚未全部提交时注入强制终止；用同一运行恢复，验证过期归档内容最终只删除一次、`records.jsonl`/`source-snapshots.jsonl` 只保留元数据、其他页面和历史不重复，清理中途不会报告 `committed`。← FR-RECOVERY-005, FR-RECOVERY-006, FR-RECOVERY-007

## 9. 宪法检查与取舍

- **P0：能删除就删除**：不加恢复 CLI、重试队列、告警、CAS、调度或 provider 抽象；恢复由现有命令和稳定状态自动完成。
- **P1：能复用就复用**：复用 S1-S6、`max_doc_lines`、claims、coverage、faithfulness、现有原子写入、归档和 report；只补风险路由与 durable recovery seam。
- **P2：最小持久化**：只增加单份 recovery state、暂存输出和单库锁；不建完整 append-only journal 或事务框架。
- **P3：不为未来扩展预埋接口**：不实现并发成功、CAS retry、scheduler、daemon、外部索引和模型 judge，只记录未来风险。

关键取舍：质量收益尚无 Phase 0/1 实测证据，因此规格要求记录可复现的质量/成本事实和 `benefit_status=unmeasured`，但不设置自动关闭 rethink 的长期机制。安全优先于质量：坏轮回退，不能牺牲来源和覆盖完整性。

## 10. 风险、假设和下游输入

### 已接受风险

- 本地规则可能漏判语义复杂度；按来源行估算 claim unit 会对“单行多个 claim”和“单行只有 URL/参数名”等极端输入产生偏差；后续用真实样本校准，但本期不做标定工具。
- 校准触发口径：至少积累 3 个真实样本组的 replay 报告后，才允许基于覆盖率、成本和分层误差证据提出新的规则版本；变更必须同时更新 `risk_rule_version`、规则表和对应验收，不在本期加入自动标定工具。
- rethink 可能增加成本而没有质量收益；报告必须显示成本和 `unmeasured`，不把实验结果写成保证。
- 无 CAS 意味着本期不处理外部程序绕过本地锁直接修改目标文件；本期边界是同一 CLI 的单写入者。
- recovery state 或暂存文件损坏时自动恢复会停止，避免猜测覆盖；用户需先修复状态。

### 实现假设

- 现有 S4 可以被重复调用或抽出可注入的本地生成边界；不得新增外部 provider 依赖。
- 同一输入清单和配置能生成稳定 `run_id`；配置或内容变化即产生新的运行身份。
- 现有页面、归档、JSONL 和 report 输出都能加入 `run_id` 去重字段而不破坏既有消费者。
- 锁接管的平台实现必须使用 `os.kill(pid, 0)` 或等效的进程存活检查；子进程/同一运行写入任务无法可靠确认时按“仍可能活动”处理，不自动接管，具体跨平台命令和测试由 build-plan 落实。

### 交给 build-plan 的精确输入

build-plan 必须把本规格的全部 `FR-*`、`AC-001` 至 `AC-017` 拆成实现顺序、文件变更、测试证据和失败恢复演练。优先顺序：规则/轮次 → insufficient_signal 门禁 → 成本与报告 → 锁 → prepare 封闭事务清单与基线核对 → commit 恢复/幂等 → cleanup tombstone → Phase 0/1 回归。不得扩大到第 2.3 节的排除项。

## 11. 阶段执行记录

- `spec-specify`：executed；本规格覆盖目标、边界、需求、场景、数据、失败语义、验收和风险。
- `spec-clarify`：executed；处理 1 个重大轴：采用可解释规则表；用户选择 A；未重新询问已锁定决定。
- `simplicity-guard`：由正式 `wh-review` 按配置执行；本阶段不单独调用。
- `wh-review`：本阶段已提交正式审查；规格正文不预写 verdict，实际 provider、verdict 和意见以 canonical result 为准；完成后由交接卡记录最终结果。
