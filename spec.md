---
content_profile: spec-content.v3
---

<!-- ACTIVE-CONTRACT v4.7: this section is the only current contract. The
     historical material below is retained for traceability only. -->

## 当前修订 v4.7（2026-09-04）：入口、输出、基线和逐句血缘唯一解释

符号规则唯一解释：`route_name:page_identity` 与 `route_name:home_target_page_identity` 都只是记号，实际 slot bytes 始终是 `route_name`、一个 ASCII `:`、以及 `home_target_page_identity` 字段的实际值；不把字段名本身写进 slot。纯 lineage/quality 失败固定为 `not_released`/exit 1；只有 identity、authority、锁、预算或 provider-global 失败才是 `blocked`/exit 2 或 `unavailable`/exit 2。

本节是唯一生效的产品合同，不增加用户功能范围。本文其余内容全部是历史归档或背景，不授权执行；任何旧文字与本节冲突时，以本节为准。当前 LLM 唯一使用 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`；`mini_task.design`/`terminal-clean` 只作可选 DESIGN-ADVISORY 记录，不是 M401、M401-R 或 M402 的前置条件。实现审查仍是硬门，真实知识质量和五项 CompanyBrain 严格胜出门槛不变。

本次实现的正式 public machine 闭包固定为十一项：`_audit/audit-pages.json`、`source-status.json`、`companybrain-route-snapshot.json`、`semantic-compile-ledger.jsonl`、`semantic-response-ledger.jsonl`、`route-ledger.jsonl`、`raw-coordinate-map.json`、`source-not-documented-zero-match.json`、`source-not-documented-verifier.json`、`run-result.json`、`directory-manifest.json`。因此 host-only receipt 的 `public_receipt_ref` 指向 `bundle/_audit/run-result.json`；旧文中把 `run-result.receipt.json`、`quality.json`、`sources.jsonl`、`evidence.jsonl` 作为正式 public 文件的描述均不再授权执行。quality 结果只以 host-only attempt/promoted artifact 的 ref+SHA 绑定，不在 run-result 中复制整份结果。

血缘口径补充：section/answer_body 的 body 精确等于 `原始资料未明确` 且 `evidence_ids=[]` 时，是保守的缺口占位，不是事实句。由于 Reader 仍可见章节标题和占位正文，它必须保留两行 RenderLedger：一行 `Reader.section`、一行 `Reader.answer_body`；两行都不填 raw binding，只计入 `unknown_units`，不计入 `rendered_units` 或 `lineage_coverage`。所有其它事实 unit 必须达到 100% raw binding；任何其它无绑定 unit 仍失败。

### v4.4 当前纠偏：历史 V50 不阻断 raw-only 发布

`RC-USER-V50` 的缺失只证明历史结果无法回放，不证明当前 raw 结果失败，也不得成为当前 raw-only 候选、M401、M401-R 或 M402 的硬前置。`ROOT-CAUSE` 仍必须保留 provider-free 的 blocked/unavailable attempt，不能伪造、替换或 promotion；但 M401/M402 只使用当前 `/Users/Hugh/Downloads/confluence 原始数据`、当前 CompanyBrain 快照、当前实现证据和当前五项质量结果。AC-v4-13 只记录历史回放状态，不把历史 blocked 状态计入当前 release predicate。

当前 CompanyBrain 比较基线是 M402 本次对 `/Users/Hugh/Hugh/Knowledge/CompanyBrain` 生成的快照和 observation，不再要求它先通过 `RC-CURRENT-BASELINE` 的历史回放身份。四产品、89 条来源、垂直切片、Qwen/Jina 真实调用、五项逐格比较、Reader/Audit 闭包仍是当前硬门；任一未通过仍只能 `not_released`/`blocked`，不降低质量门槛。

SND 扫描采用 `SND-RULE-002`：触发词与动作词同块出现才是 `rule`；只有触发词但同块明确是描述性/否定性语境（例如“不会”“没有”“避免”“不可预知”“优点”“缺点”）时是 `no_rule`；其余触发词单独出现仍是 `ambiguous`。这只修正“错误”出现在方案优缺点描述中被误判为异常规则的问题，不允许跨来源推断异常处理。

本合同所称 `canonical UTF-8 JSON` 只有一个定义：对象 key 递归按 Unicode code-point 升序，数组保持原顺序，使用无空格、`ensure_ascii=false`、`allow_nan=false` 的 UTF-8 JSON 序列化，并在末尾追加且仅追加一个 LF；所有本合同未另行说明的 JSON hash 都使用这组字节。

页面身份也只有一个确定规则：source page 的 `page_key` 与 `page_id` 均固定为 `source:<source_id>`；answer page 的 `page_key` 与 `page_id` 均固定为完整 `answer:<question_id>:<page_type>`。因此 `page_identity` 直接等于非空 `page_id`，不再允许按缺失或输出顺序选择其它 fallback；每个 Home.route 目标都能由 `page_key/page_id` 独立重算。

M401-R 的 allowlist 以本句为唯一解释：attempt 目录的写入、before/after 快照和 inverse patch 必须同时覆盖 `review-result.json`、`M401-R-review-receipt.json`、`attempt.json`、`inverse.patch` 四项；任何后文只列三项的旧措辞均不生效。`review-result.json` 由 authenticated `mini_task.implementation` adapter 写入，source receipt 随后只原样 promotion，不重写该文件。

本合同的三个确定性补充规则：Home.route render unit 以 `(route_name, home_target_page_identity)` 为唯一键；同一 `route_name` 下重复命中同一目标必须在渲染前失败，不能生成碰撞 unit。CompanyBrain observation row 的 `status` 只能是 `present`、`absent`、`unknown`、`forbidden`：`present` 才可比较，`absent` 只能映射 `CB_MISSING`，`unknown/forbidden` 不能产生 `KD_WIN`，`N/A` 只由 C0 applicability 产生。`qwen_payload_sha256` 只有一个规则：hash 传给 `model.generate` 的最终逻辑 payload 字符串 UTF-8 bytes；compiler 不 trim、不追加换行，结构化数据必须先按 C0 canonical JSON 加末尾 LF 序列化成该字符串，再对序列化后的实际 bytes 求 hash；trace、route ledger、M401/M402 必须重算同一 bytes。

1. **唯一公开入口和结果树**：`pyproject.toml` 的 `digest` 必须指向 `knowledge_digest.simple_cli:main`，但 `simple_cli` 只能做参数解析、调用 `compiler.digest`、映射终态/退出码和打印摘要；它不得生成业务正文、标签、质量 verdict 或第二套输出树。`compiler.digest` 是唯一生产编排入口，必须调用 `providers` 和 `publisher.commit`。正式 Downloads 运行目录下只有一个公开结果 `bundle/`；读者入口为 `bundle/README.md`、`bundle/Home.md`、`bundle/products/...`、`bundle/Audit.md`。机器结果只允许使用本节开头列出的十一项固定文件。`_digest` 只能作为仓库内历史/测试资料，不能出现在正式 bundle，也不能再出现 `scripts/task5_reader_quality.py` 这类第二入口。

2. **CompanyBrain 当前绑定**：五项比较必须使用 M402 本次由 authenticated runner 传入的 `companybrain_root` 快照，不得直接消费静态 baseline prose；当前任务的 runner 参数必须绑定用户批准的 CompanyBrain 目录，并把实际 root identity 写入 host-only receipt，不能把 host path 写入 public bundle。该快照必须绑定同一 raw manifest 的 `source_manifest_sha256`、当前 `run_id`、CompanyBrain `companybrain_snapshot_id`、`companybrain_tree_sha256`、逐文件 hash/locator 和 `observation_sha256`；`bundle/_audit/companybrain-route-snapshot.json` 是脱敏 public projection，且固定写入上述字段和快照文件清单。`quality.json` 的每一条 `case × projection × dimension` 必须引用同一 `companybrain_snapshot_id/companybrain_tree_sha256/observation_sha256`。任何缺失、陈旧、hash 漂移或跨运行复用都是 `CB_MISSING/UNKNOWN`，禁止 `KD_WIN`。

3. **Reader 逐句 raw 血缘门**：发布前把 Reader 中每个可见标题、问题、业务句、轴值、页面类型值、section 和 Home route 计为一个 render unit；每个 unit 必须先在 staging candidate 的 `_audit/evidence.jsonl` 有且仅有一行，且严格满足唯一的 `knowledge-digest-render-unit.v1` 行合同：`unit_id`、`page_key`、`page_path`、`surface`（`Reader.title|Reader.question|Reader.summary|Reader.answer_body|Reader.section|Reader.axis|Reader.page_type|Home.route`）、`slot`、`text_sha256`、`raw_source_id`、`raw_hash`、`block_id`、`claim_id`、`locator`、`support_sha256`、`audit_ref`。正式 public tree 不复制这份中间 RenderLedger，而由 host-only quality result 固定绑定其 100% lineage 结果；`Audit.md` 仍是读者回查入口。`unit_id` 的输入不是可见字符串转义，而是四段 UTF-8 byte array 按顺序拼接：`page_path bytes`、单个 `0x00` byte、`page_key bytes`、单个 `0x00` byte、`surface bytes`、单个 `0x00` byte、`slot bytes`；取 SHA-256 前 24 个小写十六进制字符并加 `u-`。`slot` 对 title/question/summary/page_type 使用固定值，对 axis 使用轴名，对 section/answer_body 使用 heading，对 Home.route 使用记号 `route_name:<home_target_page_identity>` 的字节公式（字段名不进入 bytes）；`unit_id + page_path` 必须唯一。`audit_ref` 必须严格是 `Audit.md#evidence-<evidence_id>`，并指向同一 source/block/claim/hash/locator 的 Audit 锚点。Reader.summary 使用该页 summary 的首个按 `(source.relative_path,start_line,evidence_id)` 排序的 evidence binding；Reader.title、Reader.question、Reader.page_type 使用同一 summary binding；Reader.answer_body/Reader.section 使用该 section 的首个 binding；Reader.axis 使用对应轴的 binding；Home.route 使用其 route row 的首个 binding。没有 binding 的 unit 不生成 Reader，不能用页面名、文件名或模板补证据。axis、page_type、Reader.title、Reader.question 和 Home.route 不是编译器猜测：它们必须引用 route ledger 的 `evidence_bindings`，并与触发该值的 raw block/claim/locator/support hash 字节相等；Reader.summary/answer_body/section 也必须使用同一 raw binding。`README.md`、`Audit.md` 和 Home 的固定导航壳只允许由本次 machine evidence 确定性重建，不能写入动态业务句；实现若输出任何非固定模板句，必须失败，不再为壳层增加动态 surface。quality.py 必须重算并判定 `lineage_coverage = bound_units / rendered_units = 100%`，publisher 只校验 quality.py 已生成的结果和文件 bytes。任何无绑定、跨 source、错 hash、错 locator、Audit-only 证据或只引用 CompanyBrain 的 unit 都失败；失败只能 `blocked/not_released`，不得由文字模板、原文拼接或质量分补救。

4. **机器验收绑定**：M401 必须有可执行的 `ENTRY-001`（薄入口确实调用 compiler）、`OUTPUT-001`（bundle/_audit 唯一树）、`BASELINE-001`（quality 只接受当前 snapshot binding）、`LINEAGE-001`（逐 unit 100% raw binding）测试和 receipt；M401-R 必须审查同一 receipt/当前 snapshot，M402 必须重算真实 Downloads bundle。测试只证明实现行为，不能替代真实 provider、真实 raw、真实 CompanyBrain 或五项 `KD_WIN`。

M401 packet writer 使用同一个 `digest` CLI 的 `--gate M401` 证据模式，仍进入 `compiler.digest`，只写上述 attempt packet、attempt receipt、inverse.patch 和隔离 run-root；该模式不读取真实 raw/CompanyBrain、不发 provider、不写 Downloads/public bundle，也不生成第二套业务入口。`scripts/task5_reader_quality.py` 不得出现在当前任何生效命令中。

CLI 模式合同固定如下：`--gate M401` 必须同时接收 `--fixture-bundle <c3_bundle>`、`--m401-attempt <attempt_dir>`、`--m401-run-root <run_root>`；fixture 必须是通过 C3 的不可变 bundle，编译器验证其十一项 public machine 闭包、manifest/tree/material identity 后才生成 M401 attempt。`--gate M402` 是唯一真实运行模式，接收 `<raw_input> <downloads_run_root>`、`--companybrain-root <companybrain_root>`、`--config <runtime_config>`、`--provider-config <provider_config>` 及 M401/M401-R/WorkflowHub 绑定参数；`--config` 只指非秘密的 Task5 runtime 配置，`--provider-config` 只指本地凭据和 provider 配置，实际 provider-config 路径仅记录在 host-only receipt。两种 gate 都由 `simple_cli` 解析后调用 `compiler.digest`，不得另建脚本入口。

M402 还必须提供冻结的 `--quality-config`，且直接 `compiler.digest` 只能接收 `evaluation_mode=full`；缺少质量配置或直接走 slice 都是 `blocked`，不能退化为普通 `completed`。SND `semantic-zero-match-verifier` 不是可选审计：verifier 未 `passed` 时，正式 bundle 必须保持 `not_released`，即使五维比较结果暂时全部为 `KD_WIN` 也不能升级。

Provider 配置的默认位置固定为 `~/.config/knowledge-digest/config.json`（展开后为当前用户的 `.config/knowledge-digest/config.json`）；M402 可由 authenticated runner 通过 `--provider-config` 显式传入同一 schema 的本地文件，显式参数优先。文件必须同时声明 `llm` 和 `embedding`：LLM 只允许 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`，embedding 只允许 `https://llm.paxszapp.com/v1` 的 `jina-embeddings`；运行 receipt 必须记录实际配置模型。配置写成其他模型时，provider preflight 必须在首个请求前阻断，不能静默替换模型。凭据解析顺序固定为 provider section 的直接 `api_key`，其次是该 section 的 `api_key_env` 兼容回退；根级 `api_key` 只作迁移兼容的直接 key，并按同一优先级补入缺失的 provider section，绝不覆盖已有 section `api_key`。缺失/无效 key、schema、endpoint、model 或 calibration 在首个 provider request 前统一 `blocked|unavailable`、`provider_calls=0`；key 只在进程内使用，不能进入 payload、receipt、cache、bundle 或报告，实际绝对 config path 只允许出现在 host-only receipt。

`knowledge-digest-render-unit.v1` 还固定保存 `slot`；quality.py 用 `page_path/page_key/surface/slot` 重算稳定 `unit_id`，其中 Home.route 的 slot 使用记号 `route_name:<home_target_page_identity>` 的字节公式，字段名不进入 bytes，因此同一入口下的多个页面不会碰撞，审查和重复运行无需依赖输出顺序。

`RunManifest` 的唯一 schema 为 `knowledge-digest-run-manifest.v1`，顶层字段集恰好为 `schema_version`、`source_count`、`sources`、`routes`、`pages`、`tree_sha256`；它只内嵌于 `run-result.json.manifest`，运行级完整性由同一 `run-result.json` 的 `canonical_sha256` 和 `directory-manifest.json` 共同回查，不再生成独立的 public `run-result.receipt.json`。M402 真实输入时 `source_count` 必须等于 `sources` 长度且恰好为 89；C3/M401 的受控 fixture 使用其自身的 `fixture_source_count`，但仍必须满足同一 schema、行数相等和闭包校验，不能套用 89 行硬门。数组顺序固定为：`sources` 按 `source_id`、`routes` 按 `query_id`、`pages` 按 `page_id`，均按 UTF-8 bytes 升序；这与 source-manifest projection 另行规定的 `relative_path` 排序不冲突。

`knowledge-digest-page-row.v1` 是 `RunManifest.pages` 的唯一行 schema，字段集恰好为 `page_id`、`page_key`、`page_type`、`axes`、`source_ids`、`path`、`surface_sha256`；`axes` 恰好为 `product`、`module`、`object`、`scenario`、`boundary` 五个字符串，`source_ids` 非空并按 UTF-8 bytes 排序，`surface_sha256` 是该 Reader Markdown 文件完整 UTF-8 bytes 的 SHA-256。`page_type` 只允许五个英文值：`positioning`（定位）、`concept`（概念）、`operation`（操作）、`diagnosis`（诊断）、`experience`（经验）；DIM-04 的五类页面与这五个值一一对应，projection 键中的 `qr.operation`、`metric.diagnosis` 等后缀只描述投影，不产生第六种 page type。Reader path 只按 `products/<product_key>/<page_type>/<filename>.md` 生成：产品键归一化为 `emm-for-android|emm-for-ios|goinsight|merchant-system`，跨产品 selected closure 才用 `shared`；filename 对 `title` 执行 Unicode NFKC、casefold、保留字母数字/空格/`-`/`_`/`·`、`&`→`and`、斜杠→空格、连续分隔符合并、去首尾 `-`、最多 100 个 Unicode code point 的 slug 规则。同一 `(product_key,page_type,filename)` 冲突按 `(product_key,title,page_id)` UTF-8 bytes 升序，从第二项追加 `-2`、`-3`；`pages` 按 `page_id` UTF-8 bytes 排序，不能依赖输入或模型顺序。该路径公式只适用于已通过四产品映射的 published page；未知一级目录固定为 `product_key=unclassified`、`status=unsupported`、产品闭包失败且不生成 Reader/page row，不使用 `general` 兜底。`Home.md` 不属于 `pages`。

### v4.4 唯一机器合同

第 3 条中的“失败只能 `blocked/not_released`”按本节统一状态表解释：如果合同、身份、权限、预算、锁或 provider-global preflight 失败，结果为 `blocked`/`unavailable`；如果输入和合同已锁定、但 Reader/Audit/quality/lineage/比较结果未达硬门，结果为 `not_released`。两者都不代表成功。

provider 配置错误（缺失、格式不合法、endpoint/model 不在 authority allowlist、key 不可用或配置 hash 漂移）统一属于 provider-global preflight failure：必须 `blocked/unavailable`、exit 2、provider calls=0；不能按 source/projection-local failure 继续运行。

运行级状态和失败原因采用当前 `config/task5-run-result-v1.json` 的封闭合同。`publication_status` 在 staging 检查点可为 `candidate`，但最终 public bundle 只能是 `released|not_released`；`outcome` 只能是 `success|blocked|unavailable|failed|overrun|cancelled`。只读 gate 的 `status` 只能是 `pass|failed|blocked|unavailable`；可回滚 repair gate 和 M401 receipt 的 `status` 只能是 `passed|failed|blocked|unavailable`；M401-R 的 `outcome` 只能是 `available|needs_human|unavailable|partial`。`reason_code` 必须是非空稳定机器码；成功使用 `NONE`，质量或血缘未通过使用 `QUALITY_GATE_FAILED`，provider 全局不可用使用 `PROVIDER_UNAVAILABLE`，其它错误必须按当前运行阶段的合同映射。`terminal_status` 只能是 `semantic|transport|cancelled`，M401-R 通过必须为 `semantic`。
M401-R 对上述通用映射有唯一细化：`outcome=available` 必须为 `reason_code=NONE/status=passed/terminal_status=semantic`；`outcome=needs_human` 或 `partial` 必须为 `reason_code=QUALITY_GATE_FAILED/status=blocked/terminal_status=semantic`，表示结果存在但 finding 未处置或只完成部分审查，均不得进入 M402；`outcome=unavailable` 必须为 `reason_code=REVIEW_UNAVAILABLE/status=unavailable/terminal_status=transport|cancelled`，不把审查传输不可用改写成普通质量失败。除 `available` 外，M401-R 的所有 outcome 都是非通过终态。

M401-R 的唯一 receipt schema 是 `task5-m401-r-review-receipt.v1`：attempt-local source receipt 和顶层 promotion view 均固定包含 `schema_version`、`review_kind`、`m401_packet_ref`、`m401_packet_sha256`、`review_result_ref`、`review_result_sha256`、`source_receipt_ref`、`source_receipt_sha256`、`snapshot_tree`、`material_id`、`terminal_status`、`terminal_clean`、`all_findings_disposed`、`finding_dispositions`、`outcome`、`status`、`reason_code`；authenticated adapter 只原样 promotion source bytes/hash，不重算或重写内容。`status`/`reason_code` 按本节 M401-R 细化映射执行。

`review_result_ref` 必须指向 authenticated WorkflowHub `mini_task.implementation` 生成的 attempt-local canonical result artifact `quality/evidence/task5/repair-gates/attempts/<review_attempt_id>/M401-R/review-result.json`；该文件使用本节 canonical UTF-8 JSON+LF 字节规则，`review_result_sha256` 是完整文件字节的 SHA-256。source/promotion receipt 只能引用同一 ref/SHA，不能指向口头摘要或自行重写的 JSON。

M401-R receipt 内的 `source_receipt_ref/source_receipt_sha256` 有唯一含义：它们指向 M401 同一 attempt 的 `attempt-receipt.json` 完整文件字节和 SHA；M401-R 自身的 attempt-local `M401-R-review-receipt.json` 是被 promotion 的 source receipt，不把 `source_receipt_ref` 指向自身，因此没有自引用。

M401-R 的 `m401_packet_ref` 必须指向同一 M401 attempt 的 `quality/evidence/task5/repair-gates/attempts/<m401_attempt_id>/M401/M401-evidence-packet.json`，`m401_packet_sha256` 是该 packet 完整 source bytes 的 SHA-256；不得指向 promotion view、bundle 或旧 packet。M401 的 promotion view 固定为 `quality/evidence/task5/M401-evidence-packet.json`，只原样提升通过 attempt 的 packet source bytes；来源 ref/SHA 只记录在 M401 的 `attempt-receipt.json`，不附加到 packet 副本内。

M401 packet 的 promotion 也只由 authenticated adapter 执行：通过的 `quality/evidence/task5/repair-gates/attempts/<id>/M401/M401-evidence-packet.json` 单文件 source bytes 原样提升为 `quality/evidence/task5/M401-evidence-packet.json`；来源 ref/SHA 只记录在同一 attempt 的 `attempt-receipt.json`，promotion view 与 source bytes 完全一致，不写 Downloads、不生成第二份 packet 内容；spec 中“只写隔离 attempt”仅指 M401 fake/no-network 运行不写 public/Downloads bundle。
M401 receipt 的 `fixture_bundle_sha256` 唯一等于 C3 fixture `bundle/` 的 `tree_sha256`：对该 bundle 除 `_audit/run-result.json`、`_audit/run-result.receipt.json` 外全部 regular files 建立 `{relative_path,sha256}` 数组，按相对路径 UTF-8 bytes 排序，以 canonical JSON+LF 求 SHA-256。`fixture_manifest_sha256` 唯一等于同一 fixture `bundle/_audit/run-result.json` 内嵌 `manifest` 对象的 canonical JSON+LF bytes SHA-256，也必须等于 fixture `run-result.receipt.json.manifest_sha256`；两者分别绑定 bundle 文件树和 RunManifest，不得用目录路径、文件名列表或串联原文替代。

host-only `quality-result.json` 顶层固定携带 `companybrain_snapshot_id`、`companybrain_tree_sha256`、`observation_sha256`；每条 `quality_rows` 的 `observation_digests.companybrain` 必须同时属于这三个顶层身份绑定对应的本次 snapshot，不能只依赖 row 内的 `cb_observation_ref` 或外部静态 baseline。它只由 M402 evaluator 写入 attempt 和唯一 promoted artifact，public bundle 不复制整份质量结果。

`tree_sha256` 和 `companybrain_tree_sha256` 使用同一字节算法：先取各自声明文件集合中所有 regular files 的 `{relative_path, sha256}`，按 `relative_path` 的 UTF-8 bytes 升序排序；对该数组使用递归 key 排序、无空格、`ensure_ascii=false` 的 canonical UTF-8 JSON，并追加单个 LF，再求 SHA-256。正式 public bundle 的 tree 声明集合排除 `bundle/_audit/run-result.json` 和 `bundle/_audit/directory-manifest.json`；compiler 的临时 receipt/quality/evidence 文件在 formal audit 前删除，不属于 public 集合。CompanyBrain 的集合是 authenticated scanner 实际读取的 approved snapshot regular files，不含目录、软链接和生成的 KnowledgeDigest 文件。`companybrain_snapshot_id` 固定为 `cb-` 加上述 CompanyBrain canonical file-list bytes 的 SHA-256 前 24 个小写十六进制字符；它不含主机绝对路径、运行 ID 或输入顺序。

M401 attempt packet 的唯一 schema 文件是 `quality/evidence/task5/repair-gates/attempts/<id>/M401/M401-evidence-packet.json`，schema=`task5-m401-evidence-packet.v1`，其 `canonical_sha256` 计算前必须从 packet object 中移除 `canonical_sha256` 字段本身，再对剩余对象使用上述 canonical UTF-8 JSON+LF 序列化并 SHA-256；“source bytes”只指这一文件，不指整个目录。M401 attempt receipt 的唯一文件是同目录 `attempt-receipt.json`，schema=`task5-m401-attempt-receipt.v1`，固定且不得增加的字段依次为 `schema_version`、`gate`、`attempt_id`、`command`、`command_sha256`、`fixture_bundle_ref`、`fixture_bundle_sha256`、`fixture_manifest_sha256`、`run_root_ref`、`run_root_sha256`、`packet_ref`、`packet_sha256`、`snapshot_tree`、`material_id`、`exit_code`、`status`、`reason_code`；它只记录本次 M401 输入、输出和终态，不承载回滚字段。before/after/inverse 的完整回滚字段只属于同目录 `attempt.json` 的 `task5-repair-gate-attempt.v1`，两者职责不重复；M401-R 的 `source_receipt_ref/source_receipt_sha256` 必须指向同一 M401 attempt 的 `attempt-receipt.json` 完整文件。M401-R 必须读取该 packet、同目录 `attempt.json`、`attempt-receipt.json` 和 `inverse.patch`，重算 packet/receipt SHA 后才能生成 review receipt；authenticated adapter 只原样 promotion 该文件及 receipt 的 source ref/SHA。

`task5-repair-gate-attempt.v1` 的 `attempt.json` 固定且不得增加字段：`schema_version`、`gate`、`attempt_id`、`attempt_seq`、`material_id`、`command`、`command_sha256`、`before_snapshot`、`after_snapshot`、`changed_paths`、`before_sha256`、`after_sha256`、`patch_sha256`、`inverse_patch_ref`、`inverse_patch_sha256`、`inverse_base_after_snapshot`、`run_root_ref`、`exit_code`、`status`、`reason_code`。其中 `before_snapshot/after_snapshot/inverse_base_after_snapshot` 是 64 位小写 SHA-256，`changed_paths` 是按 path UTF-8 bytes 排序的 `{path,before_sha256,after_sha256}` 数组，`before_sha256/after_sha256` 是对应快照文件清单的 SHA-256，`patch_sha256` 是 `changed_paths` canonical UTF-8 JSON+LF bytes 的 SHA-256（不另设 forward.patch artifact），`inverse_patch_sha256` 是完整 `inverse.patch` bytes 的 SHA-256；C3/M401 的 `run_root_ref` 必须为隔离 run-root 相对引用，IMPLEMENT/M401-R 必须为 `null`。失败 attempt 仍必须写完整字段，不能用 `not_released` 替换 `status`。

本合同区分两类身份：WorkflowHub 产生的 `snapshot_tree` 是 authenticated Git tree OID，允许 40–64 位小写十六进制（当前本地 WorkflowHub 使用 40 位）；Task5 自己计算的 `tree_sha256`、`companybrain_tree_sha256`、`source_manifest_sha256` 和其它文件清单 hash 才固定为 64 位小写 SHA-256。`material_id` 和 `authority_manifest_sha256` 固定为 64 位小写 SHA-256。`input_snapshot` 只能是 `{snapshot_tree,material_id,source_manifest_sha256,authority_manifest_sha256}`，其中 `snapshot_tree` 使用上述 WorkflowHub identity，后三项按各自规则使用 64 位 SHA-256（尚未建立 raw manifest 的只读 gate 中 `source_manifest_sha256` 为 `null`）。同一个 `snapshot_tree` 必须在当前 WorkflowHub receipt、M401/M401-R 和 successor 中逐字一致，不能截短、补零或把文件清单 hash冒充 Git tree OID。route 的 `scores` 只能是按 source id 排序的 `{source_id: finite_number}` 对象；`embedding_receipt` 只能为 `null` 或 `{provider,model,request_identity,selected_source_ids,selected_closure_sha256,response_sha256,status}`，`status` 只能是 `passed|failed|unavailable`；`failure` 只能为 `null` 或 `{reason_code,message,source_id,projection_id,provider_calls}`，不得增加字段。`input_snapshot`、`scores`、`embedding_receipt`、`failure` 的字段全集和 null 规则由写者与 verifier 共同执行，不能靠 prose 或模型输出自由扩展。`authority_manifest_sha256` 必须逐字等于当前 22 文件 authority/evaluation 闭包计算出的 `runtime_contract_hash`，不是第三套 hash。M401-R 的 `review_result.json` 使用唯一 schema=`workflowhub-mini-task-review-result.v1`，其字段由 authenticated WorkflowHub `mini_task.implementation` result contract 固定；本 Task5 只校验该 schema、canonical bytes、review_kind=`mini_task.implementation`、review_attempt_id、review_outcome、terminal_status、terminal_clean、findings、finding_dispositions、snapshot_tree、material_id 和 contract identity，不能用 caller 自报字段替代。

WorkflowHub successor 也只有一套可计算合同：`quality/evidence/task5/workflowhub-implementation-handoff.json` 使用 `workflowhub-implementation-successor.v1`，顶层字段恰好为 `schema_version`、`handoff_kind`、`task_id`、`project_name`、`stage`、`review_kind`、`handoff_ref`、`handoff_sha256`、`parent_design_review`、`implementation_review`、`current`、`runtime_contract`、`writer_attestation`。`handoff_sha256` 的输入是删除自身字段后的整个 handoff object，按本节 canonical UTF-8 JSON+LF 求 SHA-256；文件本身也必须等于该 object 的 canonical UTF-8 JSON+LF，`handoff_ref` 必须是该 promoted 文件的受控相对引用。

其中 `parent_design_review` 可以为 `null`，表示本任务按用户决定不等待可认证的 terminal-clean `mini_task.design` 结果；也可以恰好包含 `review_kind`、`result_ref`、`result_sha256`、`attempt_ref`、`attempt_sha256`、`report_ref`、`report_sha256`、`contract_id`、`contract_hash`、`semantic_hash`、`snapshot_tree`、`material_id`、`writer_attestation` 作为可选审计记录，但该记录不再是 M401/M402 的硬前置。`implementation_review` 恰好包含 `review_kind`、`result_ref`、`result_sha256`、`attempt_ref`、`attempt_sha256`、`report_ref`、`report_sha256`、`outcome`、`terminal_status`、`terminal_clean`、`finding_dispositions_ref`、`finding_dispositions_sha256`、`all_findings_disposed`、`m401_packet_sha256`；`current` 恰好包含 `task_id`、`project_name`、`stage`、`snapshot_tree`、`material_id`、`worktree`；`runtime_contract` 恰好包含 `runtime_contract_id`、`runtime_contract_hash`、`semantic_contract_id`、`semantic_contract_hash`、`m401_packet_ref`、`m401_packet_sha256`、`m401_r_receipt_ref`、`m401_r_receipt_sha256`；`writer_attestation` 恰好包含 `writer`、`adapter`、`authenticated`、`attestation_sha256`。各 ref/hash 必须指向同一 authenticated WorkflowHub attempt 的实际 bytes；implementation 的 `terminal_status=semantic`、`terminal_clean=true`、`all_findings_disposed=true`、`authenticated=true` 仍是进入 M402 的固定值。M402 必须重算 handoff 自身 hash，并逐项核对当前 snapshot/material/worktree、implementation review、M401 packet 和 M401-R receipt 的 ref/hash；缺失、额外字段、路径越界或三方 identity 不相等都必须在读取 raw/CompanyBrain 和首个 provider request 前 `blocked/calls=0`。该 successor 由 authenticated WorkflowHub adapter 独占写入，Task5 CLI 不能自报或补写。

CompanyBrain 的 `companybrain_snapshot_id` 必须哈希与 `companybrain_tree_sha256` 完全相同的 canonical UTF-8 JSON+LF 字节对象，即按相对路径 UTF-8 bytes 排序的完整 `{relative_path, sha256}` 数组；取该完整字节 SHA-256 的前 24 个小写十六进制字符并加 `cb-` 前缀，不得哈希 `tree_sha256` 字符串、仅路径列表或主机路径。

C0/C1/C2 的只读 attempt 统一使用 `task5-readonly-gate-attempt.v1`：固定字段为 `schema_version`、`gate`、`attempt_id`、`material_id`、`input_snapshot`、`command`、`command_sha256`、`observed_files`、`output_ref`、`output_sha256`、`run_root_ref`、`exit_code`、`status`、`reason_code`；`observed_files` 是按相对路径 UTF-8 bytes 排序的 `{path,size,sha256}` 数组，`output_ref`、`output_sha256`、`run_root_ref` 必须为 null，禁止增加字段。它只记录只读核对，不等同于 C3/M401 的可回滚 repair-gate receipt。

`runtime_contract_hash` 的输入唯一为 runtime authority map、其声明的 17 个 authority 文件和 4 个评价输入，共 22 个文件；按相对路径 UTF-8 bytes 排序后，将每项的 `{relative_path,schema,actual_sha256,canonical_sha256,size}` 数组按本节 canonical UTF-8 JSON+LF 序列化并 SHA-256。`config/task5-quality-result-v3.json` 是 gate-specific schema input，不进入 `runtime_contract_hash`；`runtime_contract_id` 固定为 `rt-` 加该 hash 前 24 个小写十六进制字符。

C0 的旧 slice 常量反例只指旧口径的 `14 case/12 path`；当前从 `config/task5-slice-cases-v1.json` 派生的 `11 case/27 unique path` 和质量 `P=12` 都是合法当前值，不触发旧常量阻断。

为消除执行歧义，正式 `bundle/_audit` 机器闭包只能精确包含本节开头列出的十一项文件；compiler 临时生成的 `run-result.receipt.json`、`evidence.jsonl`、`sources.jsonl`、`quality.json` 只用于 formal audit 输入，审计收口前删除，不属于 public bundle。M402 的通过条件必须按 released 谓词逐行满足：所有 `applicable=true` 的 projection×dimension row 为 `KD_WIN`，所有 `applicable=false` 的 row 恰为 `N/A`，且无缺行、重复行、额外行或其它 verdict。

host-only `quality-result.json` 的每条 `quality_rows` 固定为 `projection_key`、`dimension_id`、`verdict`、`kd_observation_ref`、`cb_observation_ref`、`observation_digests`、`advantage_basis`；`kd_observation_ref` 必须等于同一 `case × projection × dimension` observation row 的 `kd_ref`，并且只能解析到本次 KnowledgeDigest Reader 的 `page_path#unit_id`。`audit_ref`、`gap_ref` 等补充定位字段只允许放在 `advantage_basis`/observation row 的固定结构中，不能用 Audit-only 引用代替 Reader 侧引用。

`quality_rows` 的粒度是 `projection_key × dimension_id`，不是 case 汇总行；`case_id` 由该 `projection_key` 在冻结 quality-cases 配置中的唯一归属派生，并只在顶层 comparison result 的 `case_id`/`projection_key` 绑定中出现，不向 row 再复制第二个可漂移的 case 字段。quality result 的顶层 `case_id`、`projection_key`、`dimension_results` 与 `quality_rows` 必须由同一 projection 配置映射重算；任何 projection 无法唯一映射 case、顶层绑定与 row 不一致，均为 `INVALID/UNKNOWN`，不得由标签、总分或模型字段补齐。每条 row 的 `kd_observation_ref`、`cb_observation_ref`、`observation_digests` 和 `advantage_basis` 都必须属于该 projection/dimension，不能跨 case、跨 projection 或跨维度复用。

答案页的 `page_id` 固定等于其完整 `page_key`，因此 `answer:<question_id>:<page_type>` 的 `page_identity` 可独立重算；source page 的 `page_id` 固定等于 `source:<source_id>`，source page 的 `page_identity` 也固定等于该值，不允许缺失或 fallback 到裸 `source_id`。同一页面的五个轴名必须唯一且非空；重复或空轴名是确定性 render contract failure。`manifest_sha256` 固定为内嵌 `manifest` 的 canonical UTF-8 JSON（递归 key 排序、无空格、末尾 LF）的 SHA-256，receipt 校验必须按该字节规则重算，且 manifest 包含其 `routes`。

- `bundle/_audit/run-result.json` 的 schema 是当前 machine-evidence authority 固定的 `task5-run-result.v1`；它内嵌唯一 `RunManifest`，compiler 内部的 `knowledge-digest-run.v1` 仅是 formal audit 前的中间 run view，不是第二个 public 文件。正式 public tree 的 `tree_sha256` 按已发布文件的相对路径和文件 hash 计算，只排除 `run-result.json` 与 `directory-manifest.json`；临时 `run-result.receipt.json`、`quality.json`、`sources.jsonl`、`evidence.jsonl` 在 formal audit 前删除，quality 只以 host-only artifact ref+SHA 绑定。
- `bundle/_audit/run-result.receipt.json`、`evidence.jsonl`、`sources.jsonl` 和 `quality.json` 不是正式 public 文件；它们只在 formal audit 前作为不可变中间输入。正式 Reader/Audit machine 闭包由十一项固定文件组成，`run-result.json` 是唯一 public 运行结果入口，host-only `quality-result` 由 ref+SHA 绑定。`bundle/_audit/companybrain-route-snapshot.json` 是十一项中的一项，schema 为 `companybrain-route-snapshot-public.v1`，必须包含本次运行的快照身份、tree、observation 和脱敏文件清单；质量结果只引用它，不直接引用静态 baseline。
- compiler 的 `evidence.jsonl` 和 `sources.jsonl` 仍必须在 formal audit 前提供完整 Reader/Audit 血缘输入；它们不进入最终 public machine 闭包。RunManifest `sources` 和十一项 public audit 文件仍按各自严格字段合同校验。
- host-only `quality-result.json` 的 schema 为 `knowledge-digest-quality-result.v3`，五个维度只能使用 `DIM-01.route`、`DIM-02.taxonomy`、`DIM-03.business-answer`、`DIM-04.page-type`、`DIM-05.reader-audit`；当前质量 projection 恰好为 12 个。`bundle/_audit/companybrain-route-snapshot.json` 是固定 machine tree 十一项中的一项，schema 为 `companybrain-route-snapshot-public.v1`，必须包含本次运行的快照身份、tree、observation 和脱敏文件清单；其中 `relative_path` 和 `locator` 都必须限定在 CompanyBrain 根内的相对位置，不能写绝对宿主路径。质量结果只引用它，不直接引用静态 baseline；旧的通用快照字段名不得再写入 public 或 quality 合同。
- CompanyBrain 内容或绑定不全时统一记为 `CB_MISSING` 或 `UNKNOWN`；“gap”只能在两侧均有同一次可比较 observation 时使用，不能把缺失 CompanyBrain 当作 KnowledgeDigest 的胜出。
- C0 清单的构成为 1 个且只有 1 个 runtime authority map（`config/task5-runtime-authority-map-v1.json`，schema=`task5-runtime-authority-map.v1`）+ 该 map 指向的 17 个 authority 文件  + 4 个评价输入 + 1 个 gate-specific schema input，共 23 个文件；17 个 authority 的逻辑清单固定为：`external_processing_policy`、`provider_handshake`、`provider_prompt`、`provider_semantic`、`publication_layout`、`reader_quality_provider`、`replay_store`、`semantic_frame`、`semantic_frame_field_closure`、`source_block_claim`、`reader_path_relation`、`source_digest`、`source_not_documented`、`source_sensitive_content_scan`、`root_cause_evidence`、`root_cause_inputs`、`machine_evidence`；四个评价输入固定为 `config/task5-quality-cases-v2.json`、`config/task5-companybrain-baseline-v2.json`、`config/task5-source-page-manifest-v2.json`、`config/task5-slice-cases-v1.json`；gate-specific schema input 是 `config/task5-quality-result-v3.json`，不计入 runtime_contract_hash。其中 `config/task5-reader-quality-provider-v2.json` 是 17 项中的 `reader_quality_provider`，唯一 schema=`task5-runtime-config.v2`，不是第二个 map。所有 authority 的 actual/canonical hash 由 C0 从真实字节重算，文档中的 hash 只作索引。
- 公共产物 schema 统一使用 `knowledge-digest-*`；`task5-*` 可用于 C0 authority/config/provider 输入，以及 WorkflowHub、repair-gate、failure、host-only evidence schema 的身份，但不是 public bundle schema。`task5-semantic-output.v2` 是 provider 输入/输出 authority，写入 Reader 前必须被转换为当前 public `knowledge-digest-*` 机器合同。
- 五个比较维度使用唯一枚举：`DIM-01.route`（问题/场景路由）、`DIM-02.taxonomy`（产品/模块/对象/场景/边界）、`DIM-03.business-answer`（业务化答案正文）、`DIM-04.page-type`（定位/概念/操作/诊断/经验）、`DIM-05.reader-audit`（Reader 可见与 Audit 可回查）。`quality.json` 与 CompanyBrain observation 必须逐行使用这五个 `dimension_id`，禁止使用自由文本别名。
- 当前质量 projection 固定为 12 个：`Q-POS-01.positioning`、`Q-CON-01.concept`、`Q-OPR-01.qr.operation`、`Q-OPR-01.zero-touch.operation`、`Q-DIA-01.diagnosis.metric`、`Q-DIA-01.diagnosis.migration`、`Q-DIA-01.diagnosis.query`、`Q-DIA-01.diagnosis.delete`、`Q-DIA-01.diagnosis.doc`、`Q-EXP-01.experience`、`Q-BND-01.operation`、`Q-BND-01.diagnosis`；任何其它数量都不是当前运行事实。
- `task5-run-result.v1` 是 machine-evidence authority 对正式 `bundle/_audit/run-result.json` 的唯一运行级 schema；compiler 内部的 `knowledge-digest-run.v1` 只作为 formal audit 前的中间 run view，不是第二个 public 文件。正式 public tree 不产生 `run-result.receipt.json` 或其它同义运行结果文件。
- 退出码只有进程级可重试分类：`released=0`、`not_released=1`、`blocked=2`、`unavailable=2`、`failed=3`、`cancelled=4`；`blocked` 与 `unavailable` 故意共用 2，调用方必须读取同一 `run-result.json.reason_code` 区分策略/身份阻断与 provider 全局不可用，不能只看 exit code。
- C3/M401 的 fake/no-network 运行只写隔离的仓库 evidence attempt 目录；它不写 Downloads、不读取 raw/CompanyBrain，也不冒充 M402。只有 M402 才在新 Downloads run root 生成真实 bundle。

`knowledge-digest-render-unit.v1` 的四个“surface 名即 slot”固定字面量是 `title`、`question`、`summary`、`page_type`；`axis` 使用轴名、`section`/`answer_body` 使用 heading、`Home.route` 使用记号 `route_name:<home_target_page_identity>` 的字节公式，字段名不进入 bytes。quality.py 按 surface 独立推导同样的字面量后重算 `unit_id`，不能照抄待验证行中的 slot。`page_key`、`route_name` 和实际 U+0000 分隔字节的定义见 route ledger 段，所有写者和验证者必须使用同一规则。
`surface` 字段的实际存储值始终包含前缀（例如 `Reader.title`、`Home.route`）；只有 `slot` 对四个基础 Reader surface 使用不带前缀的 `title`、`question`、`summary`、`page_type`。`surface` 与 `slot` 不得互相省略或改写，quality.py、compiler、M401/M402 按这两个不同字段重算同一 `unit_id`。

同一 page 内 `section`/`answer_body` heading 必须唯一且非空；重复 heading 是 render contract failure，不能用输入顺序、ordinal 或隐含编号消歧。这样 `slot=heading` 的稳定性由合同保证，quality.py 可独立重算而不依赖页面渲染顺序。失败运行不生成第二套 public machine tree；唯一失败索引是 `<downloads_root>/<output_basename>.failure.<run_id>.<owner_nonce>/failure.json`，使用 `task5-failure-evidence.v1` 并由 run-result 的 `reason_code`/ref 指向它。

### v4.3 当前 AC、产品、路由和快照机器定义

Route identity 规则与 route ledger 同属当前合同。`ROUTE_QUERIES` 只有以下五个完整 `route_name`，不得由模型改写：`我想了解一个产品是什么、服务谁、怎么选以及边界`、`我想理解一个模块、对象或配置项`、`我想按步骤完成一项操作`、`我遇到了问题，需要定位原因`、`我想了解历史经验、版本和踩坑`。每个 route ledger row 的 `query_id` 先把 `question`、`scene`、`product_key`、`projection_id` 各自做 NFKC，再按 UTF-8 bytes 拼接：`question bytes`、LF byte、`scene bytes`、LF byte、`product_key bytes`、单个实际 `0x00` byte、`projection_id bytes`；取 SHA-256 前 20 个小写十六进制字符。`question_id` 明确定义为该主 route row 的 `query_id`，不是 Reader 可见文本的另一个 hash；`page_key` 是 ReaderPage 的稳定键，source page 固定为 `source:<source_id>`，quality answer page 固定为 `answer:<question_id>:<page_type>`。`page_identity` 等于 page 的 `page_id`，且当前 page contract 保证 source page 的 `page_id=source:<source_id>`、answer page 的 `page_id=answer:<question_id>:<page_type>`，缺失 page_id 是确定性 render contract failure，不得 fallback 到 `source_id`；它不取路径、标题、文件顺序或随机值。Home.route 的 page key 是 `route:<sha256(NFKC(route_name))[:20]>`，但其 `page_path` 固定为 `bundle/Home.md`，这里的 `page_identity` 只表示该 route row 唯一命中的主目标 ReaderPage，不表示 Home 自身。零个或多个匹配目标都失败；只能有一个主目标，并将 `home_target_page_identity` 写入 route ledger/evidence；Home.route 的 `slot` 只按 `route_name`、ASCII `:` 和该字段的实际值拼接，文档记号为 `route_name:<home_target_page_identity>`，不把字段名写入 slot。`unit_id` 的输入不是可见字符串转义，而是四段 UTF-8 byte array 按顺序拼接：`page_path bytes`、单个 `0x00` byte、`page_key bytes`、单个 `0x00` byte、`surface bytes`、单个 `0x00` byte、`slot bytes`；再取 SHA-256 前 24 个小写十六进制字符并加 `u-`。写者、quality.py 和 M401/M402 verifier 必须调用同一规则。

M401 的 AC trace 逐条绑定下列 13 项；每项必须有当前命令、输入 snapshot/material、输出 ref+SHA、实际结果和失败反例。`M401-evidence-packet.json.ac_trace` 必须恰好包含 `AC-v4-01` 至 `AC-v4-13` 各一行；每行 `evidence` 固定按 `command`、`input_snapshot`、`input_material`、`output_ref`、`output_sha256`、`actual_result`、`failure_counterexample` 七个子字段保存，七个字段都必须是当前 attempt 的可回查值。AC 表的第三列只是这些子字段的归属索引，不是删减字段：

| AC | 检查范围 | 必做动作 | 证据归属 |
| --- | --- | --- | --- |
| AC-v4-01 | raw 89 条 | 重算 manifest、hash、line/byte locator | C1/M402 source receipt |
| AC-v4-02 | slice→full | 从 slice JSON 派生并续跑全量 | C0/M402 run context |
| AC-v4-03 | source-digest | ready source 恰好一次 Qwen | C2 provider ledger |
| AC-v4-04 | typed semantic | 校验 schema、Claim、projection | C2/M401 test receipt |
| AC-v4-05 | Reader 血缘 | 重算 raw→Claim→Audit | LINEAGE-001 |
| AC-v4-06 | 问题/场景入口 | 回放 Home 全部 route | OUTPUT-001/M402 |
| AC-v4-07 | 产品与输出树 | 校验四产品、禁路径、唯一 bundle | OUTPUT-001 |
| AC-v4-08 | 89 条 Audit | 对账 empty、alias、failure、Reader | C1/C3/M402 |
| AC-v4-09 | Jina→Qwen | 比较 closure、payload、route ledger | C2 provider ledger |
| AC-v4-10 | 五维对照 | 按 DIM-01…05 逐 case/projection | M402 quality result |
| AC-v4-11 | 发布与秘密 | 扫描 calls、hash、key、原子写入 | C3/M402 receipt |
| AC-v4-12 | WorkflowHub | 校验 task/worktree/snapshot 链 | M401/M401-R |
| AC-v4-13 | 旧结果根因 | 回放精确 V50；缺失只记录历史 blocked，不阻断当前 raw-only | ROOT-CAUSE receipt |

raw 相对路径的第一级目录先做 Unicode NFKC、去首尾空格、casefold，再按下表得到唯一 `product_key/product_label`；两者必须进入 sources、RunManifest、ReaderPage 和 Home route。未知一级目录进入 `unclassified` 并令产品闭包失败，不能静默并入已有产品。

| 归一化比较键 | product_key | product_label | 原始目录例 |
| --- | --- | --- |
| `goinsight` | `goinsight` | `GoInsight` | `GoInsight` |
| `emm for android` | `emm-for-android` | `EMM for Android` | `emm for android` |
| `emm for ios` | `emm-for-ios` | `EMM for iOS` | `emm for ios` |
| `merchant system` | `merchant-system` | `Merchant System` | `merchant system` |

除跨产品答案的 `shared` 外，Reader 不得跨产品落点。`shared` 只在同一答案页的 selected closure 含两个及以上不同 `product_key` 时使用；此时页面目录为 `products/shared/`、`product_key=shared`、`product_label=跨产品答案`，但每条 source/RunManifest source row 仍保留自己的四产品归属，不能把来源改写成 shared。单一产品答案绝不能进入 shared；Home route、ReaderPage、route ledger 必须同时保留跨产品 selected source ids 和各自的 product 字段。产品映射只证明归属，不替代 Qwen 对 module/object/scene/boundary 的证据判断。

`run-result.json` 内嵌的 `manifest.routes` 是唯一 route ledger，schema=`knowledge-digest-route-ledger.v1`，由 `compiler.digest` 生成，Reader/Home 和 `quality.py` 消费。每行固定含 `query_id`、`question`、`scene`、`route_name`、`product_key`、`projection_id`、`candidate_source_ids`、`selected_source_ids`、`selected_page_ids`、`scores`、`embedding_receipt`、`qwen_payload_sha256`、`evidence_bindings`、`home_target_page_identity`、`status`、`failure`；`route_name` 必须是五个冻结 `ROUTE_QUERIES` 之一，`product_key` 是该 row 主页面的稳定产品键（跨产品为 `shared`），`projection_id` 是 C0 当前 projection 的稳定键，`query_id` 与该 row 的 `question_id` 是同一值，均按 route identity 段公式生成；`page_key` 和 `page_identity` 属于 `selected_page_ids` 指向的 ReaderPage，必须按同一段公式重算，不允许用“按 route ledger 推导”替代公式。对 Home.route 而言，`selected_page_ids` 必须恰好一项，且 `home_target_page_identity` 必须等于该页的 `page_identity`；匹配为零项或多项均为确定性 route contract failure。`evidence_bindings` 逐项含 raw source/block/claim/hash/locator/support hash，且必须覆盖 selected closure。Reader 的 title/question/axis/page_type/Home.route 只能引用这组 binding，不能由文件名或模板另猜。页面级 binding 选择规则是：先锁定该 page 的主 route row（source page 用其唯一 source route，answer page 用 `selected_page_ids` 精确命中的 row），再按 `(source.relative_path,start_line,evidence_id)` 取首个 binding；若 page 由多个 route row 命中，使用 `question` 与 page.question 的 Unicode 文本逐字相等者；没有或多于一个相等 row 都失败，并同时重算其 `query_id` 相等。每个非空 answer section body 还生成 `Reader.answer_body` unit，复用该 section 首个 binding，作为业务答案正文的独立血缘面。

公开 `_audit/route-ledger.jsonl` 不是第二个 route schema，而是 `run-result.json.manifest.routes` 的 canonical projection：按 `manifest.routes` 的原有顺序逐行写出每个完整 route row，行内容使用本合同定义的 canonical UTF-8 JSON，且每行末尾恰有一个 LF。`manifest.routes` 与 JSONL 的行数、顺序、对象字段和值必须完全相同；不得删字段、增加字段、重排行或从另一份 route summary 重建。写入和 verifier 都必须计算该 projection 的完整 UTF-8 文件 SHA-256，并要求实际 `_audit/route-ledger.jsonl` 与预期字节及 SHA 同时相等；不相等即 `blocked/not_released`。因此 `manifest.routes` 是唯一事实来源，JSONL 只是公开回查投影，不得被 `Reader`、`Home` 或 `quality.py` 当作独立事实来源。

route row 的 `status` 封闭为 `ready|failed|blocked|unavailable`：`ready` 表示 selected closure、Qwen typed output 和 route bindings 均通过；`failed` 只表示该 source/projection 的局部语义或证据失败；`blocked` 表示输入、合同、身份、预算或锁等全局阻断；`unavailable` 只表示 provider/依赖不可用。`status` 与 `reason_code/failure` 必须按同一映射落盘，不能使用 `picked`、`selected`、`candidate` 等未声明值。

`run-result.json.manifest.sources` 的唯一 source row schema 是 `knowledge-digest-source-row.v1`，固定字段为 `source_id`、`relative_path`、`product_key`、`product_label`、`raw_hash`、`status`、`source_digest_eligible`、`duplicate_of`、`evidence_ids`、`reader_page_ids`、`failure`；M402 真实输入时恰好 89 行，`source_id` 和 `relative_path` 都唯一，product 字段必须符合上表。C3/M401 fixture 不套用 89 行硬门，`source_count` 只需等于该 fixture 的实际 source rows，且同样唯一、闭合、可重算。`bundle/_audit/sources.jsonl` 是同一来源的审计投影，固定 11 个字段为 `source_id`、`relative_path`、`product_key`、`product_label`、`raw_hash`、`status`、`duplicate_of`、`line_count`、`evidence`、`evidence_ids`、`failure`；其中 `evidence` 只含 `evidence_id/start_line/end_line/block_content_sha256`，不复制 raw 正文，且不能改变归属或状态。用于 hash 的 source-manifest projection 只取 `source_id`、`relative_path`、`product_key`、`product_label`、`raw_hash`、`status`、`duplicate_of`、`evidence_ids` 八个字段；M402 的 `source_manifest_sha256` 是这 89 行 projection 按 `relative_path` 排序后，使用 canonical UTF-8 JSON（递归 key 排序、无空格、末尾 LF）计算的 SHA-256；C3/M401 按同一算法对 fixture 行数计算。C1/`compiler.digest` 是唯一生成者；M402 从 RunManifest 和 `_audit/sources.jsonl` 各提取同一八字段 projection，必须重算相等。

`sources.jsonl` 到 RunManifest source row 的映射是固定的：`source_id`、`relative_path`、`product_key`、`product_label`、`raw_hash`、`status`、`duplicate_of`、`evidence_ids` 直接复制；`line_count` 由同一 raw snapshot 字节计算；`evidence` 由这些 `evidence_ids` 对应的 `start_line/end_line/block_content_sha256` 生成；`failure` 直接复制。`source_digest_eligible` 与 `reader_page_ids` 不进入 sources.jsonl，是有意省略的派生/读者字段；sources.jsonl 的八字段 hash projection 必须与 RunManifest 的八字段 projection 逐项相等，不能从另一份清单重建。

`observation_sha256` 由 M402 的 CompanyBrain snapshot scanner 生成：compiler 必须先完成本次 Reader 页面、Home、Audit 和 `_audit/evidence.jsonl`，再由 scanner 读取这些不可变输出和 CompanyBrain 根，生成 observation rows、`kd_ref` 和自身 hash，最后 compiler 才能序列化 public snapshot；不得先生成观察再补 Reader。输入为 canonical UTF-8 JSON（递归 key 排序、无空格、末尾 LF）中的 `run_id`、`source_manifest_sha256`、`companybrain_snapshot_id`、`companybrain_tree_sha256`、按 `case × projection × DIM-01…DIM-05` 排序的 observation rows。每个 observation row 的 schema 固定为 `case_id`、`projection_id`、`dimension_id`、`status`、`score`、`source_refs`、`visible_ref`、`audit_ref`、`gap_ref`、`kd_ref`，缺失项使用 `UNKNOWN`/`null`，不得删除字段。`case_id` 和 `projection_id` 来自 C0 评价输入，`dimension_id` 只允许五个 DIM 枚举，`source_refs/visible_ref/audit_ref` 必须指向同一 CompanyBrain 文件或观察记录，`kd_ref` 必须指向同一 comparison projection 的 KnowledgeDigest Reader `page_path#unit_id`，不能只指向 Audit；scanner 是唯一生成者，`companybrain-route-snapshot.json` 和每条 quality row 原样引用该 hash。
M402 的 scanner 先生成 host snapshot、CompanyBrain observation rows 和其 `observation_sha256`，再生成脱敏 public snapshot object；compiler 是 public snapshot 文件 `bundle/_audit/companybrain-route-snapshot.json` 的唯一序列化者，只按固定字段和 canonical bytes 写入，不重新计算或改写 observation；publisher 只提交并校验这份既有 bytes。public snapshot、quality rows 和 run-result 必须引用同一 `observation_sha256`，且该文件纳入 `tree_sha256`（通过 run-result/receipt 的既有排除规则除外）。

`publisher.commit` 接收显式 `run_root`：C3 只传仓库 `quality/evidence/task5/repair-gates/attempts/<id>/C3/run-root`，M401 只传 `quality/evidence/task5/repair-gates/attempts/<id>/M401/run-root`；两者各自产生对应 run root 下唯一的 `bundle/`。M401-R 只审查 packet，不产生 bundle，也不携带 `run_root`。M402 才传新的 Downloads run root；每次都只提交 `<run_root>/bundle`，所以“唯一 bundle”指每次运行的 run root，而不是把 fake 测试误写入 Downloads。M401 的真实 attempt 位于 `repair-gates/attempts/<id>/M401/`，包含 `attempt.json`、`inverse.patch`，且 `attempt.json` 内必须有 `run_root_ref` 字段指向隔离 run root；不存在名为 `attempt.json.run_root` 的第三个文件。M401-R 的 attempt 位于 `repair-gates/attempts/<id>/M401-R/`；这句话描述其自身 attempt 的写入 allowlist：只写 `review-result.json`、source receipt、`attempt.json` 和 `inverse.patch`。M401-R 的读取 allowlist 仍固定为该 attempt 对应的 M401 packet、同目录 `attempt.json`、`attempt-receipt.json` 和 `inverse.patch`，并按前述规则生成 `review-result.json`；不能把写入 allowlist 当成读取边界。`ROOT-CAUSE` 不属于 repair gate，不使用 inverse patch，单独写 `quality/evidence/task5/root-cause/attempts/<id>/root-cause-evidence.json`，schema=`task5-root-cause-evidence.v2`。

唯一执行顺序固定为：Reader/Home/Audit/`_audit/evidence.jsonl` → CompanyBrain scanner 生成 host snapshot、observation rows 和 `observation_sha256` → `quality.py` 读取这些不可变 bytes 并生成唯一 QualityResult → compiler 按固定字段序列化 public CompanyBrain snapshot → `publisher.commit` 校验并提交。任何实现若在 scanner 前运行 quality.py，或在 quality.py 前序列化 public snapshot，都属于顺序合同失败。

`observation_sha256` 输入数组的行序也固定：先按 `case_id` UTF-8 bytes 升序，再按 `projection_id` UTF-8 bytes 升序，最后按 `dimension_id` UTF-8 bytes 升序；不使用配置数组位置、输入顺序或模型输出顺序。每行的 `source_refs` 仍按 UTF-8 bytes 升序，数组之外的字段按 canonical JSON 定义序列化。

M402 的 host-only receipt 固定写入 `quality/evidence/task5/actual-run/attempts/<id>/host-run-receipt.json`，schema=`task5-host-run-receipt.v1`，由 authenticated M402 runner 唯一写入；字段固定为 `run_id`、`raw_root_identity`、`companybrain_root_identity`、`downloads_run_root`、`provider_config_ref`、`source_manifest_sha256`、`public_receipt_ref`、`public_receipt_sha256`、`terminal_status`。`provider_config_ref` 只记录配置文件的受控路径/身份和 hash，不记录 key、prompt 或 response。它只保存实际绝对路径和绑定，不进入 public bundle；`public_receipt_ref` 必须指向 M402 bundle 的 `_audit/run-result.json`，从而把 host 事实和公开结果闭合。scanner 在调用 quality.py 之前先生成 CompanyBrain snapshot 与 observation，compiler 只把已生成的 observation 作为只读输入；quality.py 是 `lineage_coverage` 的唯一计算和判定者，compiler 只在其结果未达 100% 时拒绝调用 publisher，publisher 不重复生成或改写该判定。

CompanyBrain scanner 的完整 observation rows 固定托管在 `quality/evidence/task5/actual-run/attempts/<id>/companybrain-observation.json`，该文件为 host-only、不可变，不进入 public bundle，schema=`task5-companybrain-observation.v1`。它固定且不得增加字段：`run_id`、`source_manifest_sha256`、`companybrain_snapshot_id`、`companybrain_tree_sha256`、`rows`、`observation_sha256`；`rows` 是按 `case_id`、`projection_id`、`dimension_id` UTF-8 bytes 排序的 `case_id/projection_id/dimension_id/status/score/source_refs/visible_ref/audit_ref/gap_ref/kd_ref` 对象数组。`observation_sha256` 必须对该对象去掉自身 hash 后按前述 canonical JSON+LF 求 SHA-256；`bundle/_audit/companybrain-route-snapshot.json` 只作脱敏 projection，但其 hash、row refs 和 host observation 文件必须指向同一份 rows，不能让实现自选路径或只留摘要。

M401-R 的“审查”只读消费该 M401 attempt 的 `M401-evidence-packet.json`、`attempt.json`、`attempt-receipt.json` 和 `inverse.patch`；authenticated `mini_task.implementation` adapter 在自己的 `repair-gates/attempts/<review_attempt_id>/M401-R/` 中按统一四项 allowlist 写入 `review-result.json`、attempt-local `M401-R-review-receipt.json`、`attempt.json` 和 `inverse.patch`。四项都进入 before/after 快照、路径 hash 和 inverse 校验；之后 adapter 只原样 promotion attempt-local source receipt 到 `quality/evidence/task5/M401-R-review-receipt.json`，并保存 source ref/SHA，promotion view 不重新生成内容。它不读取或生成 bundle/run-root，也不修改 M401 packet。

M401 的三个命令中，`task5-m401-attempt-receipt.v1` 和 `task5-repair-gate-attempt.v1` 的 `command`/`command_sha256` 只记录唯一的 `--gate M401` packet-writer 调用（同时带 `--fixture-bundle`、`--m401-attempt` 和 `--m401-run-root` 的完整 argv 字节）；focused/full pytest 的命令、退出码和输出 hash 只进入 AC trace/test receipt，不写入这两个 receipt 的单值 command 字段。这样 M401-R 可以对单一 command 字节重算，不把三个命令压进一个字段。

Provider adapter 的单次逻辑 HTTP request 固定 `retry=0`：同一 `(provider, request_identity)` 最多一次 HTTP attempt，adapter 不自动重试。编译器允许一个有界的恢复池，但它不是隐藏重试：source compile 最多增加 12 次全局 recovery call，单个 source 最多追加 3 次；quality projection 的结构/证据校验失败最多重新生成 1 次完整 Qwen 页面。质量事实校验按一页一请求执行，避免多页响应的 page identity/结果数漂移。每次 recovery 都必须使用新的 request identity、保留失败原因和 prompt/response hash，并计入 call plan；预算不足或达到上限就保留 Audit-only/not_released，不能循环或拼接正文。Qwen 的 timeout、HTTP/JSON/schema/Claim/reference/copy 失败以及 Jina 的 timeout、HTTP/JSON 失败是 source/projection-local failure，写入 ledger/Audit、继续允许的独立 projection，但最终只能 `not_released`；DNS、TLS、connect、认证、contract hash、重复 request identity、返回数量不一致、partial embedding、selected closure 无法判断和预算超限是 global failure，立即 `blocked/unavailable`、calls 停止。调用方必须读取 `reason_code` 区分两类，不能只看共用的 exit code 2。

`quality.py` 返回不可变 `QualityResult` 对象；compiler 只把它序列化为 host-only 的 `quality-result.json`，并在公开 `bundle/_audit/run-result.json` 中保存该文件的受控 ref 和 SHA-256，不把质量明细写进 public bundle；`publisher.commit` 只校验并提交公开 bytes。这是质量结果唯一写入责任链。旧的 `bundle/_audit/quality.json` 只允许作为中间编译输入，正式发布前必须移出公开树。

为避免字段名和边界再次漂移，当前唯一合同再明确四点：`projection_key` 与 `projection_id` 是同一个 C0 projection 字符串，前者只用于 quality/result，后者只用于 route/observation，二者逐字相等，不能靠标题、case_id 或数组位置映射。`verdict` 封闭枚举为 `KD_WIN`、`CB_WIN`、`TIE`、`UNKNOWN`、`INVALID`、`N/A`、`CB_MISSING`，平局不通过；released 必须要求所有适用 `projection_key × DIM-01…DIM-05` row 都为 `KD_WIN`，一个 case 有多个 projection 时全部通过，不能用平均分或其他 projection 抵消。`observation_digests` 固定为 `{"reader":"<64位小写 sha256>","companybrain":"<64位小写 sha256>"}`，其中 reader 等于同一 basis 的 `kd_completion_digest`、companybrain 等于同一 observation row digest，不允许额外键，并按 canonical JSON 规则校验。

`knowledge-digest-source-row.v1` 的 `status` 封闭枚举为 `ready`、`known_empty`、`duplicate_alias`、`provider_failed`、`unsupported`，并新增布尔派生字段 `source_digest_eligible`；只有 `status=ready` 时它为 true，其他状态必须为 false。R_full/R_slice 只统计 `status=ready AND source_digest_eligible=true`；当前 R_full=87，另外 2 条是非 ready，但全部 89 行仍必须保留在 RunManifest/Audit。任何未知 status、缺字段或不一致都 blocked。source-manifest 八字段 hash 投影继续排除该派生字段、reader_page_ids 和 failure，因此不改变既有 source_manifest_sha256 算法。

所有隔离 gate 的 run-root 目录名必须使用大写卡片名：`quality/evidence/task5/repair-gates/attempts/<attempt_id>/C3/run-root/` 或 `.../M401/run-root/`；M401-R 和 C0–C2 不生成 run-root，M402 只写新的 Downloads run-root。`<card>` 不再是可自由替换的占位符。

`advantage_basis` 的顶层固定字段完整集合为 `projection_key`、`dimension_id`、`cb_observation_ref`、`cb_observation_digest`、`cb_gap_type`、`cb_gap_locator`、`atom_observations`、`gap_atom_refs`、`stage_observations`、`gap_stage_refs`、`quality_feature_observations`、`gap_quality_feature_refs`、`strict_improvement_refs`、`non_regression`、`kd_completion_refs`、`kd_completion_surfaces`、`kd_completion_digest`；不得增加自定义字段或把字段移到另一层，嵌套数组/对象必须逐项符合 `config/task5-quality-result-v3.json` 的 authority contract。`kd_completion_digest` 不把自身纳入输入：先取同一 basis 的 `projection_key`、`dimension_id`、按 UTF-8 字节排序的 `kd_completion_refs`、按 UTF-8 字节排序的 `kd_completion_surfaces`、按 UTF-8 字节排序的 `strict_improvement_refs` 和布尔 `non_regression`，组成固定对象；对该对象做 UTF-8 canonical JSON（递归 key 排序、无空格、末尾 LF）后 SHA-256。`observation_digests.reader` 必须等于这个重算值；缺字段、额外字段、数组未按规则排序或 digest 不等都为 `UNKNOWN`。`cb_gap_type` 只能取 `missing_stage|wrong_relation|unreachable|untyped_contract|missing_taxonomy_axis|unsupported_answer_claim|wrong_page_type|missing_provenance|untraceable_claim`，并且必须符合当前 DIM 的 allowed gap types；observation row 的 `score` 只能是有限 JSON number 或在 `unknown|forbidden` 时为 `null`；`status=absent` 或 `applicable=false` 时 `score` 必须为 `null`，不得为 0 或其他诊断数值。

所有 `manifest.routes` row 都是 Home.route row；每行的 `selected_page_ids` 必须恰好一项，且 `home_target_page_identity` 必须非空并等于该目标 ReaderPage 的 `page_identity`，零项或多项都是确定性的 route contract failure，不允许由实现选择“第一个”。本合同不再区分另一类 answer route row，也不存在 `home_target_page_identity=null` 的 route row。每个 answer section 生成两个且仅两个独立 render unit：`Reader.section`（`slot=heading`，表示章节标题）和 `Reader.answer_body`（`slot=heading`，表示该章节正文）。有首个 evidence binding 时，二者都复用该 binding，分别计入 `rendered_units`/`bound_units`；body 精确为 `原始资料未明确` 且 evidence 为空时，二者仍保留为两行 Audit ledger，但都只计入 `unknown_units`，不计入事实 lineage 分母。heading 必须在同一页面的全部 section/answer_body 组合中非空且唯一，重复 heading 直接失败。

单条 CompanyBrain observation row 的 `cb_observation_digest` 定义为：取该 row 固定字段 `case_id`、`projection_id`、`dimension_id`、`status`、`score`、`source_refs`、`visible_ref`、`audit_ref`、`gap_ref`、`kd_ref`；其中 `source_refs` 按 UTF-8 字节排序，其余字段保持冻结值；对该固定对象做 UTF-8 canonical JSON（递归 key 排序、无空格、末尾 LF）后求 SHA-256 小写 hex。`observation_digests.companybrain` 必须等于该值；`observation_sha256` 仍是包含全部 rows 的外层 hash，不能代替单 row digest。`text_sha256` 是 Reader unit 可见文本字符串（不含 Markdown 标记、前后空白和换行壳）的 UTF-8 bytes hash；`block_content_sha256` 是 raw 快照按 byte span 截取的原始 block bytes hash；`support_sha256` 是按 `(source_id,start_byte,end_byte)` 排序后，将每个 raw support span bytes 用单个 `0x00` 拼接的 hash；三者均为小写 64 位 SHA-256，quality.py/M401/M402 必须重算，不能信任模型自报。

`applicable` 只能从冻结 quality-cases 的 projection/dimension contract 派生。若该 contract 明确双方都不适用，row 才是 `N/A`；CompanyBrain 文件缺失、观察缺失、字段缺失或 hash 漂移一律是 `CB_MISSING`/`UNKNOWN`，不能写成 `N/A`。released 谓词是：所有 `applicable=true` 的 projection×dimension row 都为 `KD_WIN`，所有 `applicable=false` 的 row 恰为 `N/A`，且没有任何其他 verdict、缺行或额外行；平局、基线缺失、证据未知都不通过。

本段中的 `slot=heading` 是文档简写，不是字面值；实现必须把该 section 的实际 heading 文本写入 `slot`，并以同一文本重算 `unit_id`。

`text_sha256` 的输入唯一是 renderer 生成的 `visible_text`：先将 CRLF/CR 归一为 LF，做 Unicode NFKC，去除首尾 ASCII 空白和末尾换行，不去除内部换行；Reader 的 title/question/summary/axis/page_type/section 使用对应 typed semantic scalar，answer_body 使用对应 section 的纯文本 body，所有 Markdown 标记（如 `#`、`**`、反引号、链接包裹符）在 renderer 产生 `visible_text` 前已不属于该 scalar。随后直接对该字符串 UTF-8 bytes 求 SHA-256；不再由 verifier 自行猜测 Markdown 剥离规则。`support_sha256` 唯一是 `SHA-256(span_1_bytes + 0x00 + span_2_bytes + ...)`，span 按 `source_id` 的 UTF-8 bytes 升序、再按 `start_byte` 数值升序、再按 `end_byte` 数值升序排列。

本合同的边界细则只有这一处定义：C3/M401 的受控行数统一称为 `fixture_source_count`，只有 M402 的真实 RunManifest 固定要求 89 行；隔离 bundle 的 `run_root_sha256` 只哈希除两个 run-result 文件外的 regular-file tree；title slug 的字母数字集合是 Unicode `Letter`/`Nd`，非空 title 生成空 slug 时使用 `untitled`，空 title 直接失败；失败索引 basename 固定为 `bundle`；空 body section 不渲染，也不生成 `Reader.section`/`Reader.answer_body` unit；每个 `manifest.routes` row 都是 `Home.route` row，必须只有一个非空 `home_target_page_identity`，不允许 null 分类。M401 `attempt-receipt.json.packet_sha256` 取 M401 packet 完整 UTF-8 文件字节，与 M401-R 的 `m401_packet_sha256` 相等，不使用去掉 `canonical_sha256` 后的内部 hash。每个 `(product_key,page_type)` 目录维护整个目录的最终文件名占用集合，按 `(product_key,title,page_id)` UTF-8 bytes 升序，从 `base_slug`、`base_slug-2`、`base_slug-3`……选择首个未占用名，追加后缀前将 base 截断到 `100-len("-N")` 个 Unicode code point；占用集合同时包含其它 base slug 组的基名和后缀名。C0/M401 必须覆盖这些反例。

## 验收标准

| AC | 当前验收条件 |
| --- | --- |
| AC-v4-01 | 89 条 raw 来源、四产品归属和 source manifest 闭合。 |
| AC-v4-02 | 垂直 slice 先行且不缩小 89 条 full closure。 |
| AC-v4-03 | ready source 的 provider 语义编译、失败分流和调用预算可回查。 |
| AC-v4-04 | typed semantic output、Claim、projection 和五类 Reader page 合同通过。 |
| AC-v4-05 | Reader 每个事实 unit 都有唯一 raw→Claim→Audit lineage。 |
| AC-v4-06 | 五个冻结问题/场景入口从 Home 可达且唯一命中 Reader。 |
| AC-v4-07 | public bundle 只有十一项 machine closure、四产品目录和允许路径。 |
| AC-v4-08 | 89 条来源的 ready/empty/duplicate/failure 状态与 Audit 闭合。 |
| AC-v4-09 | Jina selected closure 进入 route ledger、Qwen payload 和 Reader/Audit。 |
| AC-v4-10 | 五项适用维度逐 projection 全部严格 `KD_WIN`，其余恰为 `N/A`。 |
| AC-v4-11 | provider、秘密、hash、SND、质量和原子发布边界可验证。 |
| AC-v4-12 | WorkflowHub、实现审查、M401/M401-R/M402 绑定同一当前身份。 |
| AC-v4-13 | 旧结果根因回放保持独立；不可回查不阻断 raw-only，但不能冒充完成。 |

## ARCHIVE-NON-ACTIVE: previous root material

# mini-task spec：结构化 Reader 编译

## 结果

给定真实来源目录和可选 Task3 语义候选，KnowledgeDigest 生成按产品、模块、知识页组织的 Reader Bundle；Reader 干净可读，哈希和审计字段只出现在 Audit。

## 流程与范围

维护者指定输入和候选输出目录；系统冻结普通 Markdown/文本/JSON，记录路径、产品、指纹和行数；按“产品→模块→知识页”编译；生成产品 overview、模块索引、来源入口、Audit 和一页汇总；机器检查覆盖、导航、泄漏和 300 行限制。

```text
bundle/README.md  Home.md  index.md  products/index.md
bundle/products/<product>/{index.md,overview.md,modules/index.md}
bundle/products/<product>/modules/<module>/{index.md,knowledge/<knowledge>.md}
bundle/references/sources.md
audit/source-manifest.json  ...运行、指纹、质量、失败证据...
reports/projection-report.json  quality.json  release-summary.json
```

`bundle` 是日常入口，`audit` 是追溯/恢复/排错入口。Reader 不放完整 source id、topic id、content hash、fingerprint、生成器、验证事件、provider 配置或逐页机器信号。

每个产品另外生成 `knowledge-types/<type>/index.md` 作为类型入口，类型只做可追溯来源投影：产品定位与边界、模块手册、技术实现、经验与坑、规范与资产。它们链接既有唯一知识页，不复制正文，不增加第二份事实。

## 状态

`snapshot` 输入冻结；`candidate` 已生成未过门；页级 `published/degraded/failed` 描述单页；包级 `released/not_released` 描述整套交付。失败或未知不得升级，失败运行不覆盖旧正式包。

## 成功边界

- 89 条真实有效资料全部有且只有一个 Reader 逻辑知识入口；超长入口拆成连续 `part-01/part-02` 页面，不丢内容。
- 每个产品有 overview/index，每个模块有 index，Home 可达每个知识页。
- 每个产品至少有一个真实类型入口；类型入口可回到唯一知识页，不把经验、规范和产品资料继续混在一个平面。
- Reader 去除内部元数据、哈希脚注和审计块，保留事实、结构、代码、表格、链接和来源入口。
- 结构、覆盖、泄漏、链接、行数检查通过；语义覆盖与保真整理覆盖分开记录。

## 失败边界

- 读取/编码/空内容失败：只写 Audit，整包 `not_released`。
- 无法确定产品：进入 Reader 的 `products/unclassified/modules/general/knowledge/`，页面标 `degraded`，Audit 记录原因；不伪造产品，但不让来源消失。
- 软链接、导航逃逸、非新候选目录或旧包保护失败：停止且旧包不变。
- provider 不可用：允许保真整理 candidate，但不能宣称语义质量或 released。
- 重复落点、事实损失：机器失败，不静默发布。
- 超过 300 行：按 300 行硬上限拆成连续页面，页间有上一页/下一页链接；拆分失败才进入 Audit 失败。

## 非目标

不重走 make-decision，不用 build-spec 补需求；不改 TopicIndex、Task2-C 17+3 和状态语义；不新增本体、向量库、数据库、调度器或 AgentMemory；不修改 CompanyBrain；不增加逐页人工验收。

## 验收条件

- AC-01 产品→模块→知识页层级存在。
- AC-02 产品 overview/index 可读。
- AC-03 有效来源唯一落点且完整对账。
- AC-04 Reader 无哈希、指纹和内部字段。
- AC-05 正文清理但不丢事实。
- AC-06 Home→产品→模块→知识页全链路可达且每页≤300行。
- AC-07 语义不可用时诚实降级。
- AC-08 失败不覆盖旧正式包。
- AC-09 一页汇总保留人工确认边界。

## 80 分代理口径

这是机器可复算的结构质量代理，不是对 CompanyBrain 的主观等价承诺：结构层级 20 分、有效来源覆盖 20 分、产品入口 15 分、Reader 清洁度 15 分、内容保真 20 分、溯源入口 10 分，共 100 分；每项按实际通过比例计分，`score >= 80` 才能标记 `reader_quality_proxy_passed`。语义 provider 不可用时仍可生成 candidate，但必须单独标注 semantic unavailable。

## 最小依赖接口

- source manifest：`source_id`、`source_uri`、`relative_path`、`title`、`content_fingerprint`、`line_count`、`validation_status`。
- semantic candidate：`source_uri`、`content_fingerprint`、`title`、`summary`、`body`、`module`、`semantic_status`。
- Audit 映射：`source_id`、`reader_paths`、`product`、`module`、`mapping_reason`、`content_fingerprint`、`semantic_status`。
- 可选 TopicIndex 只读取 `source_members/source_ids/product/module/object_intent/published_path`；TopicIndex 不被本 mini-task 改写。
