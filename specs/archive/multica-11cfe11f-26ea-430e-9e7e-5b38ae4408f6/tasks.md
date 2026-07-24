# 实施任务清单：多轮 rethink 与单写入恢复

## 规则

- 每项完成后跑对应测试；Phase 3 前不得替换正式 commit 路径。
- 测试只写临时目录；不触碰未跟踪 `workflowhub/`。
- 恢复异常一律断言正式 KB snapshot 处于安全状态。

| ID | 动作与影响区 | 需求 | 实现依赖 / 验证依赖 | 验证 | 并行性 |
| --- | --- | --- | --- | --- | --- |
| T01 | 补共享验收助手：report/KB snapshot、固定来源/簇/轮次夹具、故障注入。`tests/acceptance/`。 | AC-001～017 | 实现：无；验证：无 | 现有回归仍通过。 | 可与 T02 并行。 |
| T02 | 固定 `risk-rules-v1` 和纯信号/规则函数。`config.py`、`draft.py`。 | FR-RISK-001～006；AC-001～003 | 实现：无；验证：T01 可选 | 0.15/0.30/0.75/8/5 边界；merge_multiple 与 target_page_count>=2 同源时记录两个规则名。 | 可与 T01 并行。 |
| T03 | needs_review 进入既有 S3/S4 并为 high；insufficient_signal 只队列/诊断。`cluster.py`、`retrieve.py`、`pipeline.py`。 | FR-RISK-004、007；AC-003、016 | 实现：T02；验证：T01 | high 计划；无 RiskDecision/草稿/正式输出。 | 可与 T04 并行；T05 统一改 pipeline 集成。 |
| T04 | 抽逐轮生成边界，复用 claims/coverage/faithfulness/fallback。`draft.py`、`faithfulness.py`。 | FR-RETHINK-001、002、005、008 | 实现：T02；验证：T01 | 每轮字段完整；未知 token=null；硬缺失 invalid。 | 可与 T03 并行。 |
| T05 | 轮次控制、newline-only 收敛、无效轮预算和回退。`draft.py`、`pipeline.py`。 | FR-RETHINK-003、004、006、007；AC-004～006 | 实现：T03、T04；验证：T01 | 3 轮无第 4；CRLF/LF 收敛；空格不同不收敛。 | 串行。 |
| T06 | 风险/轮次/质量/成本报告和 dry-run 计划。`pipeline.py`。 | FR-RISK-006；FR-RETHINK-009；AC-007、013 | 实现：T03、T05；验证：T01 | 正式 null token、calls/ceiling；dry-run 有 routing/计划成本，quality/faithfulness 字段全为 null。 | 串行。 |
| T07 | 稳定 run manifest/run_id。`pipeline.py`、测试。 | FR-RECOVERY-003；AC-010、011 | 实现：T06；验证：T01 | 同输入稳定，内容/配置改变即不同。 | 可与 T08 并行。 |
| T08 | 新建 `recovery.py`：锁、state、execution_id、PID/子任务检查、接管/recovery_attempts、错误码。 | FR-RECOVERY-001、002、004、009 | 实现：无；验证：T01 | 活锁拒绝；仅安全 prepared/committing 残锁接管；接管生成新 execution_id 且 attempts+1；坏状态 fail-closed。 | 可与 T07 并行。 |
| T09 | 生成封闭去重 staged-output 清单，覆盖所有 replace/delete tombstone。`writeback.py`、`provenance.py`、`pipeline.py`。 | FR-RECOVERY-004、005；FR-SAFE-001 | 实现：T05、T07、T08；验证：T01 | 页面、归档、records、history、index、queues、snapshots、cleanup 均覆盖且 hash 正确。 | 串行。 |
| T10 | 接入 prepare：锁、暂存/fsync、prepared state、可读报告。 | FR-RECOVERY-001、004、005；AC-008、009 | 实现：T09；验证：T01 | prepare 后 KB snapshot 不变。 | 串行。 |
| T11 | dry-run 隔离：无锁、无 recovery、无生成调用。`pipeline.py`、测试。 | FR-RECOVERY-010；FR-SAFE-003；AC-013 | 实现：T06、T08、T10；验证：T01 | 正式路径/recovery 不变；quality/faithfulness=null；成本仅 planned calls/ceilings。 | 可与 T12 并行。 |
| T12 | commit 状态机：after/before/conflict 分支和显式 delete。 | FR-RECOVERY-006；FR-SAFE-002 | 实现：T10；验证：T01 | replace/delete 三分支单测。 | 可与 T11 并行后合并。 |
| T13 | 恢复、已完成跳过、already_committed、run_id 去重。 | FR-RECOVERY-007、008；AC-010、011 | 实现：T12；验证：T01 | 部分 commit 重跑不做 S1-S4/rethink；各记录一份。 | 串行。 |
| T14 | 实现 CLI 错误映射。`cli.py`、错误辅助、验收测试。 | FR-SAFE-003；AC-008、012 | 实现：T08、T13；验证：T01 | 三个 error code 均在 stderr；失败输入为 kb_dir；有重跑提示；退出码保持既有失败类别。 | 可与 T15 并行。 |
| T15 | cleanup tombstone 与中断恢复。`provenance.py`、`writeback.py`、`pipeline.py`。 | FR-RECOVERY-005～007；AC-017 | 实现：T12、T13；验证：T01 | 只删除一次，records/snapshots 元数据保留。 | 可与 T14 并行。 |
| T16 | 不可信恢复测试：缺暂存、篡改 hash、坏 JSON、输入/基线冲突。 | FR-RECOVERY-006、009；AC-012 | 实现：T13、T15；验证：T01 | 正确错误码，KB 不覆盖。 | 可与 T17 并行。 |
| T17 | 新旧回归和范围静态检查。 | FR-SAFE-001～004；AC-014、015 | 实现：T11、T15；验证：无 | 两条 pytest 命令；无排除项实现。 | 可与 T16 并行。 |
| T18 | 生成可交接证据包：AC trace matrix、恢复演练记录、CLI 兼容报告、工作树边界检查。 | AC-001～017 | 实现：T14、T16、T17；验证：无 | matrix 含 AC→任务→测试→结果；drill 含 prepare/部分 commit/recovery/cleanup；CLI 报告含 code/kb_dir/hint/exit；确认不含 workflowhub 改动。 | 最后。 |

关键路径：`T02 → T03/T04 → T05 → T06 → T07/T08 → T09 → T10 → T12 → T13 → T14/T15 → T16/T17 → T18`。

## build-code 交付要求

- AC-001～017 的测试名/命令结果和 AC trace matrix。
- 风险/轮次 report、prepare 清单、恢复演练、CLI 兼容报告和范围静态检查。
- 未解决风险必须明确；不得以自动重试或 `--resume` CLI 绕过。
- 未满足正式审查、AC 证据、Phase 0/1 回归或 `workflowhub/` 边界前，不交 verify-code。
