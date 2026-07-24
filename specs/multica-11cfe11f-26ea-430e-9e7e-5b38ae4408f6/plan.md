# 实施计划：多轮 rethink 与单写入恢复

## 目标与边界

在既有 `digest(new_dir, kb_dir)` 实现：本地可解释风险路由；low/medium 一轮、high 最多三轮；逐轮来源/覆盖/faithfulness 门禁；单库写锁；稳定 `run_id`；prepare/commit 恢复；页面、归档、JSONL、队列、来源索引、历史和过期归档清理的安全提交。

不做新 CLI、模型 judge、CAS/自动重试、scheduler/daemon、外部同步或超过三轮。`--dry-run` 只输出风险、调用上限和写入计划；不拿锁、不建 recovery、不调用生成、不写正式 KB。

## 已核对的现状与取舍

- `pipeline.py` 现用随机运行目录，并在 `writeback()` 后直接更新来源索引、claim-history、pending-review 和归档清理；这些副作用要收敛为 prepare 的封闭清单，不能保留半直接写入。
- `retrieve.py` 现仅让 `auto` 进 S3；实现让 `needs_review` 走既有检索/生成并固定为 high。`insufficient_signal` 仍只进队列，不生成 `RiskDecision`、rethink 或正式输出。
- 复用 `draft.py`/`faithfulness.py` 的 claims、coverage、fallback，复用 `writeback.py` 的临时文件、fsync、原子替换和归档。只新增最小 `recovery.py`，不建通用事务框架。
- 现有验收已具 CLI 临时 KB 与 `monkeypatch` 故障注入；恢复演练沿用这些方式。未跟踪 `workflowhub/` 不纳入实现。

研究已执行：核对本地实现、状态边界与测试布局；不需外部研究。关键风险是分散副作用，处理方式是先生成所有最终字节和基线 hash，再允许 commit。

## 数据契约

### 风险与轮次

- 在 S3 决策、S1/S2 原文预扫描和来源状态上构建 `RiskDecision`：`risk-rules-v1`、完整 signals、rules_triggered、risk_level、max_rounds、decision_reason、max_doc_lines 快照。
- 规则严格实现 structured-line ratio、候选 claim unit、组件预扫描、coverage risk 与规格的 high/medium 阈值，无模型判断、无新配置。
- `merge_multiple` 与 `target_page_count >= 2` 同源命中时，`rules_triggered` 必须同时记录两个规则名；不能只记录一个抽象 high 原因。
- 每轮输入包含原始来源全文、旧目标正文（如有）、风险决定和上一轮草稿。每轮记录正文 SHA-256、claims、coverage、faithfulness、字符数、token（不可用为 `null`）、耗时和 stop reason。
- 只比较相邻且有效的完成轮：CRLF/孤立 CR 转 LF 后比较 UTF-8 字节。无效轮消耗预算但不选中、不触发收敛；没有有效轮时走既有 claim fallback。
- 正式 run 报告实际 generator_calls、每簇 ceiling、运行级 ceiling sum 与 `benefit_status: unmeasured`。dry-run 不生成：coverage、retained_input_unit_ratio、unsupported_claim_rate、faithfulness 等质量字段明确为 `null`，成本只给 planned calls/ceilings。

### 恢复与事务

- 规范化输入清单（相对路径、内容 SHA-256、来源清单）、S4/S5 配置和 recovery schema 计算稳定 `run_id`。
- `_digest/recovery/<run_id>.json` 是唯一 `RecoveryState`，至少含 schema_version、run_id、input_manifest_hash、status、prepared_at、committing_at、committed_at、plan_hash、staged_outputs、completed_outputs、`recovery_attempts` 和 last_error。
- 每次命令调用生成新的 UUID `execution_id`；锁记录 schema_version、run_id、execution_id、pid、started_at、target_kb。接管只在旧进程及同 run 写入子任务确认退出、状态为 prepared/committing 时发生；接管者写新 execution_id，并将 recovery_attempts 加一。状态/锁更新都经临时文件、flush、fsync、原子替换。
- `recovery.py` 负责锁、PID/子任务检查、状态校验和安全接管。活进程或无法证明安全时拒绝；第二写入者返回 `CONCURRENT_WRITER_NOT_ALLOWED`。
- `writeback.py` 分为“构建封闭暂存输出”和“按清单提交”。replace/delete 都含 relative target、staged path、size、before/after SHA-256；delete 为显式 tombstone。
- prepare 完整暂存和 fsync 后才写 prepared。commit 持久化 committing 与每项 completed_outputs；before hash 匹配才替换/删除，after hash（或 delete 不存在）表示完成，其余 `RECOVERY_STATE_INVALID`。
- 相同 committed run 返回 `already_committed`。中断恢复复用暂存、不重做 S1-S4/rethink；报告由状态投影，失败不标 committed。

## 实施阶段

### Phase 1：规则、轮次、报告

1. 在 `config.py` 固定 `risk-rules-v1`，不加 CLI 参数。
2. 修改 `cluster.py`/`retrieve.py`/`pipeline.py`：needs_review 可处理且 high；insufficient_signal 保持队列和可诊断跳过。
3. 在 `draft.py`/`faithfulness.py` 加 preflight、逐轮边界、硬校验、newline-only 收敛和 fallback，复用现有 claims/coverage。
4. 在 `pipeline.py` 输出风险、rounds、质量和成本；dry-run 明确输出 null 质量字段和调用计划。
5. 新增规则边界、别名双命中、三轮上限、收敛、无效候选、fallback、报告与 insufficient_signal 验收。

完成条件：AC-001～007、016 通过；无第四调用、模型 judge 或 insufficient_signal 正式输出。

### Phase 2：prepare 与单写锁

1. 用稳定 manifest/run_id 建立恢复身份，保留运行报告投影。
2. 新建 `recovery.py`：lock metadata、execution_id、PID/子任务检查、recovery_attempts 接管、state schema/耐久写。
3. 把页面、归档内容/records、claim-history、pending-review、source-index、source snapshots、队列和归档清理的最终字节收敛为一个去重清单。
4. 所有正式副作用移入暂存；prepare 前 KB 不变。dry-run 走只读计划分支。
5. 测试活动锁拒绝、prepare 无 mutation、暂存 hash、execution takeover 和 dry-run 零 mutation。

完成条件：AC-008、009、013 通过。

### Phase 3：commit、恢复、CLI 错误与 tombstone

1. `pipeline.py` 编排 prepared→committing→committed，逐项更新状态；恢复只提交未完成项。
2. `writeback.py` 按 before/after hash 提交 replace/delete；基线冲突 fail-closed。
3. 对 records、history、index、pending-review、snapshots、报告按 run_id 去重。
4. 在 `cli.py`/错误边界把 `CONCURRENT_WRITER_NOT_ALLOWED`、`RECOVERY_STATE_INVALID`、`RECOVERY_OUTPUT_MISSING` 映射进现有错误格式：stderr 含 code、失败输入 `kb_dir` 和重跑提示；既有退出码不变。
5. 把归档清理作为 tombstone 纳入同一清单，保留 records/source snapshots 元数据；用故障注入验证部分 commit、重跑、错误码、already_committed 和清理中断。

完成条件：AC-010～012、017 与失败语义通过；无基线覆盖、重复 JSONL、隐式删除或错误 committed。

### Phase 4：回归与交接

- 运行新验收集，以及：
  - `python -m pytest tests/acceptance/test_phase0_digest.py -q`
  - `python -m pytest tests/acceptance/test_phase1_loss_prevention.py -q`
- 静态排除 scheduler/daemon、CAS retry、模型 judge、恢复 CLI、外部同步和超过三轮。
- 以 fresh fixture 复核 CLI/退出码、pages、archives、records、history、index、queues 无重复或遗漏。
- 输出三份交接证据：逐 AC trace matrix（实现任务、测试、结果）、恢复演练记录（prepare/部分 commit/恢复/cleanup）和 CLI 兼容报告（3 错误码、kb_dir、提示、退出码）。

完成条件：AC-014、015 通过，AC-001～017 均可追溯。

## 验收映射

| 验收 | 主要落点 | 证据 |
| --- | --- | --- |
| AC-001～003、016 | `config.py`、`cluster.py`、`retrieve.py`、`draft.py`、`pipeline.py` | 规则边界、needs_review、insufficient_signal、merge_multiple/多目标双规则名 |
| AC-004～007 | `draft.py`、`faithfulness.py`、`pipeline.py` | 轮次、收敛/坏轮/fallback、正式报告和 dry-run null 质量字段 |
| AC-008～009、013 | `recovery.py`、`writeback.py`、`pipeline.py` | 两执行者、prepare snapshot、hash、execution takeover、dry-run |
| AC-010～012 | `recovery.py`、`writeback.py`、`pipeline.py`、`cli.py` | commit 故障、恢复、冲突、already_committed、stderr/error code |
| AC-017 | `provenance.py`、`writeback.py`、`recovery.py` | cleanup tombstone 中断恢复 |
| AC-014～015 | 全流程/CLI | 两套回归、静态范围检查、AC trace matrix |

恢复测试必须先保存 KB snapshot，再断言允许与禁止变化；不能只看退出码。中断使用已有 `monkeypatch` 或明确提交钩子，不依赖真实杀进程。

## 风险、回滚与下游输入

最大风险是副作用分散；用预先暂存的完整清单与 before hash 消除半提交。PID/子任务无法确认时拒绝接管，不加定时清锁工具。规则未校准，只记录可回放 facts，不自动调参。prepare 前无正式变更；commit 后仅在匹配基线时继续，不用旧 rollback 覆盖外部写入。

build-code 输入：已接受 `spec.md`、本计划、任务清单、AC-001～017、当前文件边界和“`workflowhub/` 不碰”。先完成纯规则测试，再重构写回；不要并行修改 `pipeline.py` 与 `writeback.py` 的同一事务编排区。
