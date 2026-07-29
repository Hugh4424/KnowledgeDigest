# KnowledgeDigest 真实语料 Summary+Evidence 验收报告

1. **事实｜根因与回归。** 用户授权后，将 provider 请求边界从线程内 `fork()` 改为 `spawn` 子进程；并发4、180秒硬超时、`KD_LLM_RETRY_ATTEMPTS=0` 和失败回退语义保持不变。回归：专项 `67 passed`，全套 `176 passed`，`git diff --check` 通过。

2. **事实｜正式运行。** 隔离根 `/tmp/kd-real-pilot-latest.diIrxn` 的 run `run-da97cdadc9bc43b5931e81e9148a7850` 退出0：3/3来源审计，28/28 batch/provider calls，claims `1..10`、source chars `10..1400`，全部 `valid`；3/3 `selected_round=1`、Summary `validated`、无 fallback；coverage/retention/faithfulness=`1/1/passed`，unsupported=`0`。

3. **事实｜Evidence 与 provenance。** S5 `3/3 success`，S6 `211` 条且必填字段、source URI、fragment locator、content fingerprint 完整；12/12预选事实保留；3个正式页面均含 `## Summary` 和 `## Evidence`，211/211 claim 与原始材料和页面 Evidence 一致。

4. **事实与人工判断｜replay。** 固定种子 `20260728` 抽查10条摘要，10/10保留数字、日期、范围、条件词、路径、命令、函数名和工具名。replay `run-ee0c9d2aaa864e3db17da8c507448d14` 退出0，28 calls；S5/S6仍成功，claim/provenance/page集合不漂移，正式页 hash `cmp=0`；反向审计为退出 `1`（210/211）→恢复后退出 `0`（211）。正式+replay共56 calls，未超过70。

5. **结论｜建议受控试用。** 本轮硬门禁和 replay 全通过，Summary 可在受控场景试用；fallback 比例为 `0/3=0%`，但不是所有未来 provider 运行的保证。95条摘要只人工抽查10条，provider token 用量仍未记录。因此不自动修改 `llm_summary_enabled` 默认值，继续保持 `false`。
