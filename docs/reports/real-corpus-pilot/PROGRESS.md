# Real Corpus Pilot Progress
1. 2026-07-28 任务0完成：比较离线恒等输出与 qwen3.6 提炼输出，事实和溯源优先。
2. 顺序：基线核对 → 隔离语料与 dry-run → control → qwen → qwen 重放 → 评估。
3. 基线：LLM `42 passed in 0.11s`；全套 `147 passed in 3.87s`；wrapper help 成功。
4. 五份指定语料全部存在；开工状态保存于 `/tmp/kd-real-pilot.xMAHxZ/start-git-status.txt`。
5. 开工 sha256 共73条，保存于 `/tmp/kd-real-pilot.xMAHxZ/start-sha256.txt`。
6. 隔离根目录：`/tmp/kd-real-pilot.xMAHxZ`；禁止使用真实仓库作 kb_dir。
7. 最大风险：qwen 页面漂移、事实删减、错误 source、重复累积、provider 调用上限。
8. 上限：真实 provider ≤6次，完整运行 ≤3次，总时长 ≤60分钟。
9. 任务1完成：同源 control/qwen/new_dir 已建；dry-run 3 drafts、状态 dry_run、正式 pages 仍仅两份基线页。
10. 控制组完成：3 drafts，S5 2/2 success，S6 422条；report 为 `run-8e2cb8d076c64523909e974efea5e7d0/report.json`。
11. qwen 项停止：连续3次 provider 失败（2次 read timeout、1次 HTTP 429）；未修改配置或产物，继续控制组评估。
12. 任务3可完成部分结束：control 事实12/12、provenance抽查10/10、S4/S5/S6门禁通过；反向 cmp 为0/1。
13. 结论：不建议正式试用；qwen A/B 与重放未验证，control 存在全量跨页重复和 claim 噪音。
14. 收工边界：指定 sha、tracked diff、既有 untracked、允许范围外 status 四项开工/收工比较均为0。
15. S3 修复：新增独立 `page_match_threshold=0.15`；top-k 只保留审计候选，未达门槛不再进入 target_paths。
16. 回归：S3/配置聚焦 `7 passed`；phase0 `50 passed`；全套 `151 passed`；`git diff --check` 通过。
17. 新隔离根：`/tmp/kd-real-pilot-s3.VziVwd`；dry-run 三簇均为 new，旧页不在写入计划。
18. control：S5 3/3 success，S6 211条且无跨页重复，12/12事实保留，两份旧页 hash 不变。
19. qwen：小请求成功；三次正式运行均 read timeout，原始日志已保存；停止重试，A/B 与重放仍阻塞。
20. S4 分批完成：默认20 claims/3000 source chars；逐批门禁、整簇回退、结构行保护、原子代码组件和调用审计已实现。
21. 回归：LLM `49 passed`；全套 `158 passed`；`git diff --check` 通过。
22. 真实 qwen：结构安全冷运行一次在约7分半后单批 timeout；逐批日志重试16/16成功，S5 3/3、S6 211、事实12/12。
23. qwen 重放：16/16成功，正式页前后 sha256 完全一致；无 fallback。
24. A/B 结论：qwen 相对 control 仅多4个空行，无明显提炼收益；下一步转向“双层总结+逐字证据”契约。
25. 已完成设计准备：新增 `docs/plans/summary-evidence-output-design.md` 和10条人工样本 `SUMMARY-EVIDENCE-SAMPLES.md`；下一步才改 S4 schema/门禁。
26. Summary+Evidence 已实现：摘要默认关闭；系统确定性保留完整 Evidence，摘要支持必须引用输入 fingerprint；失败整簇保留证据并标记 rejected。
27. 回归：LLM `54 passed`；全套 `163 passed`；`git diff --check` 通过。
28. 首次真实摘要运行因 qwen 将 supports 简写为字符串而拒绝；增加只按精确 fingerprint 的安全归一化。
29. 第二次真实摘要 S4 全部 validated，但 S5 暴露模型给 claim 文本附加换行导致 provenance 未回填；改为稳定 fingerprint/来源/行号匹配并仅归一化空白。
30. 最终真实摘要运行：`run-0d9f33d032624656b407caca1d8a6bd6`，3/3 selected，S5 3/3 success，S6 211，12/12事实保留。
31. 原样重放：`run-a3554b240eac4de8a69000668ea2bf4e`，S5/S6 成功但 `draft-1.md` hash 漂移；3页中1页变化，摘要尚未达到正式启用门槛。
32. 稳定性修复：OpenAI 请求加入 `temperature=0`；摘要 prompt 强制保留数字、日期、范围、条件词、路径、命令和标识符。
33. 回归复核：LLM `54 passed`；全套 `163 passed`；`git diff --check` 通过。
34. 最终真实复测运行 `run-9df6c678308a40fd90d37f74c8a022ea` 约9分钟无响应，安全中止；`official_write=pending`，未产生新的正式页、S5/S6 或重放证据。
35. 当前结论：摘要功能安全门禁已具备，但质量/稳定性未达正式启用；`llm_summary_enabled` 保持默认 `false`。
36. 复核 provider：同一 endpoint/model 短请求 `HTTP 200 / 0.47s`；不是连接或 key 故障。
37. 真实10条 claim 摘要 smoke：`31.79s` 返回，`summary_status=validated`、1个 summary segment；证明小批量路径可用。
38. 全量批次即使 `KD_LLM_TIMEOUT_SECONDS=180` 仍无响应；问题定位为整批 prompt/JSON 输出规模，不再归因于 provider 故障。
39. 新增可配置 `KD_LLM_TIMEOUT_SECONDS`；回归：LLM `58 passed`，全套 `167 passed`，`git diff --check` 通过。
40. 下一步：用约10条 claim、较小 source 字符上限做单材料正式小样本，再做一次 replay；通过后才扩大范围。
41. 10条标注事实正式小样本：1批完成，`summary_status=validated`，S5 success，S6 `10` 条。
42. 小样本 replay：`run-0dc793c08cf344f78c16e472b364b766`，hash `cmp=0`，S5 success；小批量路径稳定。
43. 小样本摘要保留了10条事实中的数字、日期、范围、条件词、路径、命令和工具名；完整 Evidence 与 provenance 均保留。
44. 全量运行仍不扩大：20 claims/3000 chars 批次在 timeout `180s` 下仍无响应；问题边界明确为批次规模。
45. 下一步：单份完整材料使用约10 claims/1500 source chars 运行，再决定是否扩大到三份材料。
## 2026-07-28 本轮任务书执行
1. 目标：隔离副本验证 qwen3.6 小批量 Summary+Evidence；默认摘要仍关闭。
2. 顺序：基线 → 单份完整材料 → 三份完整材料 → 原样 replay → 反向验证 → 报告与回归。
3. 基线：专项 `58 passed`，全套 `167 passed`，`git diff --check` 通过。
4. 约束：仅写任务书允许路径；不改正式语料、正式 KB、依赖、锁文件、API key、S3/检索逻辑。
5. 本轮配置：`llm_summary_enabled=true`、`llm_batch_max_claims=10`、`llm_batch_max_source_chars=1500`、timeout `180s`。
6. 最大风险：长批次仍超时；其次是摘要遗漏数字/条件、provenance 错配、replay 漂移。
7. 单材料首次正式尝试：`run-e4f0bb143edd4d8eb7979dfe1c40b37c` 首批无响应约5分钟后退出130，`official_write=pending`，现场保留。
8. 短请求真实 provider 返回 `OK`；第二次单材料运行 `run-cbf94c80f99f4d738ec276934163dafe` 成功，13/13 provider calls，13/13 batch `valid`。
9. 单材料验收：coverage/retention/faithfulness=1，S5 success，S6=103，Summary/Evidence 存在，claim 内容与 locator 归一化核对通过。
10. 当前：任务1通过；任务2新隔离副本正式运行，预计28 calls；正式页 hash 需写入后立即 replay。
11. 任务2第1/2/3次均在 S3 后首个 HTTPS 响应阻塞，run 分别为 `run-a86fff63c6784964a91a86c1e46b88c4`、`run-c2751b39b6cf4aa09bbbd3fc1f8380f0`、`run-e915916459e54ee2903c6c138f63280d`。
12. 任务2三次均 `official_write=pending`、正式页0、无 S4/S5/S6/replay；按连续3次同类 provider 失败停止。
13. 未完成项：3/3 selected_round=1、12/12事实、10条摘要人工检查、三材料 replay hash；最终结论转为有条件试用。
14. 单材料 replay：正式页 hash `e8bddbf8094eace235eb10c11054420a8cffe853a112060adaa25d128c8d7058` 前后 `cmp=0`；replay run `run-9c2ebc310f654b938f3d0ea110a7bb2d` S5 success、S6=103。
15. 根因修复：Summary 模式下 oversized atomic component 改为 claim-sized provider batches；Evidence 仍由系统完整渲染。修复后真实三材料上下文诊断为 max claims=10、max source chars≤1500、oversized=0。
16. 回归：专项 `59 passed`，全套 `168 passed`，`git diff --check` 通过；新增测试覆盖 atomic Summary 拆批且 Evidence 不丢失。
17. 修复后真实 qwen smoke：prompt=9241、source=1400、claims=8，30.24s，`summary_status=validated`，returned claims=8。
18. 正式三材料重跑未执行：原任务最多3次完整运行已用完；现状仍为有条件试用，下一轮需用修复后代码重新走正式门禁。
19. 继续执行修复：为 urllib 响应读取加入硬墙钟 deadline；仅 transport failure 可显式重试，HTTP/JSON/校验失败不重试；正式默认 `KD_LLM_RETRY_ATTEMPTS=0`，防止超过调用上限。
20. 回归：专项 `61 passed`，全套 `170 passed`，`git diff --check` 通过；新增 transport-only retry 和 invalid-output no-retry 测试。
21. 当前进行：在全新 `/tmp/kd-real-pilot-final.*` 隔离副本重新做三材料正式 qwen 验收；保留 AprbY1 中止现场，不覆盖原始日志。
22. 修复后正式现场：`run-3cc98eab52ec419d8dd3aacfda44e8d8` 在 S3 后首个真实 HTTPS 读取阻塞；约3分30秒仍无响应，人工发送 `SIGALRM` 后返回 `provider request failed (deadline exceeded after 180s)`，进程退出 `1`，S4/S5/S6/正式页均未产生。
23. 现场栈确认阻塞为 Python `_ssl__SSLSocket_read -> poll`；改用 Timer 线程发送 `SIGALRM`，新增阻塞 deadline 回归测试。
24. 回归：专项 `62 passed`，全套 `171 passed`，`git diff --check` 通过；下一次真实运行仍限定全新隔离目录，调用不重试。
25. fork 修复后正式运行成功：`run-5163f070cdd747cba789e7dca7c04dae`，3 formal outputs，28/28 provider calls，3/3 selected_round=1，3/3 Summary validated，28/28 batch valid，无 fallback；S5 3/3 success，S6 211。
26. 正式页立即 hash：draft-1 `9e97ac...`、draft-2 `abba9f...`、draft-3 `a667a7...`；原样 replay `run-3a5185663a7a412290a0a1ad1415c5f7` 成功，28 calls，S5 3/3、S6 211，前后 `cmp=0`。
27. 反向验证：12/12 预选事实保留；211/211 claim 的规范化 source 内容、source URI、fragment locator、Evidence 一致；3/3 页面均有 Summary/Evidence。
28. 10条人工摘要样本：9/10 通过；G2 丢失“最多3篇”和 `select_detail_lines()`，数字/标识符保真不达标，Evidence 未丢失。
29. 最终结论：有条件试用；安全门禁和 replay 达标，但 Summary 质量未到10/10，摘要默认继续关闭。任务2正式+replay共56 calls；含此前任务2失败尝试仍未超过80 calls。
30. 最后修复：`_validate_summary` 现在确定性检查 Summary 中所有数字及关键路径/命令/函数/工具标识符；缺失即 rejected，完整 Evidence 不变。新增回归后专项 `63 passed`、全套 `172 passed`，skipped=0。
31. 由于最后修复发生在 56-call 正式运行/replay 之后，未伪称现有正式页就是新门禁产物；正式启用前仍需在调用预算内重新做全量复验。
32. 根因修复：模型把精确限制压成模糊词时，系统从受信任 source claim 自动追加“关键保真细节”段；不改 Evidence，不接受模糊替代。
33. 真实 qwen3.6 G2 定向复验成功：`selected_round=1`、Summary `validated`、`select_detail_lines()`/`12`/`3` 均保留、Evidence 存在；调用1次。
34. 回归：专项 `64 passed`，全套 `173 passed`，`git diff --check` 通过。三材料全量正式复验仍未执行，不能提前改成“建议试用”。
35. 性能根因：28 个 provider batch 原先串行执行，累计 provider 时间 `912.139s`（约15.2分钟），单批 `25.431～48.557s`；replay 还会再付一次调用时间。
36. 性能修复：新增可调 `llm_batch_concurrency`，默认 `4`；最多4个独立 batch 并发，结果按 batch_index 顺序合并，任一 batch 失败仍整份 draft fallback，Evidence/provenance 门禁不变。
37. 并发回归：专项 `65 passed`，全套 `174 passed`，skipped=0；新增“并发上限=2、实际并发、合并顺序、失败整份回退”断言。
38. 建议调整：默认并发4保守保留；provider 出现429或限流时可在隔离配置降为1/2，但不得关闭失败回退或放宽事实/provenance校验。

## 2026-07-28 最新代码全量复验
1. 目标：在全新隔离副本完成三材料 Summary+Evidence 正式运行、原样 replay、反向审计。
2. 顺序：任务0基线 → 隔离副本/dry-run → 正式运行 → hash/门禁 → replay → 反向验证 → 报告/回归。
3. 约束：只写隔离目录和三份报告文件；真实 KB、源材料、源代码、测试、依赖和锁文件只读。
4. 固定配置：Summary 开启、10 claims、1500 source chars、并发4；timeout=180s；retry=0。
5. 最大风险：provider 连续同类错误触发停止；其次是事实/provenance丢失、摘要关键细节遗漏、页面 replay 漂移。
6. 任务0：专项65 passed、全套174 passed、diff check通过；隔离根为 /tmp/kd-real-pilot-latest.UUSet0。
7. 开工 status 和五份指定文件 sha256 已保存于隔离根；预选事实12条已写入并核对。
8. 任务1完成：dry-run 退出0，3 sources、3 drafts、roots和结构字段正确；formal_kb_changes为空，正式页仍仅2份 KB 副本。
9. 任务2：正式命令退出1，run-5a6d73a4a7324138b91377bf3a1b8eda 在 S3 后因并发 worker fork 的 macOS objc_initializeAfterForkError 失败；S4/S5/S6/正式页均无产物。
10. 按连续同类 provider 错误和不自行重试硬约束停止受影响项；不执行 replay/反向审计；最终专项65、全套174、diff check均通过，报告已更新。

## 继续复核
1. 最新代码和隔离现场未改变；并发线程内 fork 的 macOS 回归可由源码路径和原始错误共同确认。
2. 未使用环境变量绕过 fork 安全检查，未改并发配置、源代码或测试；当前无合规的第二运行路径。

## 2026-07-28 根因修复后继续执行
1. 用户授权修复根因：provider transport 改为 `spawn` 子进程；并发4、180秒硬超时、retry=0和失败回退语义保持不变。
2. 先写回归测试再修复：原实现本地4并发复现 `objc_initializeAfterForkError`；修复后并发4和硬超时测试均通过。
3. 修复后回归：专项 `67 passed`，全套 `176 passed`，`git diff --check` 通过；既有工作树改动保留。
4. 下一步：全新 `/tmp/kd-real-pilot-latest.*`，重新 dry-run、三材料正式运行、页面 hash、原样 replay和反向验证。
5. 新隔离根：`/tmp/kd-real-pilot-latest.diIrxn`；开工 status、五份指定文件 sha256、12条预选事实已保存。
6. 新 dry-run：退出0，3/3来源、3/3 drafts、固定 Summary/batch 配置正确；formal_kb_changes为空，正式页仍只有2份副本。
7. 修复后正式 run `run-da97cdadc9bc43b5931e81e9148a7850`：退出0，3/3来源，28/28 batch/provider calls，全部 valid，3/3 Summary validated，无 fallback。
8. 正式门禁：coverage/retention/faithfulness=1/1/passed，unsupported=0；S5 3/3 success，S6 211条，12/12预选事实，3页均含 Summary/Evidence。
9. 正式页 hash 已保存于 `before-replay.sha256`；三页 hash：draft-1 `3731e418...`、draft-2 `300845f9...`、draft-3 `8ebb1789...`。
10. 原样 replay `run-ee0c9d2aaa864e3db17da8c507448d14` 退出0；S5/S6仍3/3、211，claim/provenance/page集合不漂移，hash `cmp=0`。
11. 反向验证：删除首行检查退出1（210/211），恢复后退出0（211）；两次输出和副本均保留。
