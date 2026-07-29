# Blocked

- 2026-07-28：qwen3.6 正式运行连续3次 provider 失败，按任务书停止该项。
  - 第1次：`provider request failed (The read operation timed out)`
  - 第2次：`provider request failed (The read operation timed out)`
  - 第3次：`429: provider returned a non-success status`
- 影响：无 qwen S4/S5/S6 正式产物，不能执行 qwen 重放、A/B 质量对比、selected_round/fallback_reason 统计或 qwen 事实/溯源验收。
- 未影响：control 正式产物、12条事实检查、10条 provenance 抽查、S4/S5/S6 检查、反向验证、仓库边界核对。
- 证据：`/tmp/kd-real-pilot.xMAHxZ/qwen/_digest/runs/` 下3个失败 run，全部 `official_write.status=pending`。

## S3 修复后重跑

- 2026-07-28：独立小请求在20秒内返回 `OK`，但同一真实语料三次正式 qwen 运行均在约60秒 read timeout。
- 影响：仍无 qwen S4/S5/S6、A/B 页面质量和重放稳定性证据。
- 诊断边界：endpoint、API key、model 基础连通性已确认；正式 prompt 为30,741～55,941字符，并要求回传50～110条 claim。长输入/长输出超出当前调用窗口是证据支持的方向，但尚未通过分批试验确认。
- 原始证据：`/tmp/kd-real-pilot-s3.VziVwd/logs/`、`/tmp/kd-real-pilot-s3.VziVwd/qwen/_digest/runs/`；三个 run 均为 `official_write.status=pending`。
- 已知未阻塞风险：`routing-jaccard-v2` 使用全文 Jaccard；长页面可能稀释相关词并保守地产生新页。修复该问题需要章节级标注样本和独立路由评估，不在本次两页负样本上继续拍阈值。

## 分批生成后的状态

- 原“所有真实请求必超时”阻塞已部分解除：16批正式运行和16批重放均成功，事实、结构、coverage、provenance 与页面 hash 门禁通过。
- 仍有可靠性风险：一次冷缓存结构安全运行在约7分半后出现单批60秒 timeout；成功重试部分命中 provider 缓存，尚不能证明冷缓存成功率。
- 当前效果阻塞：qwen 相对 control 只增加4个空行，没有可见知识提炼收益。现有“所有 claim 必须逐字进入正文”契约与“压缩提炼”目标冲突，需要新规格，不应继续靠调 timeout 或批大小掩盖。
- 成本证据缺口：provider 响应的 `usage` 尚未进入内部结果，真实报告 `total_provider_tokens=null`；当前只能审计调用数、字符数和耗时，不能据此做 token 成本结论。

## Summary+Evidence 后续阻塞

- 2026-07-28：最终摘要运行的安全门禁通过，但10条标注样本的限定词/数字机械预检约7/10，且重放3页中1页 hash 漂移。
- 影响：摘要只能作为实验能力，不能正式开启；Evidence、S5、S6 不受影响。
- 最小解法：增加确定性 provider 参数并强化摘要保留数字/范围/条件/路径规则，再做一次小样本运行与重放；不放宽 summary 引用、faithfulness、provenance 门禁。
- 证据：`/tmp/kd-real-pilot-s3.VziVwd/qwen-summary-final/{_digest/runs,}-*`、`qwen-summary-final-{before,after}-replay.sha256`。
- 2026-07-28：加入 `temperature=0` 后的最终复测 `run-9df6c678308a40fd90d37f74c8a022ea` 约9分钟仍卡在 provider HTTP 响应，安全中止，`official_write=pending`。
- 影响：无法证明确定性参数是否修复 replay 漂移；全量请求规模仍过大，未把中止结果当作成功或失败的语义质量证据。
- 复核：短请求 `HTTP 200 / 0.47s`；10条 claim 摘要 `31.79s` 成功。provider 连通性正常，后续应缩小批次而不是继续增加全量等待时间。
- 解除部分：10条标注事实小样本已成功完成并 replay hash `cmp=0`；剩余阻塞仅针对大批次全量运行。

- 2026-07-28 修复后正式现场：`/tmp/kd-real-pilot-final.postfix/`，run `run-3cc98eab52ec419d8dd3aacfda44e8d8`。
  - 配置为 Summary 开启、10 claims/1500 source chars、`KD_LLM_TIMEOUT_SECONDS=180`、`KD_LLM_RETRY_ATTEMPTS=0`。
  - S3 后首个真实 HTTPS 读取停在 Python `_ssl__SSLSocket_read -> poll`；约3分30秒无响应，人工 `SIGALRM` 后原始错误为 `provider request failed (deadline exceeded after 180s)`，CLI 退出码 `1`。
  - `official_write.status=pending`，无 S4/S5/S6、正式页或 replay；现场目录和 `formal-run.log` 保留。该次 provider 请求计1次。
  - 计时器第一版未在现场自动触发；改为 Timer 线程发送 `SIGALRM`，专项/全套回归后为 `62/171 passed`。

## fork 边界后的最终验收

- 2026-07-28：fork 子进程边界后的三材料正式运行 `run-5163f070cdd747cba789e7dca7c04dae` 成功，28/28 provider calls，3/3 selected、Summary validated，S5 `3/3 success`、S6 `211`，无 fallback。
- 原样 replay `run-3a5185663a7a412290a0a1ad1415c5f7` 成功，28 calls；三页正式页 hash 前后 `cmp=0`，hash 记录在 `/tmp/kd-real-pilot-final.fork/before-replay.sha256` 与 `after-replay.sha256`。
- 12/12 预选事实、211/211 claim 的规范化内容/locator/source URI、Evidence 和 provenance 通过；但人工摘要为 `9/10`：G2 丢失“最多3篇”和 `select_detail_lines()` 标识符。
- 因 G2 摘要违反数字/标识符保真要求，结论为“有条件试用”，`llm_summary_enabled` 默认保持关闭；不能把安全 Evidence 结论扩大为摘要质量已达标。
- 收尾修复：`_validate_summary` 加入数字和关键路径/命令/函数/工具标识符的确定性保真门禁；缺失时 Summary rejected、Evidence 保留。回归为专项 `63 passed`、全套 `172 passed`、skipped=0。
- 该门禁加入在上述正式运行/replay 之后，且两次运行共56 provider calls；未再伪造新全量结果。新门禁下的三材料全量复验是剩余缺口，故最终不是“建议试用”。
- 根因已修复：模型遗漏精确限制时，系统从 source claim 自动追加精确保真段；真实 qwen G2 定向复验通过，`selected_round=1`、Summary validated、函数名/12/3/Evidence 均保留。
- 剩余缺口仅为新修复后的三材料全量正式运行和 replay；不能用一次定向调用替代该正式门禁。

## 本轮任务书执行

- 2026-07-28：单材料正式运行第1次 `run-e4f0bb143edd4d8eb7979dfe1c40b37c` 使用 10 claims/1500 source chars、timeout=180s；TLS 连接已建立，但约5分钟未收到 provider 响应，S4 未产出，`official_write.status=pending`，进程由安全中止退出码 `130`。
- 原始现场：`/tmp/kd-real-pilot-final.zc6jq6/task1-run.log` 为空（无 provider 错误文本）；对应 `report.json`、S1-S3 和锁文件均保留。短请求同一 endpoint/model 返回 `OK`，不能把该次卡住归因于 key 或基础连通性。
- 解除：单材料第2次新隔离运行成功，运行目录 `/tmp/kd-real-pilot-final.zc6jq6/task1-retry/`；上述失败现场仍保留，未写正式仓库。

- 2026-07-28：任务2三份材料连续3次 provider 阻塞，按任务书停止。
  - `run-a86fff63c6784964a91a86c1e46b88c4`、`run-c2751b39b6cf4aa09bbbd3fc1f8380f0`、`run-e915916459e54ee2903c6c138f63280d` 均使用 10 claims/1500 source chars、timeout=180s。
  - 三次均各发起 1 次 provider 请求并停在 S3 后首个 HTTPS 响应；任务2累计 3 次尝试。无 S4/S5/S6、无正式页、`official_write.status=pending`；三份原始日志均为空，进程安全中止退出码 `130`。
  - 证据目录：`/tmp/kd-real-pilot-final.zc6jq6/task2-final/`、`task2-retry/`、`task2-third/`。未执行 replay；3/3 selected_round、3/3 Summary、12条事实、10条摘要样本和 replay hash 均未验证。

## 修复后的验证

- 根因：旧逻辑为保护 atomic code/parameter component，会让单批超过配置上限；实测出现 17 条和 11 条 claim 的 provider batch。
- 修复：仅 Summary 模式按 claim 拆 oversized atomic component；完整 source 不交给模型重组，仍由系统确定性写入 Evidence。修复后诊断为三份材料 `max_claims=10`、`max_source_chars<=1500`、`oversized=0`。
- 证据：专项 `59 passed`、全套 `168 passed`；真实 qwen smoke `prompt=9241`、`source=1400`、`claims=8`，`30.24s` 返回 `summary_status=validated`、returned claims=8。
- 剩余边界：原任务三次正式运行上限已用完，未用修复后代码重跑三材料；因此 3/3、12/12、10/10、replay 仍是未验证项。

## 并发修复后的未验证项

- 2026-07-28：已确认全量慢的直接原因是 28 个独立 provider batch 串行执行；上一轮正式运行累计 `912.139s` provider 时间（约15.2分钟），单批 `25.431～48.557s`，原样 replay 还需再执行一遍。
- 已实现默认 `llm_batch_concurrency=4` 的有界并发；结果按 batch_index 顺序合并，任一 batch 失败仍整份 draft fallback，Evidence、coverage、S5、S6 门禁未放宽。

## 最新代码三材料复验现场

- 2026-07-28：全新隔离根 `/tmp/kd-real-pilot-latest.UUSet0` 的唯一正式运行 `run-5a6d73a4a7324138b91377bf3a1b8eda` 在 S3 后退出码 `1`。
- 原始错误：并发 worker 内 `fork()` 触发 macOS `objc_initializeAfterForkError`，随后 `provider request failed (child returned no result)`；不是成功响应，不能计为 provider PASS。
- 现场状态：S1/S2/S3 和 structure-check 已写；S4、S5、S6、正式页均未产生；`official_write.status=pending`；无自动重试。
- 按任务书连续同类错误即停且不自行重试；不使用 `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` 掩盖并发/子进程回归，不伪造 replay 或反向验证结果。
- 影响：本轮三材料 `selected_round`、Summary 质量、fallback 比例、12/12事实、S5/S6、页面 hash、replay 和反向审计均未完成；正式 KB 未被写入。
- 复核证据：`src/knowledge_digest/draft.py:1037-1041` 在固定并发4下启动线程池；`src/knowledge_digest/llm.py:271-272` 每个真实请求进入 `os.fork()`；当前宿主为 Darwin ARM64，Docker daemon 不可用。

## 根因修复

- 用户随后明确授权修复根因；`llm.py` 已将请求边界改为 `multiprocessing` `spawn`，不再在线程内直接 `fork()`，父进程仍负责硬墙钟超时。
- 回归证据：修复前本地 HTTP 4并发稳定触发 `objc_initializeAfterForkError`；修复后并发4真实 transport 测试 `2 passed`（含1秒超时测试），专项 `67 passed`，全套 `176 passed`。
- 原三材料失败现场不覆盖；必须使用新的 `/tmp/kd-real-pilot-latest.*` 重新完成正式运行和 replay。

## 阻塞解除后的正式验收

- 新隔离根 `/tmp/kd-real-pilot-latest.diIrxn` 使用 `spawn` 修复后正式运行和原样 replay 均成功；旧失败现场保留，不作为成功证据。
- 正式与 replay 均为退出码0；28/28 provider batches valid、3/3 Summary validated、S5 3/3 success、S6 211；12/12预选事实和10/10固定种子摘要抽查通过。
- 正式页 hash 前后 `cmp=0`；claim/provenance/page 集合无漂移；反向审计删除首行返回1，恢复后返回0。
