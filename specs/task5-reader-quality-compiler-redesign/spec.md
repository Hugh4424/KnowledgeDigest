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

## ARCHIVE-NON-ACTIVE: 历史合同 v4（非生效）

## 已废止合同 v4（历史归档，非生效）

### 目标与五项硬门

KnowledgeDigest 只读取 `/Users/Hugh/Downloads/confluence 原始数据`，在同一 Task5 内完成垂直切片和 89 条全量消化，生成可直接阅读的知识。质量不是目录数量或平均分；以下五项必须逐项严格 `KD_WIN`，且逐项高于 CompanyBrain：问题/场景路由、产品/模块/对象/场景/边界分类、业务化答案正文、定位/概念/操作/诊断/经验页面类型、Reader 可读与 Audit 可回查。任一 projection 的任一维为 `UNKNOWN`、`TIE`、`INVALID`、`CB_WIN`、`CB_MISSING` 或缺证据，结果只能为 `not_released`；只有全部五项通过才可 `released`/close。

### 输入、模型和范围

- raw、CompanyBrain `/Users/Hugh/Hugh/Knowledge/CompanyBrain`、旧候选和旧 review 都是只读事实，不能作为新正文来源。
- 当前 raw 事实是 89 条、4 个产品、87 条普通非空、1 条已知空源、1 条重复别名；空源和别名必须进入闭包与 Audit。
- provider 配置只读 `/Users/Hugh/.config/knowledge-digest/config.json`；LLM 允许 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.6`/`qwen3.8`，embedding 允许 `https://llm.paxszapp.com/v1` 的 `jina-embeddings`。key 只在内存中使用，不落到 payload、receipt、cache、bundle 或报告。
- slice case、路径和风险标签只从 `config/task5-slice-cases-v1.json` 派生。当前实际派生 11 个 case、27 个唯一 source path；实现不得继续使用旧的 14/12 常数。
- 当前切片 authority 固定为 `config/task5-slice-cases-v1.json`：实际字节 SHA-256=`62703a6cc06c006ea90c7be28f392cab7fd4f9918f2da384179548ca42c89cef`，canonical SHA-256=`f346b9b2bd67cf48a0fd37654e41780ed7c3f0c870ad5c9dddc04df7be80cef`。派生规则是读取 `cases[*].source_paths`，按 case 文件出现顺序保留首次出现、去重；排序只用于统计和比较，不改变运行闭包。当前派生事实为 11 case、27 unique path、25 ready、1 blank、1 duplicate_alias。旧材料中的 14/13/12 和旧切片 hash 只属于历史归档，不能作为运行输入。
- 这是一个有意保持在同一 Task5 的完整 mini-task：切片、89 条 full、真实 provider 和五项对照都不能延期到后续任务。这个范围是用户已确认的 accepted risk；降低范围不算修复。

### 唯一生产链和责任

```text
digest CLI → compiler.digest → providers(Qwen/Jina) → publisher.commit
```

`compiler` 是唯一编译入口；`providers` 只负责 Qwen typed semantic compile 与 Jina route；`publisher` 只负责安全、一次、原子写入。旧 `task5_runtime.py`、`task5_provider.py` 和旧 evaluator 可以留作历史/回归资料，但生产入口不得 import 或调用它们。

```text
raw snapshot → Evidence(Block/Claim) → Jina route → Qwen typed output
→ ReaderPage → Home/Audit/RunManifest → 五项质量重算 → 原子发布
```

Qwen 是业务正文唯一来源。renderer/compiler 不得补业务句子、补标签、拼原文、用 overlay 修结果或静默重生成；Qwen 输出不合法只进 Audit failure。Jina descriptor 只能来自当前 raw/Evidence，selected closure 必须同时进入 route ledger、实际 Qwen 输入、ReaderPage、Home route 和 Audit；只记录调用不算消费。

### Reader 流程和输出树

读者路径固定为 `Home → 问题/场景入口 → 产品 → 模块/对象 → 场景/边界 → 业务答案页 → Reader 证据 → Audit 精确来源块`。公开树固定为 `bundle/README.md`、`bundle/Home.md`、`bundle/Audit.md`、`bundle/products/<product>/<page-type>/<readable-title>.md` 和 `bundle/_audit/{run-result,evidence,sources,quality}.json*`；禁止 `modules/`、`boundaries/`、`knowledge/`、hash-only 文件名、staging/attempt 路径。产品目录只允许四个 raw 产品；跨产品答案放 `products/shared/`。

Home 必须同时提供按问题和按场景入口。Reader 正文必须可见地展示五轴、页面类型、直接结论和证据链接，不能只放 frontmatter。Audit 记录 source id、原始相对路径、内容 hash、block/claim、行/byte locator、引用关系和失败原因，不复制整篇 raw。正文必须是短段落、列表或表格，无法从 raw 确认的内容写“原始资料未明确”。

### 语义和机器闭包

- Evidence 是 raw 的 Block/Claim 闭包；每个 block 恰好对应一个 claim，带 source、hash 和行/byte locator。
- ReaderPage 只保存通过 typed semantic 校验的答案、五轴、页面类型、引用 evidence 和 selected closure。
- RunManifest 是唯一运行闭包索引，不生成正文；`sources` 恰好 89 行，`pages`、`routes`、失败状态和 tree hash 必须与实际输出相等。
- `page_key` 由 compiler 派生：source 页为 `source:<source_id>`，答案页为 `answer:<question_id>:<page_type>`；Qwen 不自报随机身份。
- `question_id`、payload、surface、tree hash 统一由实现使用 canonical UTF-8 JSON 计算并测试；调用方不能自报或从文件名猜。

Qwen 响应必须严格为 `task5-semantic-output.v2`，只允许 `schema_version`、`title`、`page_type`、`page_type_claim_ids`、`axis`、`axis_claim_ids`、`summary`、`sections`。所有页面句子、五轴和 section 都必须有当前 Evidence；缺字段、未知字段、越界引用、类型不符、无证据、原文复制、改变数字/否定/条件均只进 Audit。

每条 source 在 RunManifest 中只能有一个终态：`ready`、`blank`、`duplicate_alias`、`failed`、`unsupported`。输入错误映射为 `failed` + `input_invalid`，编码错误映射为 `failed` + `encoding_invalid`；优先级为输入/编码错误 > blank > duplicate_alias > failed > ready。blank 不进 Home/Reader，duplicate alias 只链接 canonical Reader，不生成第二份正文。

### 当前验收标准（AC-v4-01…AC-v4-13）

以下是当前合同唯一生效的 AC 集；M401 的 AC trace 必须逐条给出命令、输入 hash、输出 ref 和结果，不能引用下方历史归档中的 AC-001…AC-021。

1. `AC-v4-01`：raw 快照与 `task5-source-page-manifest-v2.json` 都是 89 条；每条都有 source id、相对路径、字节 hash、行/byte locator 和唯一终态。
2. `AC-v4-02`：slice case 只从 `task5-slice-cases-v1.json` 派生；11 个 case、27 个 unique path 是运行时重算事实，不能写死旧数量；slice 之后仍必须执行同一 Task5 的 89 条 full。
3. `AC-v4-03`：每个 ready source 恰好一次 `source-digest` 语义编译；Qwen 失败、证据缺失、冲突或越界只进入 failure sink/Audit，不得 raw fallback、原文拼接或静默重试。
4. `AC-v4-04`：每个质量 projection 都从当前 raw Evidence 生成，使用 `task5-semantic-output.v2`；Qwen 输出只能含合同字段，页面身份由 compiler 派生。
5. `AC-v4-05`：每条 Reader 业务句、五轴、页面类型和 section 都能回到本次 source→block→claim→semantic-frame；无法确认的内容明确写“原始资料未明确”，不补外部知识。
6. `AC-v4-06`：Home 同时提供问题和场景入口；入口能到产品、模块/对象、场景/边界、答案页，Reader 页面可见直接结论、五轴、页面类型和证据链接。
7. `AC-v4-07`：公开树只含 README/Home/Audit/products 和 `_audit` 六类机器文件；四个产品归属正确，跨产品页进入 `products/shared/`，不得出现 `_digest`、`modules/`、`boundaries/`、`knowledge/`、staging、attempt 或 hash-only Reader 路径。
8. `AC-v4-08`：Audit 对 89 条来源、每个 Reader claim、block、hash、locator 和失败原因闭合；duplicate alias 指向 canonical Reader，known empty 只进 Audit，不生成伪正文。
9. `AC-v4-09`：每次 Jina route 的 selected closure 同时进入 route ledger、实际 Qwen payload、Reader/Audit；仅记录 embedding 调用不算消费。
10. `AC-v4-10`：五项质量逐 `case × projection × dimension` 从本次 Reader/Home/Audit/route ledger 和 CompanyBrain observation 重算；每项必须有 strict improvement、non-regression、gap ref 和独立证据，任何 `UNKNOWN/TIE/INVALID/CB_WIN/CB_MISSING` 都阻断。
11. `AC-v4-11`：真实运行的 provider call ledger、响应 hash、配置/合同 hash、source closure、发布树 hash 和 secret scan 完整；key 不出现在任何落盘材料；发布使用 create-only staging 和原子提交，失败不得污染旧结果。
12. `AC-v4-12`：当前 WorkflowHub implementation review、M401、M401-R、implementation successor、slice/full 和最终质量证据必须绑定同一 task/worktree snapshot/material；设计审查只作可选 advisory，缺失不阻断；其余任一硬证据缺失只能 `blocked` 或 `not_released`，不能 close。
13. `AC-v4-13`：必须对用户指出的旧结果做一次 provider-free root-cause replay；V50 原始候选不可回查时，必须落盘 `blocked/calls=0` 证据并保留“待验证”状态，不能把 raw-only 当前运行当成根因解释完成。

### AC-v4 当前 trace 对照表

M401 必须为每行保存本次命令、输入 snapshot/material、输出 ref+SHA、实际结果和失败反例；下表是 AC 的唯一动作与 receipt 映射，不能只写“测试通过”。

| AC | 检查范围 | 必做动作 | 主要证据 |
| --- | --- | --- | --- |
| AC-v4-01 | raw 89 条 | 重算 manifest 与定位 | C1/M402 source receipt |
| AC-v4-02 | slice→full | 从 slice JSON 派生并续跑全量 | C0/M402 run context |
| AC-v4-03 | source-digest | 每个 ready source 恰好一次 Qwen | C2 provider ledger |
| AC-v4-04 | typed semantic | 校验 schema、Claim 和 projection | C2/M401 test receipt |
| AC-v4-05 | Reader 血缘 | 逐句重算 raw→Claim→Audit | LINEAGE-001 |
| AC-v4-06 | 问题/场景入口 | 回放 Home 全部 route | OUTPUT-001/M402 |
| AC-v4-07 | 产品与输出树 | 校验四产品、禁路径和唯一 bundle | OUTPUT-001 |
| AC-v4-08 | 89 条 Audit 闭包 | 对账 empty、alias、failure、Reader | C1/C3/M402 |
| AC-v4-09 | Jina→Qwen | 比较 closure、payload、route ledger | C2 provider ledger |
| AC-v4-10 | 五维对照 | 按 DIM-01…05 逐 case/project 比较 | M402 quality result |
| AC-v4-11 | 发布与秘密 | 扫描 calls、hash、key、原子写入 | C3/M402 run receipt |
| AC-v4-12 | WorkflowHub | 校验同 task/worktree/snapshot 链 | DESIGN/M401/M401-R |
| AC-v4-13 | 旧结果根因 | 回放精确 V50；不可回查则 blocked | ROOT-CAUSE receipt |

### 四产品唯一归属规则

raw 相对路径的第一级目录先做 Unicode NFKC、去首尾空格、casefold，再按下表映射；`product_key` 和 `product_label` 必须同时写入 `sources.jsonl`、RunManifest、ReaderPage 和 Home route。除 `shared` 的跨产品答案外，Reader 不能跨产品落点。未知一级目录进入 `unclassified` 并令产品闭包失败，不得静默塞进已有产品。

| raw 一级目录 | product_key | product_label |
| --- | --- | --- |
| `GoInsight` | `goinsight` | `GoInsight` |
| `emm for android` | `emm-for-android` | `EMM for Android` |
| `emm for ios` | `emm-for-ios` | `EMM for iOS` |
| `merchant system` | `merchant-system` | `Merchant System` |

产品映射只决定归属，不替代 Qwen 对 module/object/scene/boundary 的证据判断；任何轴值仍需按 route ledger 的 raw `evidence_bindings` 回查。

### C0 authority 闭包

C0 的有限 authority 集合不是隐含输入：它由 1 个 `config/task5-runtime-authority-map-v1.json`、其中 17 项 `authorities` 和 4 个评价输入 `config/task5-quality-cases-v2.json`、`config/task5-companybrain-baseline-v2.json`、`config/task5-source-page-manifest-v2.json`、`config/task5-slice-cases-v1.json` 组成，共 22 个文件；`task5-run-result.v1` 只作为 machine-evidence 的嵌套字段合同，不是第二个运行文件或第二个公开 schema，其他 `task5-*.json` 都是历史或示例，不进入当前运行。C0 必须读取每个文件的真实字节，记录相对路径、schema、actual SHA-256、canonical SHA-256、size 和交叉引用结果，生成 `authority_inventory`；缺文件、额外文件、schema/hash/交叉引用不符即 `blocked/calls=0`。材料审查只审这个有限集合的清单和规则，不把未提交的 raw、CompanyBrain 或 secret 当作 design 输入。

当前 review packet 直接携带以下权威清单；运行前仍必须由 C0 重新读取真实字节并复 hash，表内 hash 不是 caller 自报值：

| path | schema | bytes | actual SHA-256 | canonical SHA-256 |
|---|---|---:|---|---|
| `config/task5-runtime-authority-map-v1.json` | `task5-runtime-authority-map.v1` | 8290 | `2369e3fe8233b251d1841a761a42a64158a22f8030252d6bd3a4246bd3afb88e` | `d305a27eb48892a17a0d45a640332f4b14a811c514296624a65b9d79bf9da896` |
| `config/task5-external-processing-policy-v1.json` | `task5-external-processing-policy.v1` | 3127 | `145339af1da2170e386ccbb41a82e8041e1e08743ae610d5b20aa48f3c47b01a` | `24fe898c759ff2d4ff4ff628635978250590d2ca27daea007ddf1be639bd890c` |
| `config/task5-provider-contract-handshake-v3.json` | `task5-provider-contract-handshake.v3` | 4581 | `c15c06120550ddab294540c91376ac480cd64e82617c3a8edbebee162e34dee0` | `fc821c355525e6e7efb3889140da4688087e08a26d664b9e4de04e8f217ee978` |
| `config/task5-provider-prompt-contract-v1.json` | `task5-provider-prompt-contract.v1` | 1758 | `1e8888cb045ada6e242ab14a4e990832571cbe36d56305b5b626bdc7dd83236b` | `791ac7e1416d55228623de03961d61d6bdb82a98bd9044a28e7d927fdff1d1eb` |
| `config/task5-provider-semantic-output-v2.json` | `task5-semantic-output.v2` | 3223 | `e5fd5d67793eca583683ef331ac61b0a0f72e9f10257f7e9ead5826d4a82db7e` | `e34826caedf40d6c1a6879063d0f1bf246c2cb974446128830dc5a5b6ce45625` |
| `config/task5-publication-layout-v2.json` | `task5-publication-layout.v2` | 2256 | `653fbbedafa09b9737af10b5da4fe8083f8b6131cf10636b277511984df803bc` | `4b69e256c11afab703c09ac8206a29b3c1ccd4fe580b838459f7480e842239b6` |
| `config/task5-reader-quality-provider-v2.json` | `task5-runtime-config.v2` | 2209 | `44ccb2888ae309a350cbd63af337cc0420d6934d0cd9245a04aff3ae973f9383` | `4b9781618035ed3c534a021b831da649254b9d19d4818e36704895b2d9623607` |
| `config/task5-replay-store-v1.json` | `task5-replay-store.v1` | 2309 | `56e2198d5bb1d16c0c99d61fb3abd0e5a728619622d1d2fe8ac0409a25bd6457` | `702699887a06b16e331b134074e6e1f0fa92d8edcab6030cbb5e2d9d6ce29989` |
| `config/task5-semantic-frame-v1.json` | `task5-semantic-frame.v1` | 3771 | `e864fd5f976a5641ffda5db662eceb2ce85687f5fabf250dc7e337b73f264ae6` | `4f00f2e44e21545176f02299dbc8df7ba8f96052f3ee98ec2c926a03221c0596` |
| `config/task5-semantic-frame-field-closure-v1.json` | `task5-semantic-frame-field-closure.v1` | 3983 | `d2a560e7b06d9c5edaf031de0565abd4d86a9fc77613e26bc1b954212c6acc20` | `a3c7bd6b7c4757f9a4d38599768889b85fc66dbab4d8f5ed574dd9ba74d24262` |
| `config/task5-source-block-claim-contract-v1.json` | `task5-source-block-claim-contract.v1` | 3882 | `02898de03f72ad2ccfe7998cff9b4c4362cde95e71ed3aa0cdd35a5a00ce9b71` | `4baa67603f01aa1e1f114b08cf352a03d51d67035071feb3894f499af6983639` |
| `config/task5-reader-path-relation-contract-v1.json` | `task5-reader-path-relation-contract.v1` | 6359 | `c3f121667332680b89ae852d77a025b8587e7867442d5eb83a071146a131d3c6` | `16de1b3cc481d88443961e0b5d8e54fbc3338cfc8b54bb36ece7a53a609452c5` |
| `config/task5-source-digest-contract-v2.json` | `task5-source-digest-contract.v2` | 10640 | `2321eeb6b21e119695f458f440b69f89837ea6a58c7286b7089108effcda7fda` | `82134f7323268114acc36dd618f706d61fbdb97b5def77dd07020408e8eb9280` |
| `config/task5-source-not-documented-contract-v2.json` | `task5-source-not-documented-contract.v2` | 7688 | `762f09595fe33d33531dd373cb0bf4f3cf1ee468442d0ebccb68314af7534fa5` | `253de24de01625c4fa14c5bfab57e81c3ef56dbbd6319fd89f4150152b4263fc` |
| `config/task5-source-sensitive-content-scan-v1.json` | `source-sensitive-content-scan.v1` | 5239 | `1253ab1e1e31ae7d737183d8ac8ffb85d9e5f83a2bc76b534195bbc4339d53d5` | `5836aa4631c29d5d6117eed42c47f886e1edfe36df3c03ee97bbfcc2743dff2e` |
| `config/task5-root-cause-evidence-v2.json` | `task5-root-cause-evidence.v2` | 4840 | `6b75d70ed2db0820aeea99e82a86ae241212d6e51246e3b8f449523faa580985` | `cd4751b98da5f743faf4a8a81624ac335c219e6df803c3a44dd7e962b3d5e971` |
| `config/task5-root-cause-input-manifest-v1.json` | `task5-root-cause-input-manifest.v1` | 4089 | `2909de6d6159deeaebdf620ad4bd91655e807f4ca30bde2bdd14e95b287c44ad` | `32119ff0ce97874889c76191a70979350a353c65c65b8d14cf4e53a69a937d3f` |
| `config/task5-machine-evidence-contract-v1.json` | `task5-machine-evidence-contract.v1` | 12746 | `df96f45ab66aa58c02867834ea1d3f01051fb750a401ce2c71c46d52d0eb01ae` | `2afc28ccabd930d77ddf9278f546b1a81b3d72e6df66b129d00b70406685f882` |
| `config/task5-quality-cases-v2.json` | `task5-quality-cases.v2` | 258011 | `09272cb6612a604412c0f4b2d63955fb50739915aa0890707a3cdb36edcd19b5` | `96970a9f1630c75d7d7edc17b06f120043d6721257d14fdc4aa62f089d53462b` |
| `config/task5-companybrain-baseline-v2.json` | `companybrain-baseline.v2` | 14774 | `3f29e710d9fa90dcceb3e4b3652252bf786219583058408385e392a08beaddf3` | `9d838ea5578a6d67d45f5cb96f218d23ad0da3e148a8e7e248ba3b214be307e5` |
| `config/task5-source-page-manifest-v2.json` | `task5-source-page-manifest.v2` | 174851 | `54f54bb2b6d589f403862d4049ee0cfec5973121c4de757e4b327d2f51448973` | `a50988b46284db93993967da18ef95fdbd70c02d0233195c84e1b21670def20f` |
| `config/task5-slice-cases-v1.json` | `task5-slice-cases.v1` | 3169 | `62703a6cc06c006ea90c7be28f392cab7fd4f9918f2da384179548ca42c89cef` | `f346b9b2bd67cf48a0fd37654e41780ed7c3f0c870ad5c9dddc04df7be80cef8` |

### RunManifest / RunResult 的机器合同

`bundle/_digest/run.json` 是唯一运行结果文件；其中 `manifest` 是唯一 `RunManifest`，必须严格满足 `knowledge-digest-run-manifest.v1`：顶层只允许 `schema_version`、`source_count`、`sources`、`routes`、`pages`、`tree_sha256`；source 行只允许 `source_id`、`relative_path`、`raw_hash`、`status`、`duplicate_of`、`evidence_ids`、`reader_page_ids`、`failure`；page 行只允许 `page_id`、`page_key`、`page_type`、`axes`、`source_ids`、`path`、`surface_sha256`；route 行只允许 `query_id`、`question`、`scene`、`candidate_source_ids`、`selected_source_ids`、`selected_page_ids`、`scores`、`embedding_receipt`、`qwen_payload_sha256`、`status`、`failure`。source/page/route 的集合、引用和状态必须由实际 bundle 逐项重算。

`run.json` 外层是 `knowledge-digest-run.v1` RunResult；它必须至少包含 `run_id`、`evaluation_mode`、`source_selection`、`created_at`、`outcome`、`source_manifest_hash`、`source_count`、`reader_page_count`、`quality_projection_count`、`quality_page_count`、`manifest`、`provider_calls`、`provider_attempts`、`provider_budget`、`provider_call_plan`、`provider_identity`、`warnings`、`known_empty_sources`、`quality_status`、`release_status`、`reader_contract`，且不能把 key、Authorization、prompt、response raw、主机绝对路径写入。canonical JSON 固定为 UTF-8、递归 key sort、无空格、`ensure_ascii=false`、末尾 LF；`manifest_sha256=sha256(canonical(manifest))`，`tree_sha256=sha256(每个已发布文件按相对路径排序后的“文件 sha256 + 两空格 + 路径”行，排除 run.json 及所有 hash receipt)`；run.json 的自引用 hash 必须放在外部 receipt，不得参与自身计算。任何声明值与重算值不等即 `blocked/not_released`。

身份规则固定为：`source_id = src-` + `sha256(NFC(relative_path) + NUL + raw_bytes)[:20]`；`question_id = sha256(NFC(question) + NUL + NFC(scene) + NUL + NFC(scope))[:20]`；`payload_sha256 = sha256(canonical_json(route_kind、source/claim closure、query、prompt contract、provider identity))`；`surface_sha256 = sha256(Reader 文件 UTF-8 bytes)`。`readable-title` 只做 NFC、trim、连续空白/标点转 `-`、去首尾 `-`、最多 80 个字符；空标题或同一 product/page-type 下的路径碰撞直接 `blocked`，不追加 hash、顺序号或随机 UUID。`page_key` 由 compiler 按 source/answer 规则派生，不能由 Qwen 或文件名反报；任意身份在 source permutation、block hash drift、route closure drift 后必须变化，未变化即失败。

### Reader RenderLedger 与质量结果

`_digest/evidence.jsonl` 是 `RenderLedger`，每行必须严格为 `knowledge-digest-render-unit.v1`：`unit_id`、`page_key`、`page_path`、`surface`（`Reader.summary|Reader.section|Reader.axis|Home.route`）、`text_sha256`、`audit_ref`、`claim_ids`、`evidence_ids`。每个非空 Reader 句子/轴值/section 和每个 Home route 都至少有一行；`audit_ref` 必须指向 Audit 中同一 source、block、claim、raw hash 和 line/byte locator。Ledger 不存 prompt、response、key 或整篇 raw；孤儿 unit、重复 unit、无 evidence 的业务句或 Audit ref 漂移均阻断。

`quality.py` 是唯一纯质量裁决器：读取本次 Reader/Home/Audit/route ledger、冻结 quality cases 和 CompanyBrain observation，返回 `knowledge-digest-quality-result.v3`；compiler 只负责把这个结果写入 `_digest/quality.json`，不再存在第二个 evaluator。结果顶层固定为 `schema_version`、`run_id`、`status`、`case_count`、`projection_count`、`dimensions`、`records`、`guards`、`baseline_binding`、`candidate_binding`、`result_sha256`；`records` 每行固定为 `case_id`、`projection_id`、`dimension`、`status`、`advantage_basis`、`companybrain_observation_ref`、`candidate_surface_refs`、`audit_refs`、`reason`。只有 `status=KD_WIN` 且 `advantage_basis` 同维度包含 gap atom、strict improvement、non-regression 和完整 surface/lineage refs，才可进入 released 谓词；`result_sha256` 计算时排除自身字段。

### 特殊来源与发布失败语义

`known_empty` 的成立条件是：manifest 精确声明该路径为空、raw 快照 hash/字节/行数一致、Audit 有 locator、RunManifest 有唯一 `known_empty` 终态；它保留在 89 条分母但不生成 Reader。`duplicate_alias` 的成立条件是：两个来源 raw content hash 完全相同、alias 行绑定 canonical source id、两者均有 Audit/coverage row，且 alias 的公开入口只链接 canonical Reader。任何一项不满足，不是“可忽略的特殊情况”，而是 `failed/not_released`。这是对空源和别名的完整闭包定义，不允许实现自行解释。

### 真实调用预算与重用

M402 以同一个 run context 先做 slice 再做 full；slice 中已经成功且 identity 完全相同的 source-digest 响应必须由 full 精确重用，不得重复发请求。重用必须带原始成功 receipt 和全套 identity；没有精确命中就按新调用计数。当前 authority 派生 `P=12` 个质量 projection，full `R=87` 个 ready source，slice `R=25` 个 ready source，retry 固定为 0：LLM 上限为 `R_full + 2P + 2×min(2,P) = 115`，Jina 上限为 `ceil((R_slice+P)/8)+ceil((R_full+P)/8)=18`，M402 总上限为 133。任何实际计划超过 133，或配置 `budget.max_provider_calls < 133`，在读取 raw、CompanyBrain 或发 provider 前 `blocked/calls=0`。单独 slice/full 的计划也必须把实际 R/P 写入 run manifest，不能用旧的 115+17 或 14/12 数字。

### Publisher 失败恢复状态机

M402 的 Downloads run root 必须是新建的 `/Users/Hugh/Downloads/KnowledgeDigest-task5-reader-quality-compiler-redesign-<run_id>/`；公开结果固定在该目录的 `bundle/`，不是 `/private/tmp`。状态严格为 `preflight → locked → staging → written → verified → committed`，失败状态为 `blocked` 或 `failed`。`publisher` 在同一父目录用 `O_CREAT|O_EXCL` 建立 `.run.lock`，再用唯一 `.bundle.staging-<run_id>` 建 staging；每个文件写入、fsync 后再做 tree/manifest 校验；只有 target `bundle/` 不存在且校验通过时才 `rename`。失败或进程中断不得留下可读半成品 bundle：保留 `failure.json`（状态、reason、attempt、input/contract hash 和 staging ref），staging 只可由本次 owner 在失败清理；锁漂移、旧锁、非空目标或跨文件系统立即停止，不自动覆盖、不自动清理别的 run。成功后只保留 `bundle/` 和脱敏运行 receipt。

### 质量、WorkflowHub 和真实运行

质量配置、CompanyBrain baseline/observation、source manifest 和 slice config 都是只读 authority；结果必须从本次实际 Reader/Home/Audit/route ledger 重算，不能使用静态 verdict、关键词、页数、平均分或“内容更多”。CompanyBrain 缺失只有在完整 observation 和 source-bound 观察共同证明后才能成为 gap，否则是 `UNKNOWN`。

设计、实现、测试、审查和真实运行是不同事实。真实 M402 前必须有当前 snapshot/material 绑定的 authenticated `mini_task.design` terminal-clean、M401 packet、`mini_task.implementation` terminal-clean 和 WorkflowHub implementation successor。缺任一项，M402 在读取 raw/CompanyBrain 和发 provider 前停止，calls=0。

M402 只做一次新 Downloads 运行：同一个 run context 先按 slice JSON 执行 slice，再执行 89 条 full；不得用两次互不相干的 CLI 运行拼接“slice→full”。slice-local 失败留证后继续 full；身份、配置、预算、provider、锁或发布安全失败立即停止。五项全胜、89 条闭包、slice/full、Reader/Audit、Jina 消费、原子发布和 WorkflowHub 证据全通过，才可 released。

### 非目标和延期

不修改 raw、CompanyBrain、旧产物或 main；不接入数据库、向量库、调度器、在线搜索、增量同步、编辑工作台或 agentmemory；不新增评分维度。只允许延期 release/close，不延期 slice 或 89 条 full。

---

## 历史规格归档（非生效）

# Task5：Reader-quality KnowledgeDigest 规格

## 1. 一句话结论

把 89 条原始 Confluence 资料先编译成可回查的语义事实，再按问题和场景生成五类业务答案页；只有垂直切片、89 条全量、Reader/Audit 和五维 CompanyBrain 对照全部通过，才允许发布 Reader。任何缺源、冲突、证据断链或比较不确定，都只能保留 Audit/candidate，不得伪装成完成。

本规格首先定义产品行为、用户可见结果、数据状态和验收合同；本 repair revision 的可执行附录同时冻结 provider identity、输入上限、source manifest、fixture hash 和实现边界。它不把实现文件、代码接口或测试命令当成产品行为；详细文件改动和任务拆分仍由 plan/tasks 承载。

## 1.1 当前修正（2026-08-21 用户复核后生效）

以下修正优先于本文早期仍使用 `source-direct`、`full-source`、逐页 Audit 文件和 hash 路径的描述；它们是同一 Task5 的合同修订，不是新增任务：

- 89 条 coverage entry 中的 87 个普通 present 非空来源必须经过 Qwen 的 `source-digest` 编译；`G-SOURCE-ND` 的 1 个 present 来源由确定性 `source-not-documented` diagnosis projection 替换，不发第二次请求。两者合计最多生成 88 个由原始 Claim/Block 或可证明扫描证据支持的 Reader 页面；SND 没有语义零匹配证书时只能 Audit-only；1 个 `known_empty` 只进 Audit。`source-direct-audit` 仍保留，但只有显式声明该 route kind 时才是 Audit-only。
- `source-digest` 不是 raw/full-source 兜底：Qwen 失败、证据不完整、关系不确定或来源冲突时，不生成 Reader，只保留 Audit/blocked。`source-not-documented` 是独立受控 diagnosis projection，不使用普通失败分流。
- `source-digest` 每次只能消费一个来源的证据闭包；不得把其他来源、CompanyBrain 或模型外部知识放入提示词或正文。
- 用户公开入口固定为新 Downloads 运行目录下的 `bundle/`。用户先读 `bundle/README.md`、`bundle/Home.md`，再读 `bundle/products/<product>/<page-type>/<readable-title>.md`；证据统一进入 `bundle/Audit.md` 和 `bundle/_audit/`。
- Reader 路径禁止 `modules/`、`boundaries/`、`knowledge/` 和内部 projection hash 文件名。内部 ID 只能留在机器 Audit，不得出现在用户页面标题、路径或正文。17 项 runtime authority 的 derived contract hash 由 `config/task5-runtime-authority-map-v1.json` 的当前字节唯一计算；当前值为 `94795519ed45245995d2a720ee80d1e97006ffe17f04aeea8ab59a45ee383ca7`。
- Provider typed JSON 以 `config/task5-provider-semantic-output-v2.json` 为本轮实际合同；runtime authority map 逐项冻结 provider config、handshake-v3、prompt、source-block-claim、reader-path-relation、source-digest、source-not-documented-v2、external-processing-policy、source-sensitive-content-scan、semantic-frame、semantic-frame-field-closure、replay-store、publication-layout、reader-quality-provider、machine-evidence、root-cause-inputs 和 root-cause-evidence。旧 v1/v2 文件只作历史审计材料。所有 authority 的 actual/canonical SHA 只以该 map 为准，本文不复制第二套 hash。
- 当前 provider/runtime authority 的完整 path、schema、actual SHA 和 canonical SHA 只以 `config/task5-runtime-authority-map-v1.json` 为准；该 map 是唯一清单，实现不得从本文或 plan appendix 恢复旧 hash。
- 每个运行目录的根 README 必须指向唯一公开 bundle，并明确运行中 `candidate` 与终态 `not_released/released`；只有五项逐案例全部 `KD_WIN`、89 条来源闭包和 Reader/Audit 重审都通过，才允许 `released`。
- 这次修正改变了 source manifest、provider route、projection 和输出布局的 authority。必须新版本化相关 schema/manifest 并重算 hash，重新取得当前设计/实现审查绑定；旧 v28–v34 和旧 v1/v2 hash 不得作为新运行证据。

## 2. 目标、用户结果与影响

### 2.1 目标

- 把上一轮“目录更整齐”改成“用户能从问题进入正确答案，并能回查每条事实来源”。
- 同一任务完成风险覆盖型垂直切片和 89 条全量，不新增后续任务来补全量。
- 用五个独立维度逐问题/场景比较 KnowledgeDigest 与 CompanyBrain；五维评价是质量证明工具，不是产品目标本身。
- 任何质量不确定都显式暴露为 Audit、blocked 或 `not_released`。

### 2.2 目标用户与用户结果

- 业务读者：提出一个产品、配置、设备入网、故障或复盘问题，能在 Reader 入口找到一页直接可用的业务答案。
- 知识维护者：能看到哪些来源已处理、哪些为空/冲突/失败、哪些 Claim 没有足够证据。
- 审查者：能从每个 Reader 事实回到 source、snapshot、content hash、source block 和 locator，复核原文而不是只相信摘要。
- 交付负责人：能明确知道当前是 `candidate`、`not_released` 还是 `released`，且不会被页数、关键词命中或绿色测试误导。

### 2.3 业务影响

成功时，读者查知识的入口从“找文件”变成“找问题/场景”，内容从来源行包装变成有对象、关系、边界和验证条件的业务答案。失败时，系统会少发布一些页，但不会把不可回查或互相冲突的内容当成公司知识。

### 2.4 权威来源

- `R-001`、`R-002`、`R-003` 及用户最终确认：当前 decision-log.md。
- Task4 v37-88、CompanyBrain 和本地实现：只作为可回查历史事实与比较基线。
- CompanyBrain：只提供问题路由、页面合同、对象关系和来源回查方法参考；不提供当前任务的业务事实权威。
- 当前规格：本文件。它必须完整表达已确认决策，不能把缺失产品决策留给 plan 或 tasks 猜测。

### 2.5 来源与决策映射

| Source ID | Decision ID | FR / AC IDs | 状态与交接 |
| --- | --- | --- | --- |
| R-001、F-003~F-005 | D-003、D-011 | FR-SOURCE-001、FR-BLOCK-001、FR-SEMANTIC-001、AC-001、AC-003、AC-006 | current；Task4 只作基线 |
| R-002、F-006~F-008 | D-009、D-013、D-014 | FR-ROUTE-001、FR-PAGE-001、FR-READER-001、FR-QUALITY-001、AC-004、AC-005、AC-010、AC-011 | current；五维硬门 |
| R-003、G-301~G-303 | D-012、D-014、D-015 | FR-GATE-001、FR-STATE-001、FR-PUBLISH-001、FR-REVIEW-001、AC-002、AC-009、AC-012、AC-013 | current；下游不得补方向 |
| D-003、D-010、D-011 | D-012、D-013、D-015 | FR-FULL-001、FR-RUN-001、AC-001、AC-002、AC-007、AC-008、AC-014、AC-015 | current；全量同任务 |
| DEFER-002、DEFER-003 | D-014、D-015 | OPEN-001、OPEN-002 | deferred；交给 build-plan，不改变产品语义 |

## 3. 范围、非目标与延期

### 3.1 当前范围

当前任务同时包含：

1. 代表性、风险覆盖型垂直切片；
2. 89 条原始来源的清单、快照、处理、语义建模、页面投影和验收；
3. `Source → Block → Claim → KnowledgeUnit → Relation → PageProjection` 语义链；
4. 问题/场景路由，以及产品、模块、对象、场景、边界五类业务标签；
5. 定位、概念、操作、诊断、经验五类 Reader 页面；
6. Reader 与 Audit 两个分离但可关联的阅读面；
7. 五维、逐 quality case、严格高于 CompanyBrain 的发布闸门；
8. 空源、重复、冲突、媒体、跨源合并和来源未记录异常规则等完整性边界。

### 3.1.1 同任务大范围的最小闸门与失败交接

范围很大，但每一段都有独立的最小成功条件：R1 必须先完成配置、身份、预算、根因对照和无 provider preflight；R2 必须完成 Block/Claim/semantic-frame/typed output 且无 raw fallback；R3 必须从实际 Reader/Audit 与 CompanyBrain snapshot 逐 case 重算五维；R4 必须完成切片、89 条 source closure、Home/Reader/Audit/媒体链接和原子发布证据；M401/M401-R 必须消费这些当前快照绑定的 receipt。任一段失败都要保留失败证据、停止依赖它的后续动作并把最终状态写成 `not_released` 或真实 `blocked/unavailable`；不能删掉未完成的 89 条清单、缩小任务范围、拿旧 receipt 冒充通过或把“有完整失败证据”说成 released。这样同一任务的范围不被拆走，也不会因一段失败而伪造整体成功。

### 3.2 非目标

以下内容明确不属于本任务：

- 复制 CompanyBrain 的业务事实、目录内容或人工偏置。
- 用页面数量、行数、关键词命中、固定模板、平均分、加权总分或测试绿色替代读者质量。
- 补写 89 条原始来源之外的业务事实。
- 把 LLM、向量检索或模型输出本身当成事实证据。
- 建设后台调度、持续同步服务、编辑工作台、权限系统、在线搜索、多语言系统或新的知识库平台。

### 3.3 延期项

- 增量同步与影响分析；
- 几万条规模的性能与生产晋级；
- 外部资料接入与在线搜索；
- 用户反馈闭环和自动本体学习；
- 人工逐页审核工作台；
- 多语言发布。

延期项不能减少当前垂直切片 + 89 条全量范围，也不能改变 `not_released` 的失败语义。

### 3.4 历史结果根因回放合同（R1/M101）

用户原始需求明确要求复查旧方案、旧实现、旧产物，并解释为什么结果比 CompanyBrain 差；这不是可延期的研究旁支，而是本次修复的输入验证和修复依据。R1/M101 必须在任何 LLM、embedding 或 RED 测试前，生成并校验 `task5-root-cause-evidence.v2`：

- 固定读取五类只读对象：旧 Task4 v37-88 交付包、用户实际查看的 V50 candidate bundle、当前 Task5 修复前实现/基线（由 `quality/evidence/task5-repair-baseline-v2.json` 的 commit/tree/context 和 before hash 绑定）、原始 89 条资料与 CompanyBrain 只读基线。输入按 `RC-OLD-TASK4`、`RC-USER-V50`、`RC-CURRENT-BASELINE`、`RC-RAW-89`、`RC-COMPANYBRAIN` 五个稳定 label 记录；主机绝对路径只允许留在 host-only preflight，不得进入 provider packet、公开 Reader、Audit 或结果自由文本。
- 每个输入必须记录 `canonical_ref`、snapshot/tree/manifest digest、读取状态、字节/文件计数和实际 hash；旧研究文档只能作为待核对线索，不能代替读取旧实现或旧产物。
- evidence 至少包含两层可回查行：`observations[]` 记录实际失败事实（`failure_id`、artifact/ref+sha256、relative locator、observed_fact、user_symptom），并且每条 blocking/major observation 必须再绑定 `companybrain_comparison`：旧结果与冻结 CompanyBrain 的 `baseline_ref/sha256`、`quality_case_id`、`projection_key`、五维之一的 `dimension`、差异 locator/hash 和 `comparison_status`。`causal_mapping[]` 逐行绑定“失败事实 → CompanyBrain 配对差异 → 当前合同缺口（`contract_gap_ref`/`gap_kind`）→ 本轮修复（`repair_ref`/owner/status）→ ordinary/comparison evidence refs”。`not_comparable` 必须写具体缺失证据并阻断 promotion，不能只写“没有调用 LLM”“质量差”等结论。
- 必须覆盖本轮已知根因族：语义 provider/embedding 是否绕过、full-source/raw fallback、问题入口与业务页面缺失、乱码/不可读路径、临时目录未交付、静态或未闭合质量证明、89 条来源/空源/重复/审计闭包缺陷。实际读取发现的其他根因必须追加，不能用这份列表遮蔽事实。
- 固定落盘：`quality/evidence/task5/root-cause/attempts/<attempt_id>/root-cause-evidence.json`；通过校验后 promotion 到 `quality/evidence/task5/root-cause/root-cause-evidence.json`。证据 schema、canonical bytes、输入 hashes、CompanyBrain 配对差异和当前 Task5 material/snapshot 必须绑定；缺失、漂移、只读失败、比较不可建立或因果行不完整时，结果为 `blocked`、`calls=0`，不得进入 provider。
- 该证据包可以含 host-only 历史路径，但不能含 raw 正文、完整 prompt/response、凭据或内部 host path 的公开投影。M401 必须重新读取 promoted root-cause evidence，逐行核对旧结果→合同缺口→修复的绑定；不能用 design review clean、绿色测试或旧研究摘要代替。

本节列出的根因在 design 阶段只能作为 `H-###/待验证` 假设，不能直接作为事实或修复完成证明。`D0/root-cause-preflight` 先做两件不同的事：① 对当前 raw/CompanyBrain/基线输入做 provider-free identity 与可回读性检查；② 若五项历史输入都可比较，再运行历史根因回放。V50 缺失时必须保留 `blocked/not_released` 的历史证据，不能把未知写成根因事实；但这不阻塞“只用当前 raw 89 条生成新知识”的候选运行，候选仍必须在五维比较未全部 `KD_WIN` 时保持 `not_released`。

89 条 route 也拆成两层：D0 只生成完整的 source-scope ledger（89 条、空源/重复/状态/快照/单源闭包）；Qwen 负责从当前单源 Claim/Block 生成问题、页面类型和五轴业务路由，之后由 typed-output verifier 逐字段绑定 Claim/frame/locator。原始目录顶层只能作为结构性产品归属，不得作为对象、场景、边界或业务事实的证据；文件名只能作为显示标题候选，不能替代语义字段。87 个普通来源必须逐条尝试 Qwen，route 不确定的来源写 Audit-only，不得静默丢弃，也不得用文件名、目录、整篇原文或模型自报补齐。只有 87/87 的 post-provider semantic route closure、Qwen typed compile、Reader/Audit lineage 和五维严格比较同时通过，才允许 `released`。

当前预检已经确认：冻结的 `RC-USER-V50` canonical ref 当前只能读到 0 个普通文件（只剩空的 `audit/`、`products/` 目录），而输入 manifest 要求 652 个文件/111865500 bytes/snapshot=`e376886d6f6fff114c875908b5cca4fc195311fb4b38848d1bb858c66d7e5895`。这表示原 V50 内容当前不可回查，不表示可以把它当成“空产物”；不得静默换用其他临时候选。由此拆出两个不互相偷换的门：历史根因回放门继续 `blocked`，保留 `provider/embedding calls=0`；只基于当前 raw 89 条和 CompanyBrain 只读快照的候选门，使用当前 raw/source-scope/input identity 重新预检后可以继续，但候选没有完整五维 `KD_WIN`、Reader/Audit、机器证据和 Downloads 结果时必须保持 `not_released`。历史 V50 不得被替换成当前候选，也不得把当前候选冒充历史根因证据。

M401-R 通过后，WorkflowHub 必须由 authenticated adapter 生成唯一的 `quality/evidence/task5/workflowhub-implementation-handoff.json`（schema=`workflowhub-implementation-successor.v1`），再允许 M402 读取。该 handoff 不是 caller 自报状态，必须绑定同一任务的 `mini_task.design` result/attempt/report ref+SHA、`mini_task.implementation` result/attempt/report ref+SHA、两套 contract/semantic hash、当前 snapshot/material/worktree、M401 packet SHA、M401-R promoted receipt SHA、全部 finding dispositions 和 WorkflowHub writer attestation；`review_kind` 固定为 `mini_task.implementation`、`terminal_status=semantic`、`terminal_clean=true`。设计 preflight 的 canonical parent projection 必须同时有独立 `attempt_id`，validation handoff/receipt 必须有并校验对应的 `parent_attempt_id`，不能因 result/attempt 共用路径就视为绑定。缺失、旧 ref、未处置 finding、writer/identity/hash 漂移或 handoff canonical SHA 不符，M402 在读取 raw/CompanyBrain 或发 provider 前 `blocked/calls=0`。

## 4. 产品概念与稳定对象

### 4.1 Source（来源）

一条原始资料及其不可变快照。每条期望来源都必须有稳定 source id、来源相对路径、snapshot id、content hash、读取状态、处理状态和失败原因。空白来源也必须保留清单行和快照记录。

本任务的来源闭包不是“数量等于 89”这么简单，而是一个冻结的 `SourceInventory`。当前原始目录去掉隐藏文件后的事实为：`inventory_version=task5-corpus-v1`、89 条 canonical relative path，路径集合摘要 `7484673e9b5996112916190c57d612a67dcfa3468b870d9fd2c1f51d57cb6a51`；`emm for android /AE - AirViewer厂商管理.md` 的去空白内容为空，其他 88 条期望为 `present`。每次运行必须绑定同一 `inventory_version` 和路径集合；path-only 的 `source_path_key` 由规范化相对路径稳定派生，运行时 `source_id` 只按 §10.3.1a 派生，不能由输入顺序或 `cluster-N` 派生。

`SourceInventory` 每一行至少包含：`source_id`、canonical relative path、期望状态、snapshot id、content hash、字节/行数、读取/处理状态、失败原因和 duplicate/conflict 关系。路径分隔符统一为 `/`，`..`、软链接逃逸、隐藏文件、重复 canonical path 和 inventory 外文件不得静默进入分母：要么被拒绝并进入 Audit，要么让本次运行 `blocked/not_released`。实际快照 hash 与期望状态必须逐行记录；路径清单不变但 hash 变化也必须建立新的运行边界。

本规格不再维护第二份手写 89 条路径执行清单。AC-001 的唯一字节权威是 `config/task5-source-page-manifest-v2.json`（actual SHA-256=`b7d6e3f59c0c6ccc6fd04a059007c7a320fd40e85af1d090686a6a0d8272107f`，canonical=`46d65dc22e3b822efa3dc7c965264378b054556e807620837e4b25e2643ab0b1`）；其 `source_snapshot` 声明 89 条路径/hash/byte/line/locator，`projection_policy.source_not_documented` 明确替换同一 entry 的 source-digest，不增加第二次 source-digest 请求、第二个 Reader 或第二个 coverage row。下面不抄路径。
- `emm for android /AE - GoInsight数据收集.md` — expected: `present`
- `emm for android /AE - 应用定向发布.md` — expected: `present`
- `emm for android /AE - 应用详情.md` — expected: `present`
`source_path_key` 的 path-only 规则是 `sha256("source-path:" + canonical_relative_path)`，只用于路径排序、清单和 duplicate tie-break；它不是运行时 `source_id`。运行时 `source_id` 的唯一规则是 §10.3.1a 的 `provider_visible_source_uri + source_snapshot_id + content_hash` 算法，旧的 path-only `source_id` 规则废止，不得写入 provider-visible、Reader、Audit 或 replay identity。

### 4.2 Block（来源块）

来源中可以独立定位的标题、段落、列表、表格、代码/配置块、图片说明、链接或其他媒体块。Block 必须保留原文结构和 locator；不能为了生成摘要而删除链接目标、图片引用、表格单元或命令含义。

### 4.3 Claim（事实声明）

由一个或多个来源块支持的最小业务事实。Claim 必须记录 owner source/block、content hash、locator、证据状态、适用边界和冲突关系。`extracted` 不等于 `supported`；没有 source block、ownership、hash 或 locator 的 Claim 不能进入正式 Reader。

### 4.3.1 ClaimSemanticFrame（Claim 语义中间层）

每个准备进入 Reader 的 supported Claim 必须先生成 `task5-semantic-frame.v1`：`subject`、`predicate`、`object`、`action`、`order`、`quantity`、`conditions`、`polarity`、`scope` 和各自字段状态。每个 concrete 字段必须带一个或多个可重放的 `support_span`；缺失或不适用字段必须显式写成 `{value: "unknown"|"not_applicable", support_span: [], evidence_state: "unknown"|"not_applicable"}`，不能伪造坐标，也不能满足 Reader 必答字段。它是闭世界结构化事实，不是模型自报标签；Reader 必需字段为 unknown、冲突或无法映射时只能 Audit/blocked。业务化连接词可以由 Qwen 增加，主体、关系、客体、顺序、数量、条件、否定和适用范围不得超出 frame。

### 4.4 KnowledgeUnit（知识单元）

围绕一个业务对象、任务链、场景、故障、边界或经验组织的 Claim 集合。KnowledgeUnit 不是原文件的复制品，必须由通过语义 frame 的 Claim 组成，并能解释 Claim 之间的关系和适用范围。

### 4.5 Relation（关系）

由证据支持的产品、模块、对象、场景、边界、前置条件、依赖、冲突或相关关系。关系必须有来源 Claim；硬编码的“相关”链接不能单独证明业务关系。

### 4.6 RouteRecord（路由记录）

从读者问题/场景到答案页的可回查记录，至少包含：

- 主问题或场景；
- 读者可能使用的同义问法/入口别名；
- 主意图；
- 产品、模块、对象、场景、边界；
- 目标 page type；
- PageProjection id；
- 支持该投影的 Claim ids。

主意图缺失或冲突时为 `UNKNOWN`，不能默认成操作页。通用 `source-digest` 当前固定为“一个非空来源、一次单源请求、一个 primary PageProjection”；静态预检或 Qwen 输出发现多个不可消解的主意图时，记录 `source_digest_ambiguous`，不生成 Reader，不能把多个意图硬拼成一个答案。命中 `source_not_documented` 的 entry 不走 Qwen，而是用其独立合同替换这一个 primary PageProjection。只有 QualityCase（例如 Q-OPR/Q-BND）在自己的冻结合同中允许一个来源拆成多个独立 PageProjection。

### 4.7 PageProjection（页面投影）

把 KnowledgeUnit 和 RouteRecord 编译成 Reader 页面和对应 Audit 记录。页面投影拥有一个主问题、一个主 page type、可读答案、边界和来源入口；内部 id、hash、运行字段只出现在 Audit，不出现在 Reader 正文。

### 4.8 QualityCase 与 GuardCase

- QualityCase：固定一个用户问题/场景、角色、必答 Claim、必答边界、禁止 Claim、原始来源和 CompanyBrain baseline，用于五维严格对照。
- GuardCase：不用于声称 KnowledgeDigest 胜出，但失败会阻断发布，用于验证全量、媒体、重复/冲突、跨源 ownership 和特殊审计。

### 4.9 产品事实与假设（PFACT）

每条 PFACT 只使用一种状态；本规格中的产品事实均为当前任务已确认的产品边界或可回查历史事实，不把实现推断写成产品事实。

- **PFACT-001：期望来源总数为 89 条。**
  - status：`verified`
  - 证据：decision-log `F-003`、D-003/D-011、make-decision 官方阶段结果。
  - 关联：FR-SOURCE-001、FR-FULL-001；AC-001、AC-002、AC-008。
- **PFACT-002：来源结构和媒体可能影响业务含义。**
  - status：`verified`
  - 证据：decision-log `F-005`、G-MEDIA-CLAIM、D-011。
  - 关联：FR-BLOCK-001；AC-003、AC-006。
- **PFACT-003：事实必须沿 Source→Block→Claim→KnowledgeUnit→Relation→PageProjection 回查。**
  - status：`verified`
  - 证据：decision-log D-004、D-011、Q303A 最终确认。
  - 关联：FR-SEMANTIC-001；AC-003、AC-007、AC-010。
- **PFACT-004：问题入口需要 typed route record，不能按标题默认 procedure。**
  - status：`verified`
  - 证据：decision-log `F-007`、G-301、D-014。
  - 关联：FR-ROUTE-001；AC-004、AC-005、AC-011。
- **PFACT-005：Task5 使用五类页面：定位、概念、操作、诊断、经验。**
  - status：`verified`
  - 证据：decision-log G-301、D-014。
  - 关联：FR-PAGE-001；AC-005、AC-011。
- **PFACT-006：Reader 和 Audit 是两个互补的用户面。**
  - status：`verified`
  - 证据：decision-log R-002、D-013/D-014、G-303。
  - 关联：FR-READER-001；AC-004、AC-010、AC-012。
- **PFACT-007：空源、冲突、证据断链和未知不能进入正式 Reader。**
  - status：`verified`
  - 证据：decision-log D-008、D-015、G-302。
  - 关联：FR-STATE-001；AC-007、AC-008、AC-009、AC-013。
- **PFACT-008：垂直切片是当前任务内的强制诊断检查点，不能替代 89 条全量，也不能把切片局部失败伪装成全局失败或通过。**
  - status：`verified`
  - 证据：decision-log D-003、D-010、最终用户确认。
  - 关联：FR-GATE-001；AC-002、AC-013。
- **PFACT-009：五个适用维度必须逐 quality case 为 KD_WIN。**
  - status：`verified`
  - 证据：decision-log R-002、D-009、D-013、六个 quality case 清单。
  - 关联：FR-QUALITY-001；AC-011、AC-012、AC-013。
- **PFACT-010：CompanyBrain baseline 缺失不能声称胜出。**
  - status：`verified`
  - 证据：decision-log D-009、D-013、CompanyBrain baseline inventory。
  - 关联：FR-BASELINE-001、FR-QUALITY-001；AC-011、AC-013。
PFACT-011–018 均为 `verified`：发布失败不破坏旧 Reader；来源指纹变化建立新运行边界；人工摘要不能覆盖 case 失败；89 条来源绑定不可变 canonical path（path-set SHA=`7484673e…`，空白源=`emm for android /AE - AirViewer厂商管理.md`）；QualityCase 是可执行 fixture；CompanyBrain 绑定不可变 baseline snapshot；每个 Reader projection 有 source/Claim/render coverage ledger；运行与 Claim 中间状态可审计。证据分别来自 decision-log D-006/D-008/D-009/D-011/D-013/D-015、G-303、G-MEDIA-CLAIM、G-LINEAGE-MERGE 和对应独立审查；关联 FR/AC 保持原定义。

## 5. 用户入口与完整流程

### 5.1 生成者流程

`make-decision receipt → 声明 89 条来源 → 建立固定清单 → 快照与完整性检查 → 风险切片 → Block 保真 → Claim/KnowledgeUnit/Relation → 页面与路由规划 → 五类页面投影 → Reader/Audit 检查 → 五维对照 → 发布或 not_released`。receipt 必须绑定原始需求、Talk 选择、stage/result/attempt ref+SHA、material revision 和 writer attestation；`mini_task.design`、M401、M402 缺失或漂移即 blocked，不得由 `build-spec` 补需求。

切片是同一任务内的强制诊断检查点，不是试点交付，也不是把全量延期。切片状态必须按 `slice_preflight: pending → passed|blocked`、`slice_execution: pending → running → completed|stopped`、`slice_quality: pending → passed|not_evaluable|failed` 记录；切片复核完成后才允许进入 full，但 `not_evaluable` 或 slice-local `failed` 不阻止 full，只阻止最终 `released`。只有输入/身份/预算/锁、provider transport/auth、取消或发布等 global fatal 才停止 full；所有 slice-local 失败后仍须完成 89 条全量的来源处理和诊断产物。最终质量/完整性失败为 `publication_status=not_released`，并保留 `outcome/reason_code`，不能写成终态 `candidate`。

### 5.2 读者默认流程

`Home → 问题/场景入口 → 产品 → 模块/对象 → 场景/边界 → 业务答案页 → 相关页面 → Reader 证据入口 → Audit 精确来源块`

Reader 入口可以是问题标题、场景标题或明确的业务任务链接；不要求本任务建设通用搜索框。只有产品名而没有问题入口时，读者仍必须能沿产品、模块、对象和场景索引到达至少一个主问题页。

公开导航的机器合同是 Home route table，也是 v1 唯一公开的产品/模块/对象/场景/边界轴索引：不再生成 `modules/`、`boundaries/`、`knowledge/` 或其他独立轴目录。每个 Reader 必须同时有一条 `entry_kind=question` 和一条 `entry_kind=scene`，字段顺序为 `entry_kind → question|entry_scene → product → module → object → scene → boundary → reader_path`。两条 route row 都必须链接到同一 PageProjection，轴值来自该 projection 的 typed semantic ledger；Home 平铺 Reader、缺轴、跳过问题/场景入口、链接目标不一致或任何 Reader 无 route row 都是发布失败。Audit 只记录 route replay 和失败原因，不替代用户入口。

Reader 与 Audit 的回查合同是：每个 Reader render unit 都有稳定、公开的 `audit_ref`，格式为 `audit/<public_projection_slug>/u-<ordinal>`；`ordinal` 按最终渲染顺序从 `0001` 开始。Reader 使用 `Audit.md#<public-anchor>` 相对链接（从 `products/<product>/<page-type>/<readable-title>.md` 为 `../../../Audit.md#...`），不展示内部 ID、hash 或主机路径。`Audit.md` 和 `_audit/audit-pages.json` 按同一 `audit_ref` 映射 Reader path、anchor、source path、snapshot/content hash、Block locator、Claim ownership、状态和失败原因；每个 Reader unit 恰好一条 Audit entry，且 `Reader → audit_ref → source block` replay 全量通过才可发布。

### 5.3 默认成功路径：读者找答案

1. 读者从 Home 或场景入口选择一个问题。
2. 路由记录给出唯一主意图、产品/模块/对象/场景/边界和 page type。
3. Reader 页先给业务答案，再给前置条件、结果、限制或边界。
4. 每个关键事实旁边都有可进入 Audit 的来源入口。
5. Audit 展示 source、snapshot、content hash、block locator、Claim ownership、状态和冲突/缺口。
6. 若答案确实来自当前来源且质量 case 通过，读者无需阅读原始文件堆即可完成任务。

### 5.4 问题不能唯一定位

当一个问题可能对应多个主意图、多个对象或多个边界时，系统不猜最像的页面。Reader 不发布领域答案；Audit 记录候选路由、冲突原因和缺少的判定信息，问题状态为 `blocked` 或 `not_answerable`。

### 5.5 空源、来源失败和权限失败

- 空源：来源仍显示在完整清单中，状态为 `empty`，保留快照和行数/字节数事实，不生成业务答案页。若它与冻结 manifest 的 `expected=empty`、路径、快照 hash、字节/行数和 Audit locator 全部匹配，则记为 `known_empty`：它完成来源闭合，但不进入 Reader，也不单独阻断包级 `released`；任何未声明、隐藏、被误报为非空或证据不完整的空源都按失败处理并阻断发布。
- 来源读取权限不足、格式不支持或处理异常：状态为 `processing_failed` 或 `unsupported`，Audit 显示原因和重试条件，不进入 Reader。
- 输出目录没有写权限或原子发布失败：当前发布事务失败，不留下半套 Reader 导航；已有旧版本不被覆盖，结果为 `failed/not_released`。
- 恢复时只能重新处理同一份稳定快照；若来源指纹已变化，必须建立新运行清单，不把新旧来源混在一次结果中。

### 5.6 重复、冲突和跨源合并

- 相同 content hash：标为 `duplicate` alias，继承 canonical source link，并在 Audit 保留重复来源身份。
- 内容不同但目标相同：先按 Claim 的关系事实判断，不再把相同 `target_key` 直接当成 `conflict`。同一目标下互补的 predicate/object/condition 是 `co_support`，保留每条 Claim 的独立 ownership；同一关系事实出现互斥 polarity、数量、条件范围或动作方向才是 `conflict`。
- 只有在每条 Claim ownership、来源状态和关系结果都明确时，多个来源才能共同支持一个 PageProjection；无法比较的关系是 `unknown`，不能猜成 co-support。
- 冲突、ownership 缺失或合并证据不完整时，Reader 不发布受影响答案。

实现必须使用下面的确定性关系算法，不能由输入顺序或模型自由选择 canonical source：

1. 先对 raw snapshot 的原始字节按 `content_hash` 分组。规范化 canonical relative path 的算法固定为：NFKC、`/` 统一为 `/`、拒绝空段和 `.`/`..` 逃逸、保留文件名大小写，然后按 Unicode code-point 升序比较；相同 hash 的组中选择最小路径，仍相同则按 `source_id` 升序。该项是唯一 `canonical_source_id`，其余来源是 `duplicate alias`。每个来源都保留 `duplicate_group_id`、`canonical_source_id`、`relation_method=raw-hash-v1` 和自己的 Claim/Audit link。
2. 只有 typed semantic compiler 已给出完整且无歧义的 `product|module|object|scene|boundary|page_type` tuple，才计算 `target_key`：各字段先 NFKC、大小写折叠、连续空白折叠、路径分隔符统一，再用 `|` 连接；缺字段或歧义时 relation 是 `unknown`，不能猜成同目标。该关系的 `relation_method=typed-target-v1`。
3. 不同 `content_hash` 且相同 `target_key` 的来源再按 canonical relation tuple 比较：tuple 的 subject/predicate/object/polarity/condition/quantity/action 互补时为 `co_support`，同一事实的 polarity、数量、条件范围或动作方向互斥时才为 `conflict`；不确定时为 `unknown`。`conflict_source_ids` 按规范化路径排序，受影响 PageProjection 为 `blocked/not_released`；不因相似词面合并。
4. 关系结果必须写入 source relation ledger，并由输入 source 顺序的两种置换测试得到同一组 `duplicate_group_id`、`canonical_source_id`、`target_key`、`relation_status`、`co_support_claim_ids` 和 `conflict_source_ids`。关系 unknown、ownership 缺失或 typed tuple 不完整时，只能进入 Audit；不能用 Reader 文本或 embedding 分数补齐关系。

### 5.7 表格、图片、链接和命令

表格、图片引用、来源内链接、代码/配置块和命令属于证据的一部分。Reader 可以选择合适的展示方式，但不能仅保留一段文字而丢掉目标、上下文或操作含义；无法保真的内容进入 Audit 并阻断受影响 quality case。

### 5.8 取消、加载和竞态

- 加载/处理期间：用户能看到当前运行仍在处理，包不能标为 `released`。
- 用户取消或进程中断：已完成的来源和 Audit 诊断可以保留，运行状态记录 `cancelled`，包的终态 `publication_status=not_released`；不得把部分结果当全量完成。
- 快照过程中来源发生变化：若不能得到稳定 hash，当前来源为 `processing_failed/conflict`，本次不发布；下一次从新的固定清单重跑。
- 发布并发或重复触发：单次发布必须原子提交，重复相同输入应得到同一语义结果；不同输入不能覆盖旧版本或伪装成同一运行。

## 6. 页面类型与正文合同

页面类型不是装饰标签，它决定主问题、必答槽位、禁写内容和验收方式。

### 6.1 positioning（定位）

最小必答合同：是什么、服务谁、解决什么问题、与其他产品/能力的区别、边界。不能只写产品名、口号或来源摘要。何时使用、价值/结果等信息只有在来源有证据时才补充，不额外成为所有定位页的放行条件。

### 6.2 concept（概念）

最小必答合同：定义、对象、关系、范围、误用。配置/数据含义在来源有证据时补充；不能把定义页伪装成步骤页。

### 6.3 operation（操作）

最小必答合同：前置条件、步骤、预期结果、验证/回滚/限制。目标、权限、入口、参数、分支、失败和完成条件属于具体 QualityCase 的必答 Claim 或边界时才成为该页的 case 约束；不能在没有来源证据时硬补。不能在缺少前置条件或完成判据时只列动作。

### 6.4 diagnosis（诊断）

普通 diagnosis 的最小必答合同：症状、检查顺序、可能原因、处理动作、升级边界。需要检查的证据和不能判断的边界按来源和 QualityCase 补充；若来源没有异常触发/处理/分支/恢复规则，只能使用受控的 `source_not_documented + not_answerable` 投影，不能推断“系统不存在异常”。

`source-not-documented-status` 是 diagnosis 的独立投影子类型，不套用普通 diagnosis 五阶段。它的固定五段是：`source_scope`（扫描对象/范围）、`scan_coverage`（规则和逐 Block 覆盖）、`zero_match_result`（明确/含糊匹配均为零）、`interpretation_boundary`（只说明资料没有记录，不推断系统状态）、`verification_next_step`（需要系统诊断时补充独立观测/来源）。普通 diagnosis 的 cause/action/escalation 在该子类型中是 `not_applicable`，必须写清“当前资料没有这类证据”，不能编造处理方案；该状态页仍使用 `page_type=diagnosis`，但 `projection_subtype=source-not-documented-status`、`reader_task_path=snd-status-v1`。

### 6.5 experience（经验）

最小必答合同：发生背景、做法/取舍、版本或时间、踩坑/限制、适用边界。影响、教训和回归点在来源有证据时补充；不能把复盘意见改写成普遍规则。

### 6.6 Reader 与 Audit 的分工

- Reader：只显示读者需要的业务答案、必要边界、验证/处理信息和干净的来源入口；不显示内部 id、hash、运行状态字段或原始噪声。
- Audit：显示完整 Claim、source block、locator、hash、ownership、状态、冲突、缺口、规则版本、扫描范围和时间。
- Reader 中的每个渲染单元必须对应一个或多个 Audit Claim，或明确标记为边界/状态单元；Audit 缺证据时 Reader 不能用“看起来合理”的文字补齐。完整覆盖由 `RenderLedger` 约束，不用抽样结果替代。

## 7. 分层状态与状态转换

### 7.0 运行和 Claim 的可观察检查点

运行状态按已确认的顺序推进：`declared → snapshotted → inventoried → modeled → compiled → evidence_checked → route_checked → candidate → released`。`candidate` 只表示运行中检查点；终态为 `blocked`、`failed`、`not_released` 或 `cancelled`，终态 `publication_status` 只能是 `released` 或 `not_released`。取消保留已完成检查点和 Audit，但不能保留终态 candidate。任何状态不得因为“页已经生成”而跳过上游检查点。

Claim 状态按 `extracted → normalized → linked → supported` 推进：`normalized` 只做不改变语义的结构归一化，`linked` 表示已绑定 KnowledgeUnit、Relation、RouteRecord 或 PageProjection，`supported` 表示 source block、ownership、hash、locator、适用边界和冲突检查完整。`extracted`、`normalized` 或 `linked` 都只能进入 Audit，不能独立支持正式 Reader；`conflict/unsupported/ambiguous/empty` 是异常事实，不是成功状态。

### 7.1 来源层

`expected → snapshotted → present`

异常终态：`empty`、`processing_failed`、`unsupported`、`duplicate`、`conflict`。

规则：来源不能从分母消失；相同 hash 的 duplicate 只能作为 alias；不同内容不能标 duplicate；相同 target 只有存在互斥关系事实才标 conflict。

### 7.2 证据层

`extracted → supported`

缺 source block、ownership、hash 或 locator 时为 `lineage_incomplete`。Claim 处于 `extracted` 时只能进入 Audit，不能支持正式 Reader。

### 7.3 问题层

- `answerable`：主意图唯一，必答 Claim 和必答边界齐全，证据可回查。
- `not_answerable`：资料明确不足以回答该问题，例如异常规则未记录。
- `blocked`：冲突、路由歧义、证据断链或发布前质量门未满足。

### 7.4 发布层

- `candidate`：运行中的中间检查点；已生成可诊断的候选产物，但还没有资格作为正式 Reader。
- `not_released`：存在任何发布硬门失败、未知或不完整。
- `released`：只能由 §10.4.2a 的唯一机器化谓词产生；slice/full 状态机完成，允许冻结闭合 SND guard 的预期 `not_evaluable`，但不得有意外 `failed`；不能把“slice 通过”解释成所有 slice projection 都必须可评估。

CLI 必须把发布状态映射为固定退出码，并在结果 JSON 与原始进程结果中同时记录：`released=0`、`not_released=1`、`blocked=2`、`unavailable=2`、`failed=3`、`cancelled=4`。`cancelled=4` 是唯一取消码，即使取消属于 global fatal，也不能改成 `2`；`unavailable` 只能表示 provider/依赖不可用，不能被当作质量通过；任何状态缺少映射、映射漂移或 `unavailable` 返回 0 都是运行失败。

`candidate` 只允许出现在运行未结束的 lifecycle checkpoint；它不是成功终态，也没有独立的成功退出码。运行结束、被中断或发布硬门失败时，`publication_status` 必须唯一归一为 `not_released`，候选文件只能由 `artifact_manifest.kind=candidate` 标识；真实失败类别写入 `outcome/reason_code`（global 的 `blocked|unavailable|overrun|cancelled` 不得被改写成质量失败）。原始进程退出码按 outcome contract 计算，质量/完整性失败为 `1`，global fatal 为 `2` 或取消 `4`；不能返回 `0`，也不能把 `candidate` 当作 `released`。测试必须覆盖“文件已生成但终态不是 candidate”的负例。

`blocked` 与 `unavailable` 共用退出码 `2` 是冻结 provider config 的有意合同：shell 退出码只表示“未成功且需人工/配置处理”，不能单独区分完整性阻断和 provider 不可用。区分两者的唯一权威是当前阶段的 canonical receipt：S0/S1 读取 `task5-preflight-result.v1`，output/staging 已创建后读取 `_audit/run-result.json`；两者都必须有 `publication_status`（或 preflight 对应状态）、`outcome` 和 `reason_code`。调用方必须先读取并校验相应 receipt，缺失、损坏或与退出码不一致时按 `failed=3` 处理，不能把 `unavailable` 当质量通过。

运行结果 JSON 的不可缺失字段是 `publication_status`、`outcome`、`reason_code`、`exit_code` 和 `observed_calls`；`blocked`/`unavailable` 必须分别写自己的 outcome/reason，不能只靠退出码区分。这个规则只适用于已经创建 output/staging 的运行；S0/S1 在创建 output/staging/lock 之前不能写 bundle，因此改写入 `quality/evidence/task5/run-preflight/attempts/<attempt_id>/preflight-result.json`。调用方先按 `task5-preflight-result.v1` 消费该 receipt；进入 output/staging 后再按 `task5-run-result.v1` 消费 `bundle/_audit/run-result.json`。对应 receipt 缺失、损坏、字段缺失或与原始退出码不一致时，按 `failed=3` 处理并保留 failure evidence；这条完整性规则优先于任何质量分或生成文件。

运行级结果的 schema authority 是 `config/task5-run-result-v1.json`（actual SHA-256=`8fea27acc460007fb0ac14ea90e92dfe7580f5bc7f34248d2e3cb5a462096858`，canonical SHA-256=`bbad39d78de3feb29b9a49367caa3187581f32953e53957310dc1904d6395f66`），已创建 output/staging 的运行必须写 `bundle/_audit/run-result.json`。S0/S1 的先行结果由 `config/task5-machine-evidence-contract-v1.json` 中的 `task5-preflight-result.v1` 约束，写入 repository evidence root，不伪造不存在的 bundle。两者独立于逐 projection 的 `task5-quality-result.v3`，必须绑定 raw/CompanyBrain/source/slice identity、provider/config/calibration identity、当前 `mini_task.design` 的 `review_kind/result/report/attempt` ref+SHA、`design_review_contract_id/design_review_contract_hash`、`semantic_hash`、Task5 `runtime_contract_id/runtime_contract_hash/semantic_contract_id/semantic_contract_hash`、`snapshot_tree`、`material_id`、phase 状态、产物 manifest 和失败 evidence path；CLI、测试和 M402 只能读取对应阶段的 canonical receipt 判断运行级状态，不能从 shell exit、quality score 或 provider transport completion 推断成功。canonical bytes 固定为 UTF-8、递归按 Unicode code-point 排序 object keys、保留数组顺序、无空格、`ensure_ascii=false`、禁止 NaN、末尾 LF，`canonical_sha256` 不参与自身 hash。

实现闸门的 RED/GREEN 状态也必须独立：RED 测试只写 `task5-red-test-receipt.v1` 的 `expected_failed` receipt，不能把预期失败写成 gate `failed`，也不能阻断对应 GREEN；GREEN 必须绑定该 RED receipt 的 ref+SHA，只有 GREEN `task5-repair-gate-attempt.v1` 的 failed 才阻断后续 gate。M101 的 baseline preflight 是三步无 provider bootstrap receipt，与 M101 RED 分开。任何实现报告把两类 receipt 混用，都视为设计不一致，不能进入 M401。

所有被发布/安全/评分谓词消费的机器证据统一由 `config/task5-machine-evidence-contract-v1.json`（actual SHA-256=`df96f45ab66aa58c02867834ea1d3f01051fb750a401ce2c71c46d52d0eb01ae`，canonical SHA-256=`2afc28ccabd930d77ddf9278f546b1a81b3d72e6df66b129d00b70406685f882`）冻结：包括 `workflowhub-authenticated-parent-projection.v1`、`task5-preflight-result.v1`、`companybrain-route-snapshot-host.v1`、`companybrain-route-snapshot-public.v1`、`semantic_zero_match_certificate.v1`、`semantic_zero_match_verifier_receipt.v1`、`raw-coordinate-map.v1`、`task5-output-lock.v1`、`task5-directory-manifest.v1`、`task5-failure-evidence.v1`、`task5-run-result.v1`、`task5-root-cause-input-manifest.v1`、`task5-root-cause-evidence.v2` 和 `workflowhub-implementation-successor.v1`。缺字段、绑定/禁止字段不符、host/public 脱敏失败或 hash 漂移即 blocked；不能把 prose 或“文件存在”当作机器证据。

M402 的 surface QA 是真实产物门，不是 M401 的重复或替代：S3 在 Downloads staging 形成唯一 candidate 后，最终写 run-result/发布前，R1-owned QA 必须读取该 candidate 的实际 pre-publish directory manifest/tree digest，按渲染后的 Home、问题/场景入口、Reader、Audit anchor、相对链接、媒体/外链目标、禁字段和 staging cleanup 逐项回放。receipt 写入 `quality/evidence/task5/m402-surface-qa/attempts/<attempt_id>/surface-qa.json`，`bundle/_audit/run-result.json.artifact_manifest.surface_qa` 绑定其 ref+SHA，并同时绑定最终 published directory manifest/tree digest；M401 fake candidate 的 surface receipt 不能满足该条件。surface QA 缺失、只检查文件存在、绑定漂移或 cleanup 失败，最终只能 `not_released`。

本轮四份容易混淆的证据有唯一公开路径和生命周期：`bundle/_audit/raw-coordinate-map.json` 由 S1 Block ledger 写出，供 ClaimSemanticFrame 与 Reader/Audit replay 消费；`bundle/_audit/source-not-documented-zero-match.json` 由 S2 SND analyzer 在 SND Reader promotion 前写出，供 SND gate 消费；`bundle/_audit/source-not-documented-verifier.json` 由独立 deterministic verifier 的通过 promotion 投影，供 SND Reader、M401 finalize、M402 release predicate、directory manifest 和 run-result 消费；`bundle/_audit/run-result.json` 是 output/staging 已安全创建后的唯一运行级 JSON，`Audit.md` 只做人读入口，不能被当成目录。四者都必须进入 `task5-directory-manifest.v1` 的 required paths，并和 `task5-publication-layout-v2.expected_machine_audit_files` 的十一份 machine-evidence 文件精确一致；缺失、额外、未绑定或路径漂移即 blocked/not_released。

### 7.5 优先级

`empty/processing_failed/unsupported > conflict > lineage_incomplete > blocked/not_answerable > supported`

同 hash duplicate 作为 alias，不覆盖 canonical source 状态。上面的 `empty` 优先级只适用于未被 manifest 精确声明并闭合的空源；`known_empty` 仍阻断受影响 PageProjection，但不单独阻断包级 `released`。其他上游高优先级异常都会阻断受影响 PageProjection 和包级 `released`。

### 7.6 source_not_documented 特例

该状态只允许在诊断场景出现，且必须同时满足：

1. 来源快照非空且处理成功；
2. 对整个来源快照的全部 Block、表格、代码/配置块和来源内链接完成固定规则版本的扫描；
3. 固定问题是“是否写明异常触发、处理、分支或恢复规则”；
4. 扫描得到零条明确异常规则 Claim；
5. Audit 记录 source URI、snapshot id、content hash、完整扫描范围、规则版本、运行时间和零匹配清单。

任一扫描不完整、来源为空/失败、映射或归因失败、出现含糊异常描述，都不能触发该特例。Reader 文案只能表达“在 SND-RULE-001 的扫描范围内，当前资料未记录异常触发、处理、分支或恢复规则；这份扫描不能据此判断系统不存在异常”。异常专属问题必须 `not_answerable`，不得跨来源补齐领域 Claim。

固定审计规则版本为 `SND-RULE-001`。它对同一 snapshot 的所有标题、段落、列表、表格单元、代码/配置块、图片说明和链接目标做规范化文本扫描，不调用模型、不跨来源推断；它只支持“在本规则覆盖范围内未发现匹配”的资料状态，不支持系统不存在异常的语义结论：

- `explicit_rule_match`：同一 Block，或明确相邻且属于同一表格行/步骤的 Block，同时出现 trigger marker（`异常|失败|报错|错误|故障|bug|issue|error|fail|unable`）和 action/cause marker（`处理|解决|修复|检查|重试|恢复|升级|原因|排查|fix|retry|recover|escalate|cause|diagnose`），并且该 Block 有稳定 locator；
- `ambiguous_match`：出现 trigger marker 但没有同一语义单元的 action/cause marker，或出现无法归属到 source block 的异常描述；这不是零匹配，禁止触发特殊状态；
- `zero_match`：全部扫描单元既没有 `explicit_rule_match` 也没有 `ambiguous_match`。大小写、空白和全角半角只做固定归一化，不能扩展同义词。

`zero_match` 只是有限 scanner 的结果，不是“没有异常规则”的证明。SND Reader 还必须有逐 Block、100% 覆盖且绑定 hash/locator/snapshot 的 `semantic_zero_match_certificate.v1`；每块有 `no_rule|rule|ambiguous` 和结果 digest。证书通过后必须由独立 deterministic verifier 重新扫描当前 source snapshot，逐 Block 比对分类、hash、locator、coverage 和 result digest，并在 SND Reader promotion、M401 finalize、M402 release predicate 三处留下 verifier receipt。证书与独立复核都通过时也只能生成明确标注 `SND-RULE-001` 扫描范围和局限性的 `not_answerable` 资料状态页，不产生系统行为的负面结论；缺证书、verifier 或任一比对不一致只能 `unknown/Audit-only/not_released`。

`source_not_documented` 的 Audit 记录必须包含 `rule_version=SND-RULE-001`、source URI、snapshot id、content hash、扫描单元总数与完整 locator 范围、`matched_block_refs=[]`、`ambiguous_block_refs=[]`、运行时间、扫描状态、零匹配清单和独立 verifier receipt。缺任一字段、扫描单元数不闭合、列表非空或没有独立复核，都只能是 `unknown/blocked`，不能生成该 Reader 文案。

## 8. 功能需求

### FR-SOURCE-001 来源闭包与快照

系统必须对期望的 89 条来源逐条建立清单和不可变快照，空源、重复、失败和不支持格式也必须有明确状态。来源改变后不能继续使用旧清单悄悄续跑。

来源：R-001、D-003、D-011、PFACT-001、PFACT-014。场景：SCN-002、SCN-003、SCN-009。验收：AC-001、AC-002、AC-014、AC-016。

### FR-BLOCK-001 Block 保真

系统必须保留来源块的结构、定位、表格、图片引用、链接目标、代码/配置和命令语义，使后续 Claim 能回到原始 Block。不能以清洗 URL 或图片为代价制造“干净正文”。

来源：R-001、F-005、D-011、PFACT-002、PFACT-017。场景：SCN-004。验收：AC-003、AC-006、AC-018。

### FR-SEMANTIC-001 Claim 与 KnowledgeUnit 语义链

系统必须按 Source、Block、Claim、ClaimSemanticFrame、KnowledgeUnit、Relation、PageProjection 逐级组织内容。每级都必须保留上游身份；抽取、规范化、frame 解析、来源支持和冲突解决不能共用一个“verified”状态。frame 的 authority 是 `config/task5-semantic-frame-v1.json`；编译器在 Qwen typed JSON 后、Reader 渲染前生成并逐字段回放它。

来源：D-004、D-011、PFACT-003、PFACT-017、PFACT-018。场景：SCN-001、SCN-004、SCN-005。验收：AC-003、AC-007、AC-010、AC-018、AC-019。

### FR-ROUTE-001 路由记录

系统必须从问题/场景生成 RouteRecord，明确主意图、产品、模块、对象、场景、边界、目标 page type、PageProjection 和 Claim。意图不唯一时必须显式 `UNKNOWN/blocked`，不得默认 procedure。

来源：R-002、D-014、PFACT-004、PFACT-015。场景：SCN-001、SCN-005。验收：AC-004、AC-005、AC-011、AC-017。

### FR-PAGE-001 五类页面投影

系统必须支持定位、概念、操作、诊断、经验五类页面，并使每一类满足本规格第 6 节的最小正文合同。页面粒度围绕问题、对象、任务链、边界、故障或经验，不按来源文件直接复制。

来源：R-002、G-301、D-014、PFACT-005、PFACT-015。场景：SCN-001、SCN-006。验收：AC-005、AC-011、AC-017。

### FR-READER-001 Reader/Audit 双投影

系统必须同时生成读者入口和审计入口。Reader 显示答案与边界；Audit 显示完整来源、Claim、状态、冲突和缺口。内部证据字段不得污染 Reader，但 Reader 关键事实不得脱离 Audit。

来源：R-002、D-013、D-014、PFACT-006、PFACT-017。场景：SCN-001、SCN-005、SCN-006。验收：AC-004、AC-010、AC-012、AC-018。

### FR-STATE-001 不确定性分流

系统必须将空源、处理失败、不支持、冲突、lineage incomplete、路由未知和问题不可回答分别记录；这些状态不能被摘要、默认页或免责声明掩盖。只有满足特例的诊断问题才可投影 `source_not_documented`。

来源：D-008、D-015、PFACT-007、PFACT-018。场景：SCN-002、SCN-003、SCN-005、SCN-007。验收：AC-007、AC-008、AC-009、AC-013、AC-019。

### FR-GATE-001 垂直切片闸门

系统必须先用少量端到端场景覆盖已知失败风险：空源/重复/跨源合并、表格/图片/链接、五类页面、冲突/边界、Reader/Audit。切片失败不减少全量范围，但阻断正式 Reader/released。

来源：D-003、D-010、PFACT-008、PFACT-015。场景：SCN-008。验收：AC-002、AC-013、AC-017。

### FR-FULL-001 89 条全量闭包

切片通过或失败后，系统都必须在当前任务继续完成 89 条来源的清单、快照、抽取、lineage、路由、页面候选和 Audit 结果。不能把 88 条可读内容报告为 89 条完成。

来源：D-003、D-010、D-011、PFACT-001、PFACT-014、PFACT-017。场景：SCN-008、SCN-009。验收：AC-001、AC-002、AC-013、AC-016、AC-018。

### FR-QUALITY-001 五维严格对照

系统必须以固定 quality case 为单位，分别评价问题/场景路由、五类业务分类、业务化答案正文、页面类型、Reader/Audit。每个适用维度必须 `KD_WIN`；不能用总分、平均或其他维度抵消。

来源：R-002、D-009、D-013、PFACT-009、PFACT-015。场景：SCN-008。验收：AC-011、AC-012、AC-013、AC-017。

### FR-BASELINE-001 CompanyBrain 基线边界

每个 quality case 必须有真实 CompanyBrain baseline；缺 baseline 记 `CB_MISSING` 并阻断严格胜出。CompanyBrain 只作方法和比较基线，当前业务事实必须回到 89 条原始来源。

来源：D-009、D-013、PFACT-010、PFACT-016。场景：SCN-008。验收：AC-011、AC-013、AC-017。

### FR-PUBLISH-001 原子发布与旧结果保护

只有所有发布硬门通过时才更新 Reader 入口；任何失败、取消、权限错误或竞态都不能留下半套新导航。旧的合法托管结果不因一次失败被删除或伪装更新。

来源：D-006、D-008、D-015、PFACT-011。场景：SCN-003、SCN-007、SCN-009。验收：AC-013、AC-014、AC-015。

### FR-RUN-001 可重复运行与恢复

同一来源清单、URI、hash 和计划重复运行时，结果应可识别为同一语义输入；来源变化时必须新建运行边界。失败重试只能从稳定快照恢复，不能把不同快照的 Claim 拼在一起。

来源：D-011、D-015、PFACT-012、PFACT-018。场景：SCN-003、SCN-009。验收：AC-014、AC-015、AC-019。

### FR-REVIEW-001 人工摘要确认不替代逐 case

系统可以要求人工确认质量汇总是否可读，但该确认不产生 `human_reviewed`，也不能覆盖任一 case 的 `UNKNOWN/INVALID/CB_WIN/TIE` 或 Audit 缺口。

来源：G-303、D-013、PFACT-013。场景：SCN-008。验收：AC-012、AC-013。

## 9. 场景清单

### SCN-001：读者从问题进入业务答案

角色：业务读者。给定一个唯一问题/场景，Reader 必须按路由到达正确产品、模块、对象和页面类型，正文直接回答目标并给出边界和验证信息。路由或证据缺失时转入 SCN-005，而不是显示猜测。

### SCN-002：第 89 条为空

角色：知识维护者。系统必须显示该来源已发现但为空，保留清单和快照，Audit 标明空源；不生成伪造业务页。若该空源与冻结 manifest 的 `expected=empty` 和完整快照/Audit 证据一致，包级可以继续竞争 `released`；若不一致、被隐藏或证据不全，包级不能 `released`。

### SCN-003：来源处理失败或无权限

角色：运行者。系统显示失败原因和可重试边界，保留已经完成的审计事实，不把失败来源从分母移除；重试时指纹变化则新建运行边界。

### SCN-004：媒体和结构证据保留

角色：审查者。给定表格、图片、链接、代码或配置，Audit 能定位对应 Block；Reader 不能因为清洗而丢失影响答案的上下文。

### SCN-005：问题不明确、证据冲突或不可回答

角色：读者/审查者。系统显示明确的不可回答或阻断状态、原因和 Audit 入口；不选择最像来源，不跨源补事实，不默认 procedure。

### SCN-006：不同 page type 的答案

角色：业务读者。定位、概念、操作、诊断和经验页面分别满足各自合同；页面类型错误时该 case 失败，即使正文有若干关键词命中。

### SCN-007：取消、权限错误或发布竞态

角色：运行者/维护者。运行被取消或发布失败时以 `publication_status=not_released` 结束，不覆盖旧 Reader，不留下半套导航；Audit 记录真实 outcome、失败原因和恢复方式。

### SCN-008：垂直切片与五维质量闸门

角色：交付负责人。切片必须覆盖风险类型并完成五维比较；任一适用维度不是 `KD_WIN`，切片或包级发布失败。对可继续的 slice-local 失败，89 条全量仍继续并留下诊断结果；预算、配置、输入漂移、锁和取消等全局致命失败则停止全 run，不能假装 full 已完成。

### SCN-009：89 条全量重跑

角色：运行者。系统按固定 source inventory 和 snapshot 执行全量；同一输入可重复识别，输入变化不混跑，失败可重试且不伪装成功。

## 10. QualityCase 与严格评价合同

### 10.1 五个评价维度

1. **问题/场景路由**：用户能否从问题/场景入口到达正确产品、模块、对象、场景、边界和答案页。
2. **产品/模块/对象/场景/边界分类**：五类标签是否完整、正确、有来源支持且没有错配。
3. **业务化答案正文**：是否直接回答必答 Claim、前置条件、结果、边界和限制，而不是原文堆积或无来源扩写。
4. **页面类型**：是否正确使用定位、概念、操作、诊断、经验，并满足该类型合同。
5. **Reader/Audit**：Reader 是否可见、干净、可用，正文每个关键事实是否能在 Audit 回到 source block、hash 和 locator。

### 10.1.1 五维的原子判定规则

历史 P3 只使用逐维原子 verdict，不使用跨维总分。当前 provider-required v2.2 对每个 case×dimension 记录 `0-100` 诊断分：`content_score` 是 typed semantic support 后的 required atoms，`structure_score` 是实际 Markdown 结构证据，`kd_score` 按 §11.3 的 0.7/0.3 公式计算；分数不能单独证明 Reader 质量。`KD_WIN` 必须满足证据/关系/path/Reader-Audit hard gates、同维 CompanyBrain gap 和逐 atom strict advantage；`kd_score > cb_score` 不是充分条件。相等=`TIE`，缺证据=`UNKNOWN`，baseline 无效=`CB_MISSING`；不跨维补偿，rubric 不预写 verdict/答案。

### 10.1.1.1 Projection×dimension advantage basis

`KD_WIN` 不是 projection 级的可复用标签，而是每个适用的 `projection_key × dimension` 独立裁决。每一条 `KD_WIN` 必须有且只有一条 `advantage_basis`，并同时绑定：同一 projection/dimension 的 `CompanyBrainObservation`、该 observation 的 immutable digest、唯一 `cb_gap_type`（`missing_stage|wrong_relation|unreachable|untyped_contract|missing_taxonomy_axis|unsupported_answer_claim|wrong_page_type|missing_provenance|untraceable_claim`）及可回查 locator、KD 实际补足的 Reader/TaskPath/Claim/Audit evidence refs、可见 surface 集合和 KD evidence digest。一个维度的 CB 缺口不能复用于另一个维度；baseline entry 的共享只允许按其显式 `projection_keys` 做输入复用，不能共享 advantage basis。缺 basis、projection/dimension 不一致、gap 不在该维度、KD completion 不在 Reader 可见 surface、digest 漂移或一条 basis 被多个维度消费，均为 `UNKNOWN`/blocked，不得生成 `KD_WIN`。

严格优势只能逐原子计算：每个冻结 atom 一行，含 applicable、双方 status/evidence 和 relation；gap 必须解释同一 CB gap，strict improvement 至少一项 `CB absent→KD present`，non_regression 排除 regression/unknown/forbidden。缺行、复用、错 gap、CB 已 present 仍报优势均为 UNKNOWN；KD_WIN 还要求必答 atom 全通过且无回退。分母和 atom forms 只来自冻结 rubric。

冻结结果 schema 为 `config/task5-quality-result-v3.json`（SHA-256=`4e41ef9def7c1f08872f6ffc8676a3ebad6ff7425adc4a14b3a41ba362175ef8`，canonical=`2de7c3aa87c6a193f29c941ecf9333ebbd03320a05e35122dff4c65baf34ad80`），其 CompanyBrain observation 子契约为 `config/task5-companybrain-observation-v2.json`（SHA-256=`c075caef3933360522935798f81f728662ad6cc69e7825ec61d1ab814197d313`）。它要求 `dimension_result.advantage_basis` 的 projection/dimension、CB gap、逐原子观察、严格改进引用、非回退标记、KD completion 和 digest 字段，以及 `feasibility_matrix_ref`；实现必须从真实 observation 重算，不能由 case-level `strict_advantage`、总分或静态 rubric 代填。

R3 评分前必须生成完整的 `8 projection × 5 dimension` feasibility matrix；每格按 10.2.2.1 的 dimension→gap mapping 绑定 observation、locator 和 digest。没有真实且匹配的 gap 只能 `UNKNOWN`，使 `quality_cases_proven=false`、发布保持 `not_released`；matrix 是本次 snapshot 的预检，不是预写 verdict。

#### 10.1.2 Reader surface evidence matrix

`required_atom_evidence[*].surfaces` 按维度使用以下冻结矩阵；`audit` 不是业务正文表面：

| 维度 | 必须出现的 Reader 表面 | `audit` 规则 |
| --- | --- | --- |
| 问题/场景路由 | `route` | 禁止用 `audit` 单独支持路由原子 |
| 五轴分类 | `axis` | 禁止用 `audit` 单独支持分类原子 |
| 业务化答案 | `summary`、`slot:<slot>` | 禁止用 `audit` 单独支持正文原子 |
| 页面类型 | `page_type`、`summary`、`slot:<slot>` | 禁止用 `audit` 单独支持类型合同 |
| Reader/Audit | 至少一个可达 Reader 表面 | 允许 `audit`，但只能证明回查/来源可见性 |

对前四个维度，若某个 required atom 的支持集合只有 `audit`，或 Reader 正文没有对应 statement，即使 Audit 有同名 Claim，也必须是 `UNKNOWN`/blocked，不能进入 `KD_WIN`。Reader/Audit 维度可以消费 `audit`，但仍必须先证明问题入口可达、Reader 没有内部字段泄漏，随后再用 Audit 回到 block/hash/locator；Audit-only 不等于 Reader 可用。

#### 10.1.3 ReaderTaskPath semantic hard gate

公开 Reader（`quality-reader`、`source-digest`、SND）都必须有可重放 `ReaderTaskPath`；QualityCase 要求完整五维路径，source-digest 要求同 page-type 的最小 publication path，SND 使用独立的 `snd-status-v1` publication path，不使用普通 diagnosis path。typed 形状固定为 `task_path={contract_id, stages:[{stage_id, order, statement, knowledge_unit_ids, claim_ids, support_spans, surfaces}]}`；每个 stage 必须在 Reader 中由 `KnowledgeUnit` 支撑，并通过真实入口回放、Reader/Audit 配对、closure、ClaimSemanticFrame/lineage、rewrite gate 和无 unsupported/negative/unresolved conflict 硬门。source-digest 用单源，SND 用逐 Block 扫描/零匹配证据；均不进五维。`source-direct-audit` 不生成 Reader/Home，只进 Audit。公开 Reader 任一 gate 失败即 `Audit-only/not_released`，禁 raw fallback；path replay 走真实 route link/正文并检验关系。

| page type | 必须可重放的任务阶段 |
| --- | --- |
| positioning | 识别问题 → 适用用户/范围 → 相邻能力区别 → 边界/选择依据 |
| concept | 术语定义 → 对象与关系 → 适用条件 → 误用边界 |
| operation | 前置条件/权限 → 有序步骤 → 结果/验证 → 失败恢复/限制 |
| diagnosis | 症状 → 检查顺序 → 可能原因/证据 → 处理动作 → 升级边界 |
| experience | 背景/版本 → 做法与取舍 → 教训/踩坑 → 适用范围/限制 |

SND 的 `snd-status-v1` 不属于上表的普通 diagnosis 行，固定顺序为：来源范围 → 扫描覆盖 → 零匹配结果 → 解释边界 → 独立验证下一步；每一段必须回到扫描证书或对应 SourceBlock。SND 的 `cause/action/escalation` 只能以 `not_applicable` 状态出现，不能用空白、模型推断或普通诊断模板替代。

CompanyBrain observation 和 Reader path replay 使用同一组固定 stage-heading aliases，仅用于定位可见候选段落，不直接计分：positioning=`当前结论|产品定位|是什么 / 服务|适用|目标 / 产品线|区别|相邻 / 边界|不能|误区|选择`；concept=`定义|是什么|概念 / 对象|关系|配置项 / 适用|条件|范围 / 误区|不能|不适用`；operation=`前置条件|前提|权限 / 步骤|流程|首先|然后|1. / 结果|完成|验证 / 排查|失败|恢复|限制`；diagnosis=`问题|现象|冲突|症状 / 检查|排查 / 原因|根因 / 处理|修复|建议 / 升级|影响范围`；experience=`背景|版本|Sprint / 做法|取舍 / 教训|踩坑|经验 / 适用|限制`。aliases 只确定 stage 的可见 locator；stage 是否通过仍必须由 typed unit、payload/relation、Reader surface 和 Claim lineage 证明，不能靠 marker 单独放行。

`task_path_status=pass` 的必要条件是：对 `quality-reader` projection，所有适用阶段均有 Reader statement、typed unit、逐 Claim 回查和正确关系；对公开 `source-digest`/SND Reader，必须至少有其冻结 page type 对应的同一 stage contract、完整单源/扫描闭包、入口 route replay 和 Reader/Audit 配对。任一阶段缺失、顺序错误、主体/客体互换、条件扩大/缩窄或只命中泛词即失败。`source-direct-audit` projection 不参加 ReaderTaskPath 判定；若它缺 semantic/lineage/Audit 闭包，只能是 Audit failure/UNKNOWN，不能因没有 ReaderTaskPath 被误报为 quality projection 失败。比较 CompanyBrain 时只对 QualityCase contract 计算五维严格优势；source-digest/SND 只接受 publication hard gate，不用“未进入五维”补成通过。该结果是 evaluator 从实际快照重算的 `path_replay`，不接受 fixture 预写的 verdict。

- **问题/场景路由**：检查是否只有一个主意图、RouteRecord 是否包含产品/模块/对象/场景/边界五轴、是否到达唯一 PageProjection、页面链接是否可走通，并用真实读者可能提出的同义问法复走入口。严格优势断言必须指出 KD 比 CB 多出的可观察路由能力，例如完整五轴、唯一问题入口和同义问法覆盖；不能因为两边都存在一个链接就自动判 `TIE`，但也不能把“多一个链接”当成胜出，必须证明它降低了读者找错页的风险。
- **产品/模块/对象/场景/边界分类**：五类标签逐项检查，标签必须有 Claim 支持且不能互相冲突。KD 只有在五项全对、CB 至少缺一项或存在错配、且 KD 没有新增无证据标签时才 `KD_WIN`。
- **业务化答案正文**：`required_claim_refs` 和 `required_boundary_refs` 必须全部在正文中出现或由明确的结构化答案表达，禁止 Claim 不得出现；每条正文事实都要有 Claim/Block 证据。KD 只有在满足全部必答原子且 CB 至少缺失/错写一个冻结原子时才 `KD_WIN`，不能拿更多字数或更高关键词命中换胜出。
- **页面类型**：`PageProjection.page_type` 必须等于 case 期望类型，并满足第 6 节最小合同；Q-BND 的操作和诊断是两个独立投影，不能以一个混合页代替。这里比较的是“页面是否把读者任务编译成正确的五类正文合同”，不是比较标题上有没有同一个类型词：如果 CompanyBrain 只有未类型化的 reference/overview，不能因其内容叫“字典”就视为已经满足 `concept` 合同；如果两边都是 operation/diagnosis/experience，也必须逐项比较该类型的前置、步骤、结果、验证、失败边界（或症状、检查、原因、动作、升级边界；或背景、取舍、版本、教训、适用边界）。只有候选页的合同原子全部有证据、正文可执行且明显少走错路时才 `KD_WIN`；同名标签本身既不加分也不判平手。
- **Reader/Audit**：Reader 必须可从问题入口到达、正文不泄漏内部字段；每个 RenderLedger 单元都能到 Audit，再到 source block、snapshot、hash、locator。KD 只有在完整回查且 CB 至少缺少一项同等级的可回查证据时才 `KD_WIN`。

若 case manifest、source block、baseline snapshot、适用维度或严格优势断言缺失，结果分别为 `INVALID`、`UNKNOWN` 或 `CB_MISSING`，绝不能推成 `N/A` 或 `KD_WIN`。`N/A` 只在双方都没有该维度的业务含义时使用，并且必须记录理由。

### 10.2 Verdict 与硬门

每个适用维度只能产生：`KD_WIN`、`TIE`、`CB_WIN`、`UNKNOWN`、`INVALID`、`N/A` 或 `CB_MISSING`。

- `KD_WIN`：KnowledgeDigest 在该维度严格优于 CompanyBrain，且证据完整。
- `TIE`：不算通过；严格高于未成立。
- `CB_WIN`：直接阻断对应 case 和发布。
- `UNKNOWN`/`INVALID`：不得进入“通过”分母，且直接阻断发布。
- `N/A`：只有双方在该维度都不适用时可用；不能隐藏缺项。
- `CB_MISSING`：CompanyBrain baseline 缺失，不能声称胜出。

包级成功条件：所有 quality case 的所有适用维度均为 `KD_WIN`，所有 guard case 通过，且没有任何未解决完整性状态。不存在“平均分超过 CompanyBrain”或“多数页面较好即可发布”。

### 10.2.1 CompanyBrain baseline manifest

每个 case 的 baseline 不是一个活路径，而是冻结的 `CompanyBrainBaselineManifest`：`baseline_id`、canonical path、snapshot id、content hash、相关 block/行区间、适用性、读取状态、缺失原因和实际 Reader-Audit `audit_observation`。评估只能读取 manifest 指向的快照；路径存在但 hash 不同视为 baseline 变化，记 `CB_MISSING`，不得继续比较。claim-level Audit 不存在本身不把 CompanyBrain 记零：双方按同一可见 Markdown 表面的 evidence level `none < metadata < source-clue < archive-reference < source-locator < claim-exact` 比较；只有文件缺失、hash 漂移或 applicability 缺失才是 `CB_MISSING`。第 10.3.1 节中的 hash/行区间是当前基线锚点；后续运行仍需把它们复制为不可变 snapshot 事实。

### 10.2.2 CompanyBrain observation replay

路径证据分两层：`root_realpath`/主机路径只进 WorkflowHub host-only evidence；Downloads `bundle/_audit/companybrain-route-snapshot.json` 只保留 root identity、canonical relative path、hash/byte/line、入口和 tree digest。public scanner 命中用户名、绝对路径、staging 或 WorkflowHub 路径即 blocked。

CompanyBrain 的严格优势不能凭 baseline 存在或手写缺口得出。每次先生成 host-only `companybrain-route-snapshot-host.v1`，再投影为 public `companybrain-route-snapshot-public.v1`，最后生成 `companybrain-observation.v2`。host 含 `root_realpath`、完整 regular-Markdown 文件 hash/byte/line、入口和 `tree_digest`；public 含 `snapshot_id`、`host_snapshot_sha256`、root identity、canonical relative files、入口和 tree digest，但 schema 拒绝 `root_realpath`、绝对路径和 host receipt。M401 只保存 host evidence，M402 的 Downloads `bundle/_audit/companybrain-route-snapshot.json` 只保存 public projection；两 schema 分开校验，不能用一个 schema 同时要求和删除主机路径。完整清单变化、软链接逃逸或 digest 漂移在评分前为 `CB_MISSING/blocked`；public、quality result、observation 只引用 host ref/hash/tree digest，不复制 host path。Observation 不含 verdict/score/strict advantage，只含 projection、hash、route/path、page/task/taxonomy/relation/provenance/evidence 观察和 gap。

`root_realpath` 只属于 host-only snapshot；public snapshot 删除该字段及绝对路径。public、quality result、observation 和 M401 只引用 host snapshot 的 ref/hash/tree digest。

#### 10.2.2.1 Dimension-to-gap contract

五维严格优势必须使用与维度匹配的 CompanyBrain 观察，不能把 route 的缺口拿去证明正文或审计维度。每条 `gap_locator` 必须同时带 `dimension`、实际文件 hash、行/段定位、观察字段和 scanner 版本；缺任一字段或映射不唯一就 `UNKNOWN`。

| 维度 | 必须观察的字段 | 允许的 CompanyBrain gap | 缺口含义 |
| --- | --- | --- | --- |
| route | `route_replay_path`、`relation_observations` | `unreachable`、`wrong_relation` | 入口到目标不可达，或入口/关系方向与实际内容冲突 |
| taxonomy | `taxonomy_observations`、`visible_atom_observations`、`relation_observations` | `missing_taxonomy_axis`、`wrong_relation` | 产品/模块/对象/场景/边界任一轴缺失，或轴之间关系错误 |
| business-answer | `stage_observations`、`visible_atom_observations`、`relation_observations` | `missing_stage`、`unsupported_answer_claim`、`wrong_relation` | 类型化答案阶段缺失、正文主张没有可见证据，或答案关系错误 |
| page-type | `observed_page_type`、`stage_observations` | `untyped_contract`、`wrong_page_type` | 页面没有可解析类型合同，或类型与 projection 合同不符 |
| Reader-Audit | `evidence_level`、`provenance_observations` | `missing_provenance`、`untraceable_claim` | 页面没有可见来源线索，或 Reader 主张不能回到精确 source block/hash/locator |

`missing_stage` 只属于 business-answer，`untyped_contract`/`wrong_page_type` 只属于 page-type；`wrong_relation` 的含义由当前 dimension 的观察字段限定。`KD_WIN` 的 basis 只能引用该表允许的 gap，不能用总分、case-level gap、页数或模型自报字段替代。该映射已冻结在 `config/task5-companybrain-observation-v2.json` 和 `config/task5-quality-result-v3.json`；实现、feasibility matrix 和负例测试必须逐项复核。
`gap_atom_mapping` 是运行时可执行的唯一映射：对每个 `projection_key × dimension × gap_type`，CompanyBrain observation 必须提供同一映射的 `mapping_digest`、`atom_ids`、`cb_status=absent`、`evidence_field` 和 locator；atom ID 只能来自该 projection/dimension 的冻结 required atoms，不能从 prose、分数或模型自报字段生成。质量结果的 `gap_atom_refs` 必须与该 observation 的 `atom_ids` 逐项相等，`strict_improvement_refs` 只能引用这些 atom 中实际 `CB absent → KD present` 的行；映射缺失、错维度、错 gap 或 digest 不一致一律 `UNKNOWN`，不得转成 `KD_WIN`。
M401 在 focused/full tests 前由 M401 owner 从真实只读 CompanyBrain 生成 `pre_m402_readiness` snapshot，保存在 `quality/evidence/task5/m401-receipts/attempts/<attempt_id>/companybrain-route-snapshot.json`；固定 `quality/evidence/task5/M401-companybrain-route-snapshot.json` 只作通过 attempt 的 promotion view。M401 packet 的 snapshot ref/role 只证明真实运行前置，不产生质量 verdict；M402 必须重新生成 actual-run 的 `bundle/_audit/companybrain-route-snapshot.json`，quality result 只能绑定 actual-run snapshot，不能复用 M401 文件。

M401-R 的实现审查必须另外留下 `quality/evidence/task5/M401-R-review-receipt.json` 及不可变 attempt 文件 `quality/evidence/task5/m401-r-receipts/attempts/<review_attempt_id>.json`，schema=`task5-m401-r-review-receipt.v1`，schema canonical SHA-256=`74584b624c2c672e6aa4f6d76ca98165f2a06e2fb5c40fca36b39f1807990d1a`；actual 文件 SHA 不作为 frozen schema identity。attempt 文件记录本次 `mini_task.implementation` 的 managed result/report、review outcome、terminal 状态、每条 finding disposition、M401 packet ref/SHA、snapshot tree、material_id、reviewer 和 canonical hash；固定文件只能 promotion 一个 `available + terminal_clean=true` 的 attempt。`needs_human`、`unavailable`、`partial`、non-terminal 或任何未处置 finding 都不能成为 promoted receipt，也不能满足 M402 依赖。M401-R 先读取并校验已经不可变的 M401 packet canonical hash/current snapshot/material，再生成该 receipt；M401 packet 不反向写 M401-R ref/hash。M402/implementation handoff 只接受固定 promotion receipt 的 ref/hash，不接受旧 report、本地测试结果或 transport completion。

回放算法固定如下：

1. **入口/路由**：先校验 `companybrain-route-snapshot-host.v1` 的完整 graph input file set、每个文件 hash 和 tree digest；M402 再校验与之绑定的脱敏 `companybrain-route-snapshot-public.v1`。然后以实际存在的 `gbrain-product-index.md`、各产品 `文档总览.md`、`使用场景索引.md`、`产品定位/产品总览.md`、`产品定位/常见问答入口.md`、`模块手册/模块总览.md` 作为结构入口；解析所有已 hash-bound Markdown 相对链接和 `[[...]]` 链接，按真实相对路径、NFKC、Unicode code-point 顺序建图。只接受能解析到实际文件的边；从入口到 baseline target 取最短 BFS 路径，同长度按路径序；没有路径记 `unreachable`，不能用目录名或文件存在补齐。
2. **页面类型**：只读目标文件的可见 frontmatter `type` 和正文合同；缺失或无法解析记 `untyped_contract`；可解析但与该 projection 期望类型不一致记 `wrong_page_type`。`generated_by`、内部 config 和 `_config` 不算 Reader 正文。
3. **任务阶段**：按 §10.1.3 的固定 page-type contract 在实际 Reader Markdown 中做结构化观察；每个 stage 只有在可见标题/段落包含该阶段的冻结 `atom_forms` 或显式 stage heading，并且有对应行定位时才记 `present`，否则在 business-answer 观察中记 `missing_stage`；page-type 观察不使用该 gap。该观察只描述 CB 当前页面，不预写“KD 应该赢”。
4. **关系与原子**：对同一可见正文运行 `relation-cues-v1`、否定/条件和冻结 `atom_forms` scanner；主体/客体/动作/顺序/数量/条件无法成闭包：在 business-answer 观察中记 `unsupported_answer_claim`，在 taxonomy/route 观察中记 `wrong_relation` 以外的未知状态必须保持 UNKNOWN；发现与 source case 的受支持关系相反才记当前维度允许的 `wrong_relation`。所有观察保存实际 file hash、line locator 和 scanner version；任何 graph 输入文件或 target 文件变化都会改变 observation digest，不能沿用旧缺口。

只有 `CompanyBrainObservation` 按 10.2.2.1 真实记录的、与当前 dimension 匹配的 gap 才能作为严格优势 basis；缺 observation、route snapshot 或 digest 漂移时只能 `UNKNOWN/CB_MISSING`。quality result 绑定 snapshot、observation、path replay 和逐维 basis；测试必须验证 CompanyBrain 输入 mutation 会重算 verdict。

`CompanyBrainObservation` 按 `projection_key` 保存；质量结果的 `advantage_basis` 还必须按 `projection_key × dimension` 一一绑定。单一 observation gap 不能复用于五个维度；缺少对应维度的 CB gap、KD completion 或 digest 时，该维度只能是 `UNKNOWN`，不得由 case-level `strict_advantage` 或总分补成 `KD_WIN`。实现使用 `config/task5-quality-result-v3.json` 的 required contract，测试必须覆盖“一维缺 basis、其他维度有 basis”仍不能发布。

CompanyBrain 的维度级观察使用只读 `config/task5-companybrain-observation-v2.json`：每个适用 projection×dimension 独立 immutable，带 snapshot/tree、文件 hash、route/task/taxonomy/relation/provenance/evidence、单一 mapping 合法的 gap、locator 和 digest；同一 observation/gap/digest 不得跨维复用，缺映射固定 `UNKNOWN`。

### 10.3 固定 quality cases

- `Q-POS-01`：EMM 是什么、服务谁及相邻产品边界；定位页；来源为 EMM 介绍资料；对照 CompanyBrain 的 EMM 产品定位与总览。
- `Q-CON-01`：Android 通信/网络配置项及对象关系；概念页；来源为通信网络配置和设备配置注释资料；对照 CompanyBrain 的 Android 安全通信网络配置字典。
- `Q-OPR-01`：二维码或 Zero Touch 设备入网的前置条件、步骤、结果和验证；操作页；来源为二维码注册和零接触流程资料；对照 CompanyBrain 的设备入网页。
- `Q-DIA-01`：GoInsight 异常/缺陷的现象、定位、原因、处理和升级；诊断页；来源为 v2 fixture 冻结的七个 GoInsight 文档；对照 CompanyBrain 的异常逻辑、图表冲突、缺陷趋势与根因页。
- `Q-EXP-01`：版本、迭代和复盘中的做法、坑、取舍和限制；经验页；来源为 Sprint 复盘和智能搭建资料；对照 CompanyBrain 的踩坑总览和版本演进页。
- `Q-BND-01`：商户角色、终端和规范的分工与操作边界；需要操作/诊断两个关联投影；来源为角色管理、商户规范和终端激活停用资料；对照 CompanyBrain 的 MAXSTORE 产品边界与角色权限页。

#### 10.3.1 QualityCase manifest

每个 case 必须以以下不可变字段落盘：`case_id`、用户角色、主问题、`product/module/object/scene/boundary` 五轴、一个或多个独立 PageProjection、期望 page type、`required_claim_refs`、`required_boundary_refs`、`forbidden_claim_refs`、精确 `source_block_refs`、CompanyBrain baseline manifest、适用维度、不预置结果的 `comparison_rubric` 和切片风险标签。`comparison_rubric` 只声明必答原子、CB/KD 对照方法和什么证据才算严格优势，不得包含 `expected_verdict`、`strict_advantage=true`、答案正文或 slot body。v2 fixture 中的 `Q-...::claim::NNN` 明确是 case-local `case_claim_ref`，不是运行时 Claim ID；loader 必须用同一对象的唯一 `source_block_refs` 解析出本节定义的 canonical Claim ID。解析表必须写入 Audit/quality evidence，且要求 source path、行区间、block hash、content hash 和 scope 全部一致；provider 输出的 `claim_ids` 只能使用 canonical Claim ID，evaluator 读取 fixture 时先通过该表转换 `case_claim_ref`。字段缺失、映射不唯一、canonical ID 与 case ref 对不上或两个投影共用一个身份时，case 为 `INVALID`。

#### 10.3.1a Provider-visible source URI and canonical Claim ID

这是唯一的运行时身份算法；不得把主机绝对路径、临时目录、输入顺序或 `raw://` 别名带入 provider、Reader、Audit 或 replay identity。先将 `canonical_relative_path` 做 NFKC、把 `\\` 统一为 `/`、拒绝空段和 `.`/`..` 逃逸、保留大小写；`provider_visible_source_uri = "kd://source/" + pct_encode_utf8(canonical_relative_path)`，`pct_encode_utf8` 只保留 RFC3986 unreserved 字符 `[A-Za-z0-9._~-]`，其余 UTF-8 字节用大写 `%HH` 编码。`source_id = "src-" + SHA256(canonical_json({schema:"task5-source-id.v1",provider_visible_source_uri,source_snapshot_id,content_hash}) + LF)`；`block_id = "blk-" + SHA256(canonical_json({schema:"task5-block-id.v1",source_id,raw_start_byte,raw_end_byte,block_content_hash}) + LF)`；`claim_id = "clm-" + SHA256(canonical_json({schema:"task5-claim-id.v1",provider_visible_source_uri,source_id,block_id,claim_key,raw_start_byte,raw_end_byte,claim_content_hash}) + LF)`。JSON 使用 UTF-8、递归 Unicode code-point 排序、无空格、禁止 NaN、末尾单 LF；所有哈希使用完整 64 位十六进制。`claim_key` 必须来自冻结 source block ref 的稳定键；相同输入字节与快照身份必须得到相同 URI/source_id/block_id/claim_id，路径重排、内容或快照变化必须得到新身份。host-only evidence 可以另外保存受控相对路径，但不得把它冒充 provider-visible URI；任何旧格式 ID、主机路径或 `raw://` 进入 provider-visible 字段均为 `SOURCE_IDENTITY_LEAK`，首个 provider call 前 blocked。

#### 10.3.1b Source→Block→Claim 生产合同

最上游证据生产只允许使用 `config/task5-source-block-claim-contract-v1.json`（actual=`02898de0…`，canonical=`4baa6760…`）。`task5-block-parser-v1` 冻结 raw byte 顺序下的 heading/paragraph/list/quote/table-cell/code/config/image-caption/link-target 边界、raw 坐标和完整覆盖；代码/配置不按标点拆，表格按 cell，列表按 item。每个 Block 恰好一个 `EvidenceClaim`，Claim 只是 raw evidence pointer；id、owner、span、hash、state 和 conflict refs 按合同生成。缺块/重叠/坐标漂移/重复或越界 Claim/coverage gap 在 provider 前 blocked；snapshot/source/block/claim identity 贯穿 provider、Reader、Audit、replay，public Audit 只投影 hash/relative locator。

关系与 ReaderTaskPath 只允许使用 `config/task5-reader-path-relation-contract-v1.json`（actual=`c3f12166…`，canonical=`16de1b3c…`）。它冻结 `relation-parser-v1` 的 Unicode offset、protected token、否定/条件/关系 cue 优先级、ambiguity→unknown 和 receipt 字段，并冻结五类页面的有序 stages、heading aliases、可见 Reader stage 规则及负例；同时冻结 `route-descriptor.v1` 的 title/question/page_type 字段级 support refs、当前 Block/Claim 或 authenticated CompanyBrain observation 的 closure 重算、cross-source/stale locator 拒绝和 embedding 前 unknown 规则。canonical hash 由 loader 按文件 canonical bytes 派生，不回写配置；parser/path actual、canonical 和 derived hash 必须进入 runtime、request、replay、R2 receipt、PageProjection 和 M401 identity；cue、alias、stage order、page type、descriptor support 或 ambiguity 变更必须 blocked 并重算 identity。

#### 10.3.2 v2 authority、Audit 表面和 projection closure

2026-08-25 contract revision: answer-critical Claim refs are `Reader.body+Audit`; source-detail and archive-only refs are `Audit`, so Reader need not copy every low-level Claim while Audit remains complete. Q-CON-01 claims 014/015 point to raw VPN/global-proxy blocks, Q-POS core-entry detail is Audit-only, and malformed heading/image-only refs in Q-POS/Q-OPR/Q-DIA/Q-BND were corrected. The runtime-bound quality fixture SHA-256 is `8d2a5024bce31bd48709d363bbf8cf578b18b46be732f58e4bd133f881c32f67`.

`config/task5-quality-cases-v2.json` 是 provider-required evaluator 的唯一可执行 authority，当前实际文件 SHA-256 为 `8d2a5024bce31bd48709d363bbf8cf578b18b46be732f58e4bd133f881c32f67`。本节上方六个 case 的文字只用于读者理解；旧 §10.3 描述、`config/task5-quality-cases-v1.json` 和旧答案模板都是历史资料，代码、质量门和真实运行不得读取它们来补 atoms、markers、source paths、claims、boundaries、projection 或 baseline。五项质量维度的语义合同同样冻结在该文件的 `semantic_contracts`，运行时必须从实际字节读取 route、五轴、业务答案 stage、page type 和 Reader/Audit 要求。

以 `Q-DIA-01` 为例，运行时必须从 v2 文件读取完整 source paths：`GoInsight/GoInsight V2.2.0 bug analysis.md`、`GoInsight/指标详情页.md`、`GoInsight/迁移任务列表.md`、`GoInsight/16 问数自动识别数据集.md`、`GoInsight/智能删除图表.md`、`GoInsight/智能查询文档.md`、`GoInsight/17  智能搭建.md`；不能按旧 §10.3 的两份资料自行缩短闭包。所有 case 的 `source_block_refs`、`required_claim_refs`、`required_boundary_refs`、`applicable_dimensions` 和 projection mapping 同样只能从 v2 字节恢复。每个 `required_claim_refs[*].claim_ref` 都必须经过 §10.3.1 的 case-local→canonical mapping；投影里的字符串引用只允许引用已解析的 canonical ID，不能把 `Q-...::claim::NNN` 直接当作 source Claim。

`GENERATED_BY`/`generated_by` 是内部运行元数据，只能出现在 Audit 的 `generated_by` 字段、Audit ledger 或 Audit rubric 的 `audit_only_atoms/audit_only_structure_markers` 中；它不得出现在 `Reader.body`，也不得成为 Reader-Audit 的 required atom。每个 projection 的 `required_boundary_refs` 必须使用独立的 projection id、source block refs 和 `scope=<projection_id>:projection-closure`；case 级 boundary 不能跨 projection 充当证据。两个 Q-OPR projection 的 `page_type` 都是 `operation`，分别用 subtype 绑定二维码和 Zero Touch 来源边界。

#### 10.3.3 Frozen slice fixture

`config/task5-slice-cases-v1.json` 是垂直切片的唯一输入，schema=`task5-slice-cases.v1`，实际文件 SHA-256=`4ebccc3d151dd805ed27f1394bff49298e3fdf7b9f3d813f089f5eb30efb96ef`。它固定 11 个 case、13 个风险标签和 14 个去重后的 source descriptors；14 个 descriptor 由 `cases[*].source_paths` 按首次出现顺序去重得到，其中 `G-EMPTY-89` 是空源，13 个非空 descriptor 中有 1 个 `source-not-documented` replacement，不发 Qwen source-digest，因此切片实际 source-digest LLM 调用为 12 次。首个 provider 请求前必须校验 schema、case id、source path 集合、risk tags、文件 hash 和 `Q-*`/`G-*` 责任边界；空源只保留 inventory/Audit，不发 source-digest LLM 或 embedding 请求；实现不能从代码、旧 fixture 或输入顺序临时选择切片。切片质量投影仍从 v2 QualityCase 的 projection contract 派生，切片失败不缩小 89 条全量。

#### 10.3.4 Slice/full closure mode

切片和全量使用同一套 evaluator 代码，但不是同一个证据闭包，也不是同一种发布结论：

- `full` 是质量与发布的唯一权威模式。每个 case 必须消费 v2 QualityCase 的完整 `source_paths`、source block/Claim、boundary refs 和八个 projection closure；缺少任一必需来源、原子证据或闭包字段即 `UNKNOWN`/blocked，不能发布。
- `slice` 是冻结切片的诊断模式。对每个 case，`slice_required_source_paths` 必须精确等于 slice fixture 的 `source_paths`；`full_required_source_paths` 仍从 v2 QualityCase 读取。实现计算 `missing_full_source_paths = full_required_source_paths - slice_required_source_paths`，不能把不在切片中的来源静默当成“没有证据”。
- slice evaluator 接收显式 `evaluation_mode="slice"` 和闭包差异。若某个必答 atom 或 projection 需要 `missing_full_source_paths`，其状态必须写成 `source_not_in_slice`，该 projection 的 `slice_quality_status="not_evaluable"`；它不进入严格胜出分母，不产生 `KD_WIN`，也不能合并进 full verdict。若一个 projection 的全部必需来源都在 slice 中，才按正常五维硬门评估。
- slice hard gate 仍必须通过 source descriptor、route/vector、semantic lineage、Audit/Reader 绑定、重复/冲突和原子发布检查。由冻结闭包差异明确预期的 `not_evaluable` 不算 slice 失败；意外缺失、隐藏、hash/行数不匹配、未声明来源或错误地把缺失来源当成完整闭包，才算失败，并使 full 终态为 `publication_status=not_released`。
- `Q-DIA-01` 是强制负例：full 必须使用七个 GoInsight 来源；slice fixture 只提供 `GoInsight/GoInsight V2.2.0 bug analysis.md` 和 `GoInsight/17  智能搭建.md` 两个来源，因此 slice 对依赖其余五个来源的必答原子必须显式为 `source_not_in_slice/not_evaluable`，但仍执行路由、语义、Audit 和冲突风险检查；只有 full 七来源闭合后才可评分和发布。
- slice 质量 evidence 必须记录 `evaluation_mode`、full/slice required refs、`available_source_paths`、`missing_full_source_paths`、每个 projection 的 `slice_quality_status` 和不可评估原因；slice evidence 不能冒充或覆盖 full evidence。不得修改 slice fixture，也不得为了让 slice 可评估而增加来源。

切片和 full 的状态机必须显式分层，不能用一个 `status` 字段推断另一个阶段是否通过：

```text
slice_preflight: pending → passed | blocked
slice_execution: pending → running → completed | stopped
slice_quality: pending → passed | not_evaluable | failed
full_execution: pending → running → completed | failed | stopped
```

`slice_quality` 是聚合字段，不替代 projection 级 `slice_quality_status`。先保留每个 projection 的状态和 reason refs，再按固定优先级计算：global fatal 不写成 quality 状态而停止 full；任一意外 slice-local `failed` 聚合为 `failed`；无 local failure 但存在冻结闭包差异的 `not_evaluable` 聚合为 `not_evaluable`；否则为 `passed`。因此同一切片同时有预期 `source_not_in_slice` 和意外失败时，聚合值必为 `failed`，但两类证据都保留；full 可按固定清单继续，released 仍被 failed 阻断。

preflight/身份/预算/锁、transport/auth 或取消会阻止/停止 full；slice `not_evaluable` 只来自冻结闭包差异，SND 还必须有完整 guard+zero-match certificate，缺证书是 unknown/Audit-only/not_released。slice-local failed 留 receipt 后继续 full，但最终 not_released。released 必须同时满足 slice 无意外失败、full closure 完整、全量质量/guard/发布硬门通过；任意 global fatal/unknown 阻断。

#### 10.3.5 Slice/full failure priority

“slice 失败仍跑 full”只适用于不破坏全局输入、provider 身份和输出安全的 slice-local 失败；请求级错误按固定矩阵归类，调用方不能临时改类：

| 失败类 | 例子 | 后续动作 | 结果/退出码 |
| --- | --- | --- | --- |
| global identity/preflight | 缺 config/key、endpoint/calibration/input 漂移、预算、锁/发布失败 | 不启动或立即停止 slice/full | `blocked|overrun` / `2` |
| transport/auth | timeout、connection/TLS、401/403/429/5xx、partial embedding | 不继续 full，标记未启动/停止 | `unavailable` / `2` |
| source-local contract | 2xx 坏 JSON、schema/field/route mismatch、overflow、lineage/relation/raw-copy | 当前 source/projection blocked，继续固定清单 | mode `failed`；最终 `not_released` / `1` |
| expected state | `known_empty`、`source_not_in_slice/not_evaluable` | 按闭包合同继续 | diagnostic；由 full 决定 |
| cancel | user_cancel、sigterm、deadline_cancel | 停止所有后续请求，不继续 full | `cancelled` / `4` |

“继续”表示不重试当前请求、不跨 mode 复用 receipt，只处理固定清单的后续请求。每条错误写入 class、reason、request identity、evaluation mode、observed_calls、continue decision 和原始退出码；2xx contract/semantic rejection 保存失败响应 hash（不保存 secret），不生成 Reader；transport/auth、校准、预算、identity 和取消不能伪装成 source-local。full/slice 的请求、receipt、status 分开；global fatal 写 `full_status=not_started|stopped`，slice-local failure 必须保留且不能被 full 结果覆盖。

- v2 authority 固定六个 case 和投影，不在本节复制答案或 baseline 细节：`Q-POS-01.positioning`（EMM 定位/边界）、`Q-CON-01.concept`（Android 通信网络配置）、`Q-OPR-01.qr.operation` 与 `Q-OPR-01.zero-touch.operation`（两条入网流程，均 `operation`）、`Q-DIA-01.diagnosis`（GoInsight 诊断）、`Q-EXP-01.experience`（版本/复盘经验）、`Q-BND-01.operation` 与 `Q-BND-01.diagnosis`（角色/终端操作与诊断）。每个 projection 的五轴、required/forbidden Claim、source blocks、baseline locator、切片风险和五维适用性只能从 `config/task5-quality-cases-v2.json` 字节读取；本节不预置 verdict，不能缩短 Q-DIA-01 的 full 七源闭包。

所有 case 的 `applicable_dimensions` 和 `comparison_rubric` 必须逐维落盘；当前六个 case 均适用五维。若未来事实证明某维双方都不适用，必须在 manifest 留下双方不适用的证据和理由，不能临时扩大 `N/A`。

### 10.4 固定 guard cases

- `G-EMPTY-89`：空白的第 89 条来源必须被发现并记录；与冻结 snapshot 精确闭合时只进入 Audit/coverage，不单独阻断包级发布；隐藏、误报非空或闭合证据不匹配时才阻断发布。
- `G-DUP-CONFLICT`：重复和不同内容冲突不能被错误合并或删除。
- `G-MEDIA-CLAIM`：图片、表格、链接、代码/配置和命令的 Claim 不能丢失。
- `G-LINEAGE-MERGE`：跨源合并后每条 Claim ownership 和 locator 仍可回查。
- `G-SOURCE-ND`：`source_not_documented` 只在完整、确定性、零明确异常规则扫描且语义零匹配证书闭合后触发 Reader；只有扫描零命中而无证书时，保留 guard Audit，不触发 Reader。

### 10.4.1 GuardCase manifest

GuardCase 也必须有固定输入和发布影响，不能只写名字：

- `G-EMPTY-89`：source=`emm for android /AE - AirViewer厂商管理.md`，判定=去空白内容为空但 inventory 行存在，且与冻结 manifest 的 `expected=empty`、hash、字节/行数和 Audit locator 一致；失败=消失、被当成 N/A、被误报为非空或生成业务 Claim；匹配时影响=`known_empty`、仅 Audit/coverage，不能生成 Reader，不能单独阻断包级发布；不匹配时影响=`not_released`。
- `G-DUP-CONFLICT`：source pair=`merchant system/Dashboard_MerchantPortal.md` 与 `merchant system/Dashboard_ResellerPortal.md`，分别保留 source/block/Claim ownership；相同 hash 才能 alias，不同内容先做 Claim-level relation 判断，互补则 `co_support`，互斥才 `conflict`；失败=自动选一边、覆盖或删除；影响=冲突时受影响 PageProjection blocked，包 `not_released`。该 pair 与冻结 slice fixture v1 完全一致，spec/plan/tasks 不得另选来源。
- `G-MEDIA-CLAIM`：source blocks=`emm for android /AE-通信和网络配置.md#L64-L105` 的表格、`零接触相关流程.md#L127-L134` 的媒体/链接；每个 table/media/link/command 都进入 RenderLedger；失败=静默删除、改掉目标或无 owner；影响=受影响 quality case 和包 `not_released`。
- `G-LINEAGE-MERGE`：source pair=`emm for android /AE-通信和网络配置.md` 与 `全管理相关设备配置项注释更动.md`；每个跨源 KnowledgeUnit 记录 contributing Claim、owner、locator 和冲突关系；失败=同 heading/位置覆盖或只剩页面级来源；影响=受影响 Reader blocked。
- `G-SOURCE-ND`：完整扫描零明确/含糊匹配且证书闭合才允许独立 `source-not-documented-status` Reader；缺证书只留 guard Audit/not_released。Reader 文案只能说资料记录状态，不能说系统没有异常；证书完整时 projection=`not_evaluable`，不单独阻断 package release。该 Reader 使用 `snd-status-v1` 五段和逐 Block 证据，不要求普通 diagnosis 的原因/处理/升级事实。

`source_not_documented` 使用 `config/task5-source-not-documented-contract-v2.json`（actual=`762f09595fe33d33531dd373cb0bf4f3cf1ee468442d0ebccb68314af7534fa5`、canonical=`253de24de01625c4fa14c5bfab57e81c3ef56dbbd6319fd89f4150152b4263fc`）。完整扫描先进入 guard；证书闭合后还必须由独立 deterministic verifier 按冻结的 `semantic-zero-match-verifier-receipt.v1` 合同，对当前 source snapshot 逐 Block 重算并比对，receipt 只能由通过 attempt promotion，且在 SND Reader promotion、M401 finalize、M402 release predicate 三处复核；二者都闭合才生成唯一 `diagnosis` / `source-not-documented-status` Reader/Home/Audit projection，使用 `snd-status-v1` 而非普通 diagnosis path，缺证书或 verifier=`unknown/Audit-only/not_released`。它不进 8-case 五维分母、不产生 KD_WIN；证书、独立复核、guard 和其他硬门全通过才可 release。

### 10.4.2 全量 coverage ledger

六个 QualityCase 不能替代 89 条覆盖闭包：每条 inventory entry 恰有一行 `CoverageLedger`，绑定 source→Block→Claim→KnowledgeUnit→PageProjection→coverage class。普通非空来源走 source-digest；SND replacement 只有扫描+证书闭合才进 Home/Reader，否则 Audit-only；失败、冲突或 lineage 不完整不得回退原文。known_empty 只 Audit；source-direct-audit 只 Audit；未声明/无 coverage row 或其他 present 缺 Reader 都阻断 release。

垂直切片的风险覆盖必须显式闭合：`source-closure/empty` 由 `G-EMPTY-89` 和 AC-001/008 覆盖，`route/type/boundary` 由 Q-POS/Q-CON/Q-OPR/Q-BND 覆盖，`media/structure` 由 Q-CON/Q-OPR 和 G-MEDIA-CLAIM 覆盖，`duplicate/conflict` 由 G-DUP-CONFLICT 覆盖，`cross-source lineage` 由 Q-CON 和 G-LINEAGE-MERGE 覆盖，`diagnosis/source_not_documented` 由 Q-DIA/G-SOURCE-ND 覆盖，五维严格对照由六个 QualityCase 覆盖。任何风险族没有对应 case、source block、失败 oracle 和发布影响时，切片为 `blocked`。

#### 10.4.2a 包级 released 唯一谓词

`released` 唯一谓词：89 entries/89 CoverageLedger 闭合；87 个普通 present 各有完整 source-digest Reader；SND 有完整扫描+证书并生成符合 `snd-status-v1` 的 `not_evaluable` diagnosis-status Reader；known_empty 精确 Audit-only；无其他 canonical present 缺 Reader、blocked、冲突、source-direct-audit 或未闭合 lineage/replay；slice/full、六 case 五维 `KD_WIN`、guard、敏感扫描、下载布局、M402 actual surface QA 和原子发布门全通过。`duplicate_alias` 是唯一例外：只有 alias 自己有 89-row CoverageLedger、Claim/Audit/link 闭包，`canonical_source_id`、canonical hash 和 alias→canonical Reader link 全部匹配，且明确 `closed=true` 时，才视为已闭合的 present alias；它不得生成第二个 Reader。alias 缺证据、未闭合或 canonical 绑定不匹配时同样阻断。任一 false/unknown 即 `not_released`，页数/平均分不能放行。

### 10.4.3 Reader RenderLedger

每个 PageProjection 必须有完整 `RenderLedger`。每行至少记录 `render_unit_id`、Reader page/projection id、单元类型（claim、boundary、table、media、link、command、status 或 omitted）、source block refs、Claim refs、转换动作（`preserved`、`normalized`、`summarized`、`linked`、`audit_only`、`blocked`）和原因。

- Reader 的每个句子、段落、表格、图片/链接说明、命令和状态提示都是一个 render unit；claim/boundary/status 单元必须能回到 Audit，Audit 再回到 source block、snapshot、hash 和 locator。
- `preserved/normalized/summarized/linked` 必须有 Claim refs；`audit_only/blocked` 必须说明为什么不进入 Reader。任何 source block、媒体或 Claim 没有 ledger 处置都算 `unexplained_unit`，包不能 `released`。
- RenderLedger 是全量不变量，不以“关键句抽查”或页面数量统计替代；人工走读只能补充可读性证据，不能覆盖 ledger 缺口。

## 11. 验收标准

每条 AC 都必须使用真实生成结果或真实用户可见入口验证；单纯存在字段、通过单元测试或页面数量统计不算满足。

- **AC-001**：89 条来源闭包
- **AC-002**：切片先行且失败不缩小全量
- **AC-003**：逐级 lineage
- **AC-004**：问题入口可达
- **AC-005**：五类 page type 合同
- **AC-006**：结构和媒体保真
- **AC-007**：冲突和重复分流
- **AC-008**：空源显式处理
- **AC-009**：source_not_documented 受控
- **AC-010**：Reader/Audit 一一可回查
- **AC-011**：逐 case 五维严格胜出
- **AC-012**：人工摘要不掩盖逐 case 失败
- **AC-013**：发布硬门和原子性
- **AC-014**：重复运行和恢复
- **AC-015**：失败事实不伪装成功
- **AC-016**：canonical source inventory 身份
- **AC-017**：QualityCase 与 CompanyBrain baseline 夹具
- **AC-018**：全量 coverage 与 render ledger
- **AC-019**：运行/Claim 检查点和特殊审计
- **AC-020**：旧方案/旧实现/旧产物根因证据链完整，且 M401 能回放“旧结果观察事实→CompanyBrain 配对差异（case/projection/dimension）→合同缺口→本轮修复”；缺输入、snapshot/hash、locator、配对差异、因果映射或 promotion 时，在首个 provider 请求前 `blocked/calls=0`。
- **AC-021**：实际质量结果只有一个 canonical artifact；六 case、八 projection、五 dimension 的逐项结果、证据 refs/SHAs 和最终 candidate/published tree 必须闭合，run-result、release predicate、surface QA 和 manifest 只消费同一 ref+SHA。

### AC-001：89 条来源闭包

- 方法：对照固定 `SourceInventory`、路径集合摘要和运行审计。
验证：恰好 89 个 canonical path 与本规格清单一致，source id 可由路径稳定重算；每条都有 snapshot/hash 和终态，空源也在清单中，inventory 外文件没有静默进入分母。
- 失败条件：数量少于/多于 89、路径集合摘要不一致、空源消失、额外文件混入、路径漂移或失败来源没有原因。
- 证据类型：source inventory、snapshot manifest、Audit 记录。
- 影响状态：SCN-002、SCN-009；失败为 `not_released`。

### AC-002：切片先行且失败不缩小全量

- 方法：验证 QualityCase/GuardCase manifest、切片风险矩阵和切片/全量运行关系。
验证：切片覆盖五类页面、完整性、冲突、媒体和 Reader/Audit，并绑定 source block/Claim/baseline；切片失败时全量仍处理但包不发布。
- 失败条件：切片只挑简单文件、切片失败跳过全量或切片失败仍 `released`。
- 证据类型：slice case manifest、运行状态、包发布结论。
- 影响状态：SCN-008、SCN-009。

### AC-003：逐级 lineage

- 方法：联合检查 CoverageLedger、Claim lineage 和 RenderLedger。
验证：每个进入 Reader 的 supported Claim 和每个 Reader render unit 都能回到 source block、snapshot、hash、locator 和 owner；每个 render unit 都有唯一公开 `audit_ref`，可从 Reader link 回放到 Audit entry 再到 source block；跨源合并的所有 contributing Claim 都保留。
- 失败条件：只有主题/摘要、Claim 无 block、RenderLedger 有 unexplained unit、跨源合并后 owner 丢失或只保留页面级来源。
- 证据类型：Claim/Audit 回查记录。
- 影响状态：SCN-001、SCN-004、SCN-005。

### AC-004：问题入口可达

- 方法：沿 Home 唯一路由表的两条 route row（问题、场景）实际走读，并重算 `entry_kind → question|entry_scene → product → module → object → scene → boundary → reader_path`。
验证：固定问题和固定场景都能到达唯一目标 PageProjection；Home 是唯一公开轴索引，不存在旁路目录；每条 route row 与 Reader path、PageProjection、typed semantic ledger 和 `audit_ref` 一一绑定，路由记录可回查。
- 失败条件：只能从文件名进入、入口只到产品目录、出现独立 modules/boundaries/knowledge 轴目录、跳过问题/场景、路由指向错误对象或链接断裂。
- 证据类型：Reader route trace、RouteRecord、`surface-qa` 的 rendered-link/heading receipt、页面截图/链接清单；receipt 必须绑定 candidate bundle manifest/tree digest。
- 影响状态：SCN-001、SCN-005。

### AC-005：五类 page type 合同

- 方法：对六个 quality case 的页面类型逐项检查必答槽位和禁止内容。
验证：定位、概念、操作、诊断、经验分别满足本规格第 6 节，Q-BND 两个投影均可用。
- 失败条件：全部默认 procedure、页面类型与主意图不符、必答槽位缺失或把复盘意见写成规则。
- 证据类型：PageProjection、Reader 页面、case evaluator 记录。
- 影响状态：SCN-006、SCN-008。

### AC-006：结构和媒体保真

- 方法：用 `G-MEDIA-CLAIM` 对所有涉及的表格、图片、链接、代码/配置和命令检查 RenderLedger，再做人工可读性走读。
验证：每个结构/媒体单元都有保留、转换、Audit-only 或 blocked 处置，目标和上下文未丢失，Audit 可定位，Reader 语义不被清洗改变。
- 失败条件：图片/URL/表格被静默删除、命令变成无上下文文字或媒体 Claim 没有 owner。
- 证据类型：Block 对照、Claim lineage、G-MEDIA-CLAIM、`surface-qa` 的媒体/链接渲染 receipt 和清理结果。
- 影响状态：SCN-004、SCN-008。

### AC-007：冲突和重复分流

- 方法：使用同 hash duplicate、不同内容互补 Claim 和不同内容互斥 Claim 的固定样本。
验证：duplicate 只作 alias；互补来源保留独立 ownership 并可 co-support；互斥来源两边保留且受影响 Reader 阻断。
- 失败条件：不同内容标 duplicate、把同 target 直接当 conflict、自动选一边、合并后隐藏冲突或删除来源。
- 证据类型：source state、conflict ledger、Audit 页面。
- 影响状态：SCN-005、SCN-008。

### AC-008：空源显式处理

- 方法：验证第 89 条空白来源在清单、快照、Audit 和包状态中的表现。
验证：状态为 `empty`，与冻结 manifest 的 `expected=empty`、快照 hash、字节/行数和 Audit locator 一致，不生成假答案，并以 `known_empty` 进入 `full_run_audit_only`；它不进入 Reader，也不单独阻断包级 `released`。隐藏、误报非空、hash/locator 不匹配或缺失 Audit 证据时，包不能 `released`。
- 失败条件：空源消失、记为 N/A、生成占位事实或报告全量完成。
- 证据类型：G-EMPTY-89、source manifest、release decision。
- 影响状态：SCN-002、SCN-009。

### AC-009：source_not_documented 受控

- 方法：用有异常规则、无异常规则、空源、扫描不完整和含糊描述样本对照，并覆盖 package release 状态矩阵。
验证：v2 contract 的 `SND-RULE-001` 必须完整扫描且 explicit/ambiguous 均为空；再有完整 `semantic_zero_match_certificate.v1` 才能生成 `diagnosis/source-not-documented-status` Reader 的 `snd-status-v1` 五段、Home 双路由和 Audit anchor。文案只表达资料记录状态；普通 diagnosis 的 cause/action/escalation 在该 projection 中必须是显式 `not_applicable`，不能被补写成系统事实或处理建议。缺证书为 `unknown/Audit-only/not_released`；证书完整时 projection/quality 为预期 `not_evaluable`，其余硬门通过才可 released；扫描不完整或有匹配则 blocked/not_released。
- 失败条件：普通缺 Claim 触发特例、扫描不完整触发、跨源补异常规则或把“未记录”写成“没有”。
- 证据类型：Audit scan record、规则版本、零匹配清单、G-SOURCE-ND。
- 影响状态：SCN-005、SCN-006。

### AC-010：Reader/Audit 一一可回查

- 方法：全量检查每个 PageProjection 的 RenderLedger，并用固定 case 做人工走读。
验证：每个 Reader render unit 都有唯一 Audit `audit_ref`/状态入口；从 Reader link 可回放到 Audit anchor，再回 source block、hash、locator；Reader 不泄漏内部字段；没有 `unexplained_unit`。
- 失败条件：只有页级来源、任何 render unit 无处置、Audit 不能打开原块、Reader 展示无证据推断或内部字段污染正文。
- 证据类型：Reader/Audit paired trace、`surface-qa` 的实际相对链接/anchor/rendered text 回放 receipt；不能只用内部 RouteRecord 或文件存在证明用户入口可读。
- 影响状态：SCN-001、SCN-004、SCN-005。

### AC-011：逐 case 五维严格胜出

- 方法：按不可变 QualityCase manifest、CompanyBrainBaselineManifest 和第 10.1.1 节原子 oracle 做独立五维判定。
验证：每个适用维度都是 `KD_WIN`，每个 rubric 定义的严格优势原子都有直接证据，无 `TIE/CB_WIN/UNKNOWN/INVALID/CB_MISSING`，`N/A` 仅双方都不适用。
- 失败条件：任何适用维度持平/落后/未知、baseline 缺失、扩大 N/A 或使用总分抵消。
- 证据类型：case manifest、逐维 verdict、CompanyBrain baseline 快照、判定理由。
- 影响状态：SCN-008；失败为 `not_released`。

### AC-012：人工摘要不掩盖逐 case 失败

- 方法：构造单个 case 失败但总体摘要较好的结果。
验证：摘要确认只能确认汇总可读，不能改变逐维 verdict 或发布状态。
- 失败条件：摘要把 `UNKNOWN/INVALID/TIE` 改成通过、生成 `human_reviewed` 或总分覆盖硬门。
- 证据类型：case verdict、摘要确认记录、发布结论。
- 影响状态：SCN-008。

### AC-013：发布硬门和原子性

- 方法：分别触发切片失败、已知且闭合空源、隐藏/不匹配空源、冲突、lineage 缺失、路由失败、质量失败、权限失败和取消。
验证：已知且闭合空源仍无业务页但不单独阻断包级发布；隐藏/不匹配空源及其他硬门失败结果为终态 `publication_status=not_released` 或真实 global failure，不能是终态 candidate；没有半套新 Reader，旧合法入口不被破坏。
- 失败条件：任一硬门失败仍发布、只发布成功部分、旧导航被删除或状态写成 completed/released。
- 证据类型：发布事务结果、Reader 目录快照、Audit 和状态记录。
- 影响状态：SCN-002、SCN-003、SCN-005、SCN-007、SCN-008。

### AC-014：重复运行和恢复

- 方法：同输入重复运行、稳定快照失败重试、修改来源后重跑。
验证：运行按 `declared → snapshotted → inventoried → modeled → compiled → evidence_checked → route_checked → candidate → released` 留下检查点；同输入可识别且不重复造事实；修改来源要求新运行边界；恢复不混用新旧快照。
- 失败条件：输入变更仍沿用旧计划、重复页/重复 Claim 无 alias、旧快照和新快照混合。
- 证据类型：run identity、source hash、lineage 和恢复记录。
- 影响状态：SCN-003、SCN-007、SCN-009。

### AC-015：失败事实不伪装成功

- 方法：检查所有失败、取消、不可用和未判定路径的公开状态。
验证：缺失或不可用证据保持 `unknown/unavailable/incomplete`，Claim 中间态不会伪装成 `supported`，任务和包不声称质量完成。
- 失败条件：空 findings、绿色命令、页存在或摘要被当成质量通过。
- 证据类型：运行状态、Audit、质量门结果。
- 影响状态：所有异常场景。

### AC-016：canonical source inventory 身份

- 方法：从原始目录重算 canonical path set、source id 规则和 path-set digest，并与 `SourceInventory` 比对。
验证：89 个 entry 一一对应本规格路径清单；隐藏文件、软链接逃逸、`..` 和 inventory 外文件都被拒绝或进入 Audit；任何 hash 变化产生新 run boundary。
- 失败条件：只按数量通过、依赖输入顺序命名、路径规范化不一致或额外来源静默进入 Reader。
- 证据类型：inventory manifest、path-set digest、snapshot manifest、Audit。
- 影响状态：SCN-002、SCN-003、SCN-009；失败为 `not_released`。

### AC-017：QualityCase 与 CompanyBrain baseline 夹具

- 方法：校验六个 QualityCase、Q-BND 两个独立 projection、每个 source block ref、required/forbidden refs、适用维度、comparison rubric 和 baseline snapshot/hash；禁止预置 verdict/答案字段。
验证：所有字段齐全、hash 与快照一致、baseline 缺失记 `CB_MISSING`，任何 case 不可执行记 `INVALID`，不会被改写为 `N/A/KD_WIN`。
- 失败条件：只有问题和路径、baseline 只有活路径、Q-BND 合并身份、必答 Claim/边界缺失或 strict oracle 缺失。
- 证据类型：case manifest、baseline manifest、逐维 verdict、处置记录。
- 影响状态：SCN-006、SCN-008；失败为 `not_released`。

### AC-018：全量 coverage 与 render ledger

- 方法：逐行检查 89 个 source entry、全部 supported Claim、KnowledgeUnit、PageProjection 和 Reader render unit 的 CoverageLedger/RenderLedger 关系。
验证：每个来源都有 coverage class；每个普通非空 Reader projection 都有 source-digest/quality/guard coverage，显式 source-direct-audit projection 明确为 Audit-only；每个 render unit 有 Claim/状态和 source block 处置；不存在 `unexplained_unit`。
- 失败条件：未覆盖来源/页面进入 Reader、Claim 或媒体没有 ledger、只靠抽查或页数统计声称完整。
- 证据类型：CoverageLedger、RenderLedger、Reader/Audit paired trace、guard case 结果。
- 影响状态：SCN-004、SCN-005、SCN-008、SCN-009；失败为 `not_released`。

### AC-019：运行/Claim 检查点和特殊审计

- 方法：验证运行状态、Claim `extracted → normalized → linked → supported` 和 `SND-RULE-001` 的完整扫描记录。
验证：每个状态转换有前置条件和失败边界；特殊审计只有完整零匹配清单才触发；取消、失败、含糊命中和缺 lineage 都保持可见。
- 失败条件：跳过检查点、`extracted/normalized/linked` 进入 Reader、扫描不完整却触发 `source_not_documented` 或把负证据改写成系统事实。
- 证据类型：run state ledger、Claim state ledger、Audit scan record。
- 影响状态：SCN-003、SCN-005、SCN-007、SCN-009；失败为 `not_released`。

## 12. 数据生命周期与用户可见边界

### 12.1 生命周期

来源从 `expected` 开始，经快照、Block 保真、Claim 抽取、知识建模、页面投影、证据检查和路由检查后形成 `candidate`。只有质量和完整性硬门全部通过才形成 `released`；任何上游异常都沿对应层级保留，不删除原始事实。

### 12.2 读写边界

- 输入边界：当前声明的 89 条本地原始资料及其快照。
- 事实边界：业务事实只能来自当前原始来源；CompanyBrain 不能补事实。
- Reader 边界：只发布可回答、证据完整、页面类型正确且质量 case 通过的内容。
- Audit 边界：保留所有来源、失败、冲突、Claim、规则扫描和路由诊断，包括不进入 Reader 的内容。
- 旧产物边界：Task4、旧页面类型和 CompanyBrain 不被本任务改写。

### 12.3 兼容性

Task5 使用五类新 page type；Task2/Task3 的历史三类页面记录保持历史语义，不被迁移或伪装成 Task5 结果。已有合法托管页面在一次失败发布中保持不变。

## 13. 研究、风险与规格交接

本阶段无新增外部接口或实时规则；decision-log 已冻结流程、页面/状态/CompanyBrain 边界、QualityCase 和失败语义，conditional research=`skipped`、clarify=`not_applicable`。实现只能选择排版、内部存储和测试组织，不能改变 89 条闭包、lineage、五类 page type、Reader/Audit、`source_not_documented`、六 case、五维逐项 `KD_WIN` 和 guard 硬门。来源不可读必须写 `processing_failed` Audit；标题匹配、边界、负证据、总分抵消和切片替代全量均由对应 AC/guard 阻断。性能另行研究，不降低质量门。

本文件已冻结用户流程、页面/状态/失败边界、语义链、五类页面、Reader/Audit、五维 CompanyBrain 比较、切片/89 条闭包、恢复和原子发布；build-plan 只能映射执行，不得改变范围、放宽质量门或混入延期项。

## Repair revision v2 — provider-backed semantic compiler

本 revision 只修复当前 Task5 的真实编译入口，不重写 Task4、CompanyBrain 或正式 `digest` S1–S6。它覆盖上一轮实现与用户要求之间的关键断裂：代码中虽然存在 `llm.py` 和 `embedding.py`，但 Task5 运行链没有调用它们，结果因此退化为确定性文件/行整理。

### 修复后的用户可见结果

真实命令必须按以下路径运行：

`原始 89 条资料 → 快照/Block/Claim → Qwen 语义编译 → embedding 问题/场景路由 → 五类页面投影 → Reader/Audit 校验 → 五维比较 → Downloads 运行中 candidate → 终态 not_released 或 released`

Reader 入口仍是 `Home.md`，但页面正文不能来自未经语义编译的整篇来源。来源全文、所有 Claim、provider 调用结果、embedding 路由结果和失败原因进入 Audit；Reader 只显示通过合同的业务答案。

### Provider contract

1. Provider config 由 `--provider-config` 或 `~/.config/knowledge-digest/config.json` 提供。v2 配置允许记录 `api_format`、`base_url`、`model`、timeout、批量上限、`api_key` 和 embedding calibration artifact；`api_key_env` 仅作兼容回退，`api_key` 优先。Authorization header、`apikey`、token、password、secret 和未声明字段仍禁止；密钥不进入 receipt/report。
2. LLM 只能使用批准 endpoint `https://dashscope.in.whatspos.cn/v1` 上由配置明确声明的 `qwen3.6` 或 `qwen3.8`；运行前必须通过 `/v1/models` 能力校验，receipt 绑定实际返回的 model，不得把 `qwen3.8` 冒充成 `qwen3.6`。当前用户配置对应的 endpoint 实际只提供 `qwen3.8`，因此本次真实运行使用 `qwen3.8`；embedding 真实身份固定为 `jina-embeddings` + `https://llm.paxszapp.com/v1`，并且必须通过现有 calibration artifact、dimension 和 probe identity 校验。
3. Provider calls 必须写 planned/observed/succeeded/failed、输入快照 hash、输出 hash、model、endpoint identity、config hash、call sequence 和 reason code；不得保存凭据或完整 secret-bearing 请求。
4. 修复入口的 semantic mode 是 `provider_required`。缺配置、缺 key、网络失败、超时、JSON 结构错误、模型/endpoint 不匹配、embedding 部分响应或 calibration 失败都产生 `provider_failed`/`blocked`，不允许切到 identity generator 或 Jaccard 继续宣称质量完成。
5. 每个逻辑 provider call 只允许一个实际 HTTP attempt：用户 config 的 `llm.retry_attempts` 和 `embedding.retry_attempts` 必须显式为 `0`，客户端、批处理器和 transport 也不得隐式 retry。`observed_calls` 按实际 HTTP attempt 计数；receipt 必须写 `retry_attempts=0`、`http_attempt_count=1` 和逻辑 call identity。无法证明 retry 为零、`http_attempt_count != 1`、或 observed attempt 超出 planned/max 时，在下一次网络请求前 `blocked/overrun`，不能把 transport retry 当作逻辑 call 或静默吞掉。

6. provider 可行性在 design exit 先用冻结的 `config/task5-provider-contract-handshake-v3.json`（actual SHA-256=`c15c06120550ddab294540c91376ac480cd64e82617c3a8edbebee162e34dee0`、canonical=`fc821c355…`）定义并由实现闸门证明：R1 必须按 `route_case_matrix` 对 `source-digest`、`quality-reader`、`source-direct-audit` 三类 route 各执行并 hash 一个 success case 和一个 negative case，R3 必须用 fake embedding 产生 `quality-reader` full/slice route、selected-path consumption、越界拒绝和多来源 closure identity 变化的 canonical handshake receipt；两者都不得联网，且 receipt 必须绑定 semantic/embedding/path-relation contract schema hash。embedding handshake 还必须绑定 calibration manifest/artifact 的路径、schema、SHA、endpoint、model 和 dimension。缺 route、handshake、hash 不匹配或 fake 测试不能证明失败分支时，R1/R3 不得 promotion，M302/M401-R/M402 均停止。fake handshake 只证明接口可行性，不得被 M402 当作真实 Qwen/Jina 结果。

### LLM semantic compilation contract

- 每个非空来源都先由确定性 parser 形成完整 Block/Claim ledger；LLM 只消费带稳定 Claim ref、locator、kind、section heading、media/link/structured tags 的受信输入。
- LLM 输出是 typed JSON，不直接输出页面文件，且必须符合冻结的 `config/task5-provider-semantic-output-v2.json`；`title` 是冻结 route projection 的元数据，不是模型事实：request 带 `expected_title`，返回值必须逐字相等，public path 也只用该冻结标题，不需要 `title_claim_ids`；不相等即 blocked/Audit-only。其余字段为五类 `page_type`、`page_type_claim_ids`、五轴 `axis`/`axis_claim_ids`、`summary` 和 `sections`；五轴固定为 `product/module/object/scene/boundary`，section slots 按 page type 固定，所有 Claim ref 必须来自当前 request。Claim scope 按 route 分流：`source-digest`/`source-direct-audit` 只能引用各自单源 closure；`quality-reader` 可引用本次 selected source closure 内的多个来源，但每条 Claim 必须保留唯一 owner/source/block/locator，并通过 `co_support|conflict|unknown` 关系校验；任何 closure 外 Claim、来源不明、未知字段、模型发明事实、原文整篇复制和 raw fallback 都拒绝。`llm.max_input_chars=120000` 按 `config/task5-provider-config-v2.json` 的 `max_input_chars_semantics` 解释为 Python `len(prompt)` 的 Unicode code-point 数；request、preflight 和每个 provider receipt 必须记录 `input_chars` 与 `input_length_unit=unicode_code_points`。超限只写 Audit/blocked，不截断、不发送、不重试，也不能用 provider 返回结果绕过该门。`source-digest` 逐源请求另受冻结的 `config/task5-source-digest-contract-v2.json` 约束；显式 `route_kind=source-direct-audit` 仍只能进入 Audit/coverage，不得生成 Reader。schema/hash 漂移、标题不等、Claim 越界或 route 分支串用都在网络前 blocked。
- `required_atom_evidence` 的规范形状是 `dimension → canonical_atom → {knowledge_unit_ids, claim_ids, support_spans, surfaces, scope}`；`knowledge_unit_ids` 必须指向当前 typed output 的 supported units，`claim_ids/support_spans` 必须是这些 unit 的子集，`surfaces` 只能是当前 projection 允许的 `route|axis|summary|page_type|slot:<slot>|audit`，`scope` 固定为 `selected-source-closure`。运行时不信任模型自报的证据：按 unit→Claim→Block/hash/locator 重新计算 atom coverage、surface ownership、关系/极性和 scope；字段缺失、集合不一致或 atom 没有落在声明 surface 时，该 atom 为 `UNKNOWN`，该 projection 不能 `KD_WIN`。该字段的输入/输出 hash 与重算结果写入 provider receipt 和 RenderLedger。
- QualityCase 的 `page_type` 和必答槽位由冻结 case contract 约束，模型只能填正文和证据引用，不能擅自改成另一个类型。普通 source-digest entry 的 `page_type` 由冻结 source manifest 预先指定；Qwen 必须在 typed output 中复述该类型并给出支持 Claim/理由，不能重新选择或改成另一个类型。显式 source-direct-audit 也只能使用其单源 Audit contract；source-digest 成功产生 Reader projection，source-direct-audit 只产生 Audit/coverage，QualityCase 另产生 ReaderTaskPath。
- 所有 claim id 必须属于当前输入且状态为 `supported`；正文引用的每个事实、数字、版本、URL、路径、命令、限制和条件必须能回到一个或多个 source block。Claim 只出现在 Audit 不等于 Reader 已回答。
- typed JSON 失败、缺槽位、错 Claim、受保护 token 丢失、正文只是完整原文包装、跨源 ownership 丢失或出现来源外事实时，页面状态为 `blocked`，不生成 raw fallback Reader。

### Embedding routing contract

- embedding 对冻结 quality case 的问题、显式 `aliases`、product/module/object/scene/boundary 和 projection page type 组成一个 canonical query；每个 projection 只发送一个向量，不把这些字段拆成多个隐含请求。Jina source vectors 只消费 `route_descriptor.v1` 的 title/question/page_type 元数据，不消费 canonical_text、Block、媒体或未选 source 内容。真实 route trace 至少保存 canonical query、query hash、字段覆盖、candidate source id/path、score、rank、selected、reason 和 provider identity。`top_k` 只负责对候选做稳定排序和发现；quality case 已声明的 authenticated `required_source_paths` 必须在 route 后按排名顺序并入 `selected_source_paths`，完整闭包作为 Qwen 输入。top-k 之外的冻结闭包来源不是 route-only；只有不属于冻结闭包的 top-k 候选才记为 `route_only_source_paths`，不得进入 Qwen、KnowledgeUnit、Reader/Audit claim support 或评分。
- 本 repair revision 的 embedding 只生成并消费六个 QualityCase 的 8 个 projection route（Q-OPR、Q-BND 各两个，其余各一个）；不生成 related-topic candidates，也不把相关主题链接作为本次交付能力。后续相关主题检索属于延期项；相似度不能单独创建 Claim 或覆盖冲突/空源状态。
- 若 embedding 无法使用，当前 run 不能混合 Jaccard；可以保留来源和 LLM Audit，但 run 必须 `not_released`，并把 `embedding_unavailable` 作为硬失败。

Embedding candidate 仍必须来自冻结 `source-descriptor.v1`，并记录 candidate set/vector/query/rank/tie-break/selected/route-only hashes；输入置换须稳定，selected vector/closure 必须进入 Qwen/PageProjection，route-only 不得进入正文、Audit 或评分。`routing.top_k` 当前固定为 `8`，是候选排序上限，不是冻结 quality closure 的硬上限。candidate 集为空、无效分数、并列排序不稳定、descriptor/closure 漂移、required closure 中的路径不存在或 selected closure 与 required closure 不相等，均在 provider 前 `blocked`；只因 required closure 大于 top-k 或 top-k 未命中全部 required paths，不得阻断，因为这些 required paths 会按认证闭包并入 Qwen。request identity、budget、handshake、prompt、route ledger 和测试 receipt 必须写实际 `top_k=8` 与 `selection_kind=frozen_closure_union_ranked`。

#### Selected-source identity contract

所有 provider/embedding/semantic projection 的来源身份必须使用同一个 `selected-source-identity.v1` 算法，不能只记录路径列表。每个选中来源的 canonical row 固定为：

```json
{
  "source_id": "...",
  "canonical_relative_path": "...",
  "snapshot_id": "...",
  "raw_content_hash": "...",
  "byte_count": 0,
  "line_count": 0,
  "block_refs": [
    {
      "block_id": "...",
      "block_content_hash": "...",
      "raw_start_byte": 0,
      "raw_end_byte": 0,
      "locator": "..."
    }
  ]
}
```

source 按 `(canonical_relative_path, source_id)` 排序，block 按 `(raw_start_byte, raw_end_byte, block_id)` 排序；raw content hash 必须来自快照中的 UTF-8 bytes，不能用路径 hash 冒充。canonical bytes 固定为 UTF-8、递归 key 排序、无空格、禁止 NaN、末尾 LF 的 JSON。单源 `source_hash` 可非空，但 `selected_source_closure_sha256` 也必须计算且不得为 `null`；多来源 `source_hash` 必须为 `null` 且同样写 closure hash。closure 行至少包含 source snapshot/hash、selected block refs、raw block hash、locator 和 byte span；`request_identity = SHA256(canonical_json({evaluation_mode, route_kind, source_id_or_projection_key, source_hash, selected_source_paths, selected_source_closure_sha256, query_sha256, config_hash, runtime_contract_id, runtime_contract_hash, semantic_contract_id, semantic_contract_hash, prompt_contract_sha256}) + LF)`；没有 query 写 `query_sha256=null`。closure hash 必须原样写入 request、provider receipt、embedding route ledger、semantic-response-ledger、PageProjection、RenderLedger、Audit 和 quality result；来源重排、任一 raw hash/block closure、prompt contract 或任一运行编译合同变化都必须生成新 identity，禁止复用或覆盖旧 receipt。

### 新增功能需求与验收标准

| ID | 必须行为 | 失败行为 |
| --- | --- | --- |
| FR-RP-001 | 读取用户 provider config，校验 schema、endpoint、model、`api_key`/`api_key_env` 和 calibration | 配置缺失/越界直接失败，不读取其他 secret 文件 |
| FR-RP-002 | 87 条普通 present 非空来源进入真实 LLM semantic compile ledger；1 条 SND replacement 不发 Qwen 但必须有固定 Reader/Audit 闭包；第 89 条 known_empty 只进 Audit | 未调用、调用失败或输出无效不得进入 Reader |
| FR-RP-003 | LLM typed output 保留五轴、页面类型、槽位和逐 Claim lineage | 字段存在但正文/证据不一致时 blocked |
| FR-RP-004 | embedding probe 后实际参与六个 QualityCase 的问题/场景 route | 只有 probe、没有实际 quality route calls 视为失败；related-topic route 不在本 revision |
| FR-RP-005 | provider/lineage/media/route 失败只进 Audit，不能 raw fallback | 不得把大段原文包装为业务答案 |
| FR-RP-006 | 89 条 inventory、slice→full、状态和 Downloads 输出继续可回查 | staging 必须是 Downloads 同文件系统 sibling，不能放在 `/tmp` 或作为用户交付入口 |
| AC-RP-001 | provider config hash、模型、endpoint identity 和调用计数可回查且无 key | 脱敏不完整或计数为 0 时失败 |
| AC-RP-002 | Qwen semantic call 的输出通过 typed contract 和 source-block gate | 任一质量 case 缺正文/Claim/边界即阻断 |
| AC-RP-003 | embedding route ledger 有实际 query/source vectors 和 top-k 选择 | 只有 embedding probe 或混用 Jaccard 即失败 |
| AC-RP-004 | provider 失败不生成 Reader fallback，Audit 保存 reason code | 发现 raw full-source Reader 即失败 |
| AC-RP-005 | 本地 fake provider/embedding 测试覆盖成功、JSON 错、超时、部分向量、key 缺失、config 漂移 | 只有 happy path 不合格 |
| AC-RP-006 | 修复后完整 Task5 acceptance 和旧正式管线回归通过 | 回归失败不得进入真实测试 |
| AC-RP-007 | 分两阶段：M401/M401-R 先证明真实运行前置约束并将 actual-run 标为 pending；M402 再用只读 raw/CompanyBrain 生成 Downloads 新目录、真实 status/exit 和 post-run receipt | 前置约束、实际运行或状态证据缺失；凭据/provider 缺失必须显示 blocked/unavailable，不得猜测质量 |
| AC-RP-014 | M401-R 生成 hash-bound `task5-m401-r-review-receipt.v1`，证明 `mini_task.implementation` 为 terminal semantic clean 且每条 finding 已处置 | 只有 provider transport 完成、本地测试绿、旧 review 或未绑定 packet 的口头结论，均不得放行 M402 |

M402 的首个动作是 `m401-r-gate-preflight`，发生在读取 raw/CompanyBrain、创建 source snapshot 或发出任何 LLM/embedding 请求之前：按命令参数读取 `quality/evidence/task5/M401-R-review-receipt.json`，校验其 schema、canonical SHA、`review_kind=mini_task.implementation`、`review_outcome=available`、`terminal_clean=true`、全部 finding disposition、所绑定 M401 packet SHA、当前 snapshot tree 和 material_id；同时校验当前 `mini_task.design` 的 terminal-clean identity：`review_attempt_ref`、`review_result_ref+sha256`、`review_report_ref`、`design_review_contract_id`、`design_review_contract_hash`、`semantic_hash`、`snapshot_tree`、`material_id`，以及 Task5 `runtime_contract_id/runtime_contract_hash/semantic_contract_id/semantic_contract_hash`，必须在 M401 packet、M401-R receipt 和本次 invocation 三方完全相等；另外只校验 SND contract 的静态 schema/actual/canonical SHA，不把尚不存在的 current SND verifier receipt 当作读前输入。任一字段缺失、旧 receipt、路径/哈希漂移、未处置 finding、任一合同 identity 不同或 material 不同，必须在 Downloads failure evidence sink 写 `M401_R_GATE_MISSING|STALE|DRIFT`，observed provider calls 固定为 `0`，结果为 `blocked`、exit `2`，不读取原始知识、不读取 CompanyBrain、不调用 provider；该负例必须由 M301/M302 测试覆盖。通过读前 gate 后，运行器才建立当前 raw snapshot，并在 SND Reader/Qwen/embedding 前生成、独立复核并 promotion 本次 SND verifier receipt；M401-R receipt 只证明实现审查通过，不代替 M402 的真实 Qwen/Jina 运行结果，也不代替 current SND receipt。

### 修复 revision 的非目标

不在本 revision 中加入数据库/向量库、后台调度、增量同步、在线搜索、编辑工作台、CompanyBrain 事实复制、自动放宽 quality gate、自动生成原始资料之外的事实或 commit/merge/push/cleanup。旧 P1–P4 的历史结果继续保留为失败原因和回归对照；本 revision 的真实 provider 结果不得覆盖旧产物。

## Repair revision v2.1 — design clarifications from review

以下规则是对本 revision 的可执行补强。它们覆盖旧 P4 中“无网络/provider、允许 fidelity-only fallback”的历史实现安排；旧实现事实保留在 tasks/evidence 中，但 provider-required 真实入口必须服从本节。

### 7. 五维实际评分修正（v2.2）

旧版原子布尔/替 CompanyBrain 补分文字是历史设计；当前每个 case×dimension 输出独立 `0-100` 诊断分：

- `content_score`：先通过 typed semantic support、Claim/Block lineage、实际 surface、scope 和 negation/conflict hard gate，再按该维度 rubric 的 `required_atoms`/共同 `atom_forms` 观察实际正文；命中比例只作诊断，不能单独生成 verdict；
- `structure_score`：只观察双方实际 Markdown 的共同可见正文、来源标记、定位信息和该维结构标记；不计内部 JSON、Audit 文件数或 RenderLedger。Reader-Audit 使用冻结等级 `none < metadata < source-clue < archive-reference < source-locator < claim-exact`，不因 CB 无 claim-level Audit 自动归零。
- `kd_score = round_half_up(0.7*content_score + 0.3*structure_score, 2)`，`cb_score` 同理；它只是诊断字段。`KD_WIN` 还要求本维 hard gates、path replay、同维真实 CB gap 和逐 atom strict advantage；相等=`TIE`，缺证据=`UNKNOWN`，baseline 无效=`CB_MISSING`，不跨维抵消。

评分顺序固定：先校验 typed unit、Claim owner/source/block/locator、surface、scope、关系/否定/冲突；硬门通过后才用双方共同 `atom_forms` 做等义/词形观察，关键词/完整字符串不构成支持。已通过 scope 的 `forbidden_atom` 命中则诊断 `content_score=0`；正文或结构证据缺失不得默认补分。结构分只看双方可见 Markdown/evidence level，不奖励 KD 内部 claim/source/hash/Audit/RenderLedger；仅 CB 文件缺失、hash 漂移或 applicability 缺失才 `CB_MISSING`。

Provider typed output 的 `page_type`、五轴每一项、summary 和每个 Reader slot 都必须带自己的 Claim refs；`page_type_claim_ids` 不是装饰字段，缺失或不属于本次 provider 输入 Claim 集合时，页面只能 Audit/blocked。embedding route 的 selected source paths 必须同时进入 provider prompt、provider receipt、PageProjection、RouteTrace 和质量 case；只写 route ledger、不消费 selected candidates 不算使用。full 与 slice 的 embedding probe/batch 次数按两次独立 route 的实际批次相加，调用预算必须在网络请求前覆盖两次 probe。

`comparison_rubric` 只能提供可观察的原子和结构标记，禁止预写分数、verdict、答案或 `strict_advantage`。结果必须保存双方分数、delta、命中/缺失项、结构原因、`path_replay_ref`、`companybrain_snapshot_ref`、`cb_observation_ref`、逐维 `advantage_basis` 和 evidence refs；`strict_all_kd_win` 只能由五个逐维 `KD_WIN` 派生，且每个 `KD_WIN` 都必须能回查两侧真实 observation digest 和 route snapshot digest。对应实现版本为 `task5-quality-result.v3`。

### 8. 当前 v2 质量 oracle 的冻结身份和多投影规则

provider-required 运行不允许实现者在代码里临时挑选 atoms、markers 或 baseline：

- 质量 fixture：`config/task5-quality-cases-v2.json`，SHA-256 `8d2a5024bce31bd48709d363bbf8cf578b18b46be732f58e4bd133f881c32f67`；CompanyBrain 对照：`config/task5-companybrain-baseline-v2.json`，SHA-256 `ba69f3ce432af0c8967ad4ba1df97c2abec64f40657bdd0bca48106722d79e3a`。每个 case 还冻结显式 `aliases`、`atom_forms`、Claim/surface/scope refs 和独立 projection closure，canonical embedding query 不能从实现代码临时补词；baseline v2 还冻结真实 Reader-Audit evidence-level observation 和每条 entry 的 `projection_keys`，不能用 KD 内部 JSON 给自己加分。
- provider feasibility handshake：`config/task5-provider-contract-handshake-v3.json`，actual SHA-256=`c15c06120550ddab294540c91376ac480cd64e82617c3a8edbebee162e34dee0`、canonical=`fc821c355…`；该文件用 `route_case_matrix` 冻结 `source-digest`、`quality-reader`、`source-direct-audit` 全部 LLM route 的 success/negative 映射，另冻结 embedding route、request identity、selected-source identity、receipt 字段、成功/拒绝/no-network cases 和 R1/R3/M302/M401-R gate obligations，不包含密钥，也不代表真实 provider 成功。embedding handshake 同时冻结 calibration manifest/artifact identity。实现不得临时减少 route/case 或把 fake receipt 复用为 M402 真实 evidence。
- 六个固定 case 是 `Q-POS-01`、`Q-CON-01`、`Q-OPR-01`、`Q-DIA-01`、`Q-EXP-01`、`Q-BND-01`；每个 case 的问题、五维 `required_atoms`、`structure_markers`、`forbidden_atoms`、`source_paths` 和 baseline 文件/hash/locator 只从上述冻结字节读取。运行配置 `config/task5-reader-quality-provider-v2.json` 再绑定这两个 hash；传入其他内容在网络前 blocked。
- 投影集合也冻结在 v2 fixture：`Q-POS-01=positioning`、`Q-CON-01=concept`、`Q-OPR-01=operation (projection_subtype=qr|zero-touch)`、`Q-DIA-01=diagnosis`、`Q-EXP-01=experience`、`Q-BND-01=operation + diagnosis`。每个 projection 有独立 projection key、provider receipt、Reader、Audit、RenderLedger 和五维观察；二维码/Zero Touch 子类型不是第六种 page type。
- 一个 case 的 CompanyBrain baseline 可以覆盖该 case 的多个 projection，但不能让一个 projection 代替另一个。baseline 每条 entry 必须有非空 `projection_keys`，且只能把同一份实际文件观察绑定到明确列出的 projection；evaluator 以 `projection_key` 而不是只以 `case_ids` 做 join，缺 key、错 key 或把一个 projection 的观察借给另一个 projection 都是 `INVALID`。KnowledgeDigest 采用保守聚合：每个 projection 先独立计算五维分数和硬门，case×dimension 取各 projection 的最低分，且所有 projection 都必须通过 required/forbidden/lineage/structure 硬门，才可能是 `KD_WIN`。

必答内容优先于结构分：任一 projection 缺少当前维度的 required atom、命中 forbidden atom、缺字段级 Claim refs 或证据结构不完整，该 projection 的 KD 观察不可用；结构分不能抵消必答内容缺失。`KD_WIN` 还必须满足上述硬前置、path replay、同维 CB gap 和逐 atom strict advantage，分数不能补回失败。

必答内容的字段级证据不是一组可以随意挂接的 Claim ID：编译器在接受 Qwen v2 页面后，派生页面级字段 `required_atom_evidence[dimension][atom] = {claim_ids, surfaces, scope}`，内部同时保留可回查的 unit/support span。`surfaces` 必须遵守 §10.1.2 的维度矩阵；只有 `Reader-Audit` 维度允许 `audit`，前四个维度的业务原子必须在真实 Reader 表面出现。`scope` 固定为 `selected-source-closure`。运行时验证派生 unit、`claim_ids` 和 `support_spans` 都来自当前 typed output 及其 Claim/Block 映射，atom 出现在声明表面、Claim 归属于该表面、Claim 有唯一 `source_id`/`block_id`、`content_hash`、`block_content_hash` 和有效行号；只共享一个泛词的无关 Claim、selected closure 外 Claim、缺范围或否定/不支持 Claim 均为 blocked/UNKNOWN。selected closure 内的多源 Claim 仍必须逐条验证 owner 和 `co_support|conflict|unknown` 关系。测试必须包含“正文命中但 Claim 无关”和“只在 Audit 命中、Reader 正文缺失”的负例。

### 9. provider implementation boundary and risk handoff

`quality-reader` selected-source projection 的失败是原子的：任一选中来源命中 `SOURCE_SENSITIVE_CONTENT`，或任一选中字段漏扫、scanner/payload 漂移、selected closure 不完整，整个 projection 必须在 socket 前失败并保持 calls=`0`。禁止删掉命中来源、改写 closure、重算 request identity 后重试、发送剩余来源的 partial payload，或把失败来源标成未选中；只有不相关 route/projection 可以继续，同一 projection 不生成 Reader、quality 或 publication。该规则与 source-local 的“其他来源可继续”不同：其他来源只能作为独立 projection 继续，不能拼成当前失败 projection 的替代请求。

实现复用现有 OpenAI-compatible client、retry=0、provider identity 和校准加载；pytest 只注入 fake，M402 才允许真实 Qwen/Jina。真实出站按 `config/task5-external-processing-policy-v1.json` 与 `config/task5-source-sensitive-content-scan-v1.json` 校验 endpoint、最小 source scope、provider-config SHA、policy mode 和 scanner SHA；Task5 只允许在 `task5_provider.py`/`task5_provider_config.py` transport seam 建 client/call，建 socket 前执行 approved host allowlist，记录 retry=0/HTTP attempt，未知 endpoint 在 socket 前阻断。M401 测试进程使用 `/usr/bin/sandbox-exec` `(version 1)(deny network*)`，主动探测 socket/DNS/urllib 三条路径并把 guard profile/命令 hash、exit、calls 写入 validation receipt，sandbox 不可用时 calls=0。每个 selected Block 以及 embedding route descriptor/query 的所有 text fields 都先执行冻结 scanner；唯一的 `Task5ProviderTransport.call_once` 在组装最终 LLM JSON wire payload 后、socket 前，还必须递归枚举所有 text-bearing JSON pointer（至少 `messages[*].content`、title/question/page_type、provider-visible URI、claim/route metadata、semantic frame）并逐字段扫描原始/NFKC 视图。字段回执绑定 JSON pointer、source/block/claim ref、scanner actual/canonical SHA、payload digest 和 match digest；只扫描 Block 或中间 prompt 不能替代最终 wire scan。字段缺失、未扫描、payload 漂移或 scanner contract 缺失/漂移时，必须 `SOURCE_POLICY_UNVERIFIED`、calls=0，不建立 socket。credential/PII/unknown-high-entropy 命中即 `SOURCE_SENSITIVE_CONTENT`、calls=0、当前 source/route blocked、继续其他来源，最终 full `not_released/exit=1`；不静默脱敏。若 policy 或 scanner 证明缺失/漂移则 `SOURCE_POLICY_UNVERIFIED` 为 global blocked/exit=2。`api_key` 只能入内存，不得进入 payload、receipt、cache 或 bundle。

设计审查包中的 authority appendix 只是引用清单，不等于外部 JSON/fixture 字节已被审查包携带或验证。M101 baseline preflight 必须在任何 provider、embedding、RED、代码写入、R1 promotion 或 M102 前逐项读取并校验 authority 的存在性、schema、actual SHA、canonical SHA、摘要和交叉引用，写入 `task5-baseline-preflight.v1`；`M101 RED`、后续 `M102 GREEN` 和 promotion 必须显式携带并复核同一 baseline-preflight ref/SHA、promoted root-cause ref/SHA、snapshot/material，缺失或漂移时 calls=`0` 且不写 gate receipt。任一外部 authority 缺失、不可读或漂移都只能 `blocked/calls=0`，不能用 design terminal clean、路径存在或摘要文字替代。

四个 `_audit` ledger 用 canonical JSON+LF、单写者和 manifest 绑定；response ledger create-only，冲突为 `response_variant`。跨运行 exact replay 必须遵守 `config/task5-replay-store-v1.json`，查找 `/Users/Hugh/.config/knowledge-digest/replay/task5-semantic-response-ledger.jsonl`（目录 `0700`、文件 `0600`）。每条可复用 entry 必须是 `provider_mode=real` 的成功响应，绑定 provider receipt/ref+SHA、call ledger/ref+SHA、恰好一次 HTTP attempt、原始 run identity、source snapshot/closure、runtime/semantic/prompt contract、compiler snapshot 和 parser/semantic-frame snapshot；只存 normalized typed JSON 及身份/hash，不存 key、Authorization、prompt、原始 response、raw source 或主机路径。当前运行逐字段精确复核后才允许新 Downloads output 记 `provider_calls=0`；variant、fake/缺 receipt、漂移、权限/格式异常写 failure sink 并 `blocked/not_released`。bundle 只写 replay hash/ref projection，保留到人工清理；缺 ledger/hash/replay/manifest 或 scan-failed response 不发布。

真实 receipt 的 writer authority 另外固定：所有 Qwen/Jina 网络流量只能由 R2-owned `Task5ProviderTransport.call_once` 发出，client、batcher、replay loader 和 caller 不得自报 `provider_mode`、`http_attempt_count`、response hash 或 `observed_calls`。该 seam 在 DNS/TLS/socket 前完成 approved host/TLS 校验，并在每个实际网络尝试开始前登记不可变 attempt identity；无论收到 HTTP 响应、DNS/TLS/连接失败还是 read timeout，都由 seam 以 create-only 方式写 `task5-provider-transport-attempt.v1` ledger row。无响应行必须含 `transport_phase`、`error_class`、`socket_attempted`、`http_attempt_count=0`、`retry_attempts=0`、`observed_calls`、`response_normalized_sha256=null` 和错误摘要 hash；HTTP 成功/错误行才含 response status/digest。每行绑定 `writer_id=Task5ProviderTransport.v1`、单调 `transport_event_id`、run/request identity、endpoint/model、TLS peer validation digest、request payload digest/byte count 和时间戳；不保存 prompt、response、key、Authorization 或 raw source。semantic response、failure evidence、run-result 和 replay 必须引用该 row 的 ref+SHA；缺失、序列断裂、writer 不符、ref/hash 漂移或 caller 填写计数时，立即 `blocked/calls=0`，不能把运行自报字段当真实 provider 证据。fake handshake 只能证明接口可行，不能满足 real replay。

## 11. semantic evidence、全量路由和精确回滚补强

本节的 provider 边界以 `config/task5-provider-semantic-output-v2.json` 为准：Qwen 只返回 `schema_version`、`title`、`page_type`、`page_type_claim_ids`、`axis`、`axis_claim_ids`、`summary` 和 `sections`。`KnowledgeUnit`、`required_atom_evidence`、`semantic_evidence`、`ReaderTaskPath`、relation facts 和 RenderLedger 都是编译器在收到 v2 JSON 后，根据当前 Claim/Block 和实际 Reader surface 派生、校验和记录的内部证据；Qwen 不直接返回这些对象。下文凡是把它们写成“Qwen 必须返回”的旧表述，按本段修正，不得进入 prompt、response schema 或 provider receipt 的必需字段。

### 11.1 确定性 Claim 不是语义事实

解析器产生的 `EvidenceClaim` 只表示“某个 source block 在某个 locator 有这段原文”，不表示它已经被理解成可给读者的业务结论。`KnowledgeUnit` 是编译器根据当前来源 Claim、已接受的 Qwen page surface 和确定性关系校验派生的内部证据对象，不是 Qwen v2 必须直接返回的字段。进入 Reader 的每个 summary、axis、page type 和非空 slot，都必须由派生的 unit/Claim 证据回到当前输入 Claim 的 block/hash/locator；无法派生或无法回查的内容只能进入 Audit。

`KnowledgeUnit` 的支持不是“共享一个关键词”。Normalizer 从 Qwen 已返回的页面文字和 Claim refs 派生 unit，再同时检查：引用 Claim 属于当前输入、Claim 为 supported 且无 conflict、派生 statement 与引用 Claim 有保守的证据闭合、statement 没有超出 selected source closure、没有把整段原文原样包装成答案。无法证明支持、出现否定/冲突范围不清或 unit 引用了无关 Claim 时，该 provider page 只能 Audit-only，不能由结构分补成 `KD_WIN`。

#### 11.1.1 KnowledgeUnit 的确定性支持谓词

为了避免把“模型说它理解了”当成事实，本 revision 固定一个可由代码重算的 `KnowledgeUnit` 接受谓词。Qwen v2 不直接返回 semantic fact candidate；编译器从页面的 summary/axis/slot 文字和 Claim refs 构造候选，再应用以下字段和规则。字段缺失、类型不对或值不在枚举内，整个候选为 `blocked`，不能进入 Reader：

```json
{
  "unit_id": "ku-...",
  "statement": "8 到 800 个字符的业务表述",
  "claim_ids": ["clm-<sha256(task5-claim-id.v1)>"],
  "support_spans": {
    "claim-...": [{"start_char": 0, "end_char": 24, "text": "原文中的连续片段", "span_kind": "source_fragment"}]
  },
  "scope": "selected-source-closure",
  "semantic_status": "supported",
  "polarity": "affirmed",
  "conflict_status": "none",
  "raw_copy_status": "not_copy",
  "verification_method": "semantic-frame-field-closure-v1",
  "relation_sensitivity": "none",
  "relation_facts": []
}
```

`bounded-lexical-v1` 的实现表和索引规则在本 revision 固定，不允许由模型或环境变量改写：先对原文和 statement 做 Unicode NFKC、小写和连续空白折叠；按以下优先级扫描 token，并保留原始字符区间：`URL = https?://` 后接至空白/中文标点的连续串；`VERSION = v?数字(.数字){1,3}[-+字母数字.-]*`；`PROTECTED_ID = 含 `/`、`.`、`_`、`:`、`=`、`@`、`%`、`?`、`&`、`~`、`#`、`-` 的 ASCII 串，或以 `/`、`$`、`--` 开头的串；`NUMBER = 数字串，可带小数点和 %/ms/s`；`ASCII_WORD = ASCII 字母开头、后接字母/数字/_/-`；Han 字符逐字一个 token；其余标点只做分隔符。protected token 只包括 URL、VERSION、PROTECTED_ID 和 NUMBER，按 NFKC 后的大小写不敏感多重集逐项比较。固定泛词表为：`产品、系统、功能、模块、页面、配置、设备、用户、数据、信息、内容、问题、说明、相关、支持、使用、查看、设置、操作、处理、当前、默认、可以、需要、包括、实现、方式、结果、原因、步骤、场景、范围、对象、边界、服务、能力、规则、状态、入口、流程、资料、文档`；泛词表 hash、tokenizer 名称和版本写入 provider receipt。字符 offset 是 Python Unicode code-point index，不是 UTF-8 byte offset；`text` 必须与当前 Claim 原文切片逐字相等。

模型未稳定返回有效 `support_spans` 时允许记录 `claim-lineage-v1` 诊断，但不能把它当作 Reader 语义证明：`support_spans` 绝不能缺失或为空对象。该方法必须为每个 `claim_id` 写入一个非空、覆盖该 Claim 全文的显式 span（`start_char=0`、`end_char=Claim Unicode code-point 长度`、`text=Claim 全文`、`span_kind=claim_full`），保留该 Claim 的 block/hash/locator；它只能帮助 Audit 回查，不能单独让 semantic status 变成 supported。Reader 必须使用 `semantic-frame-field-closure-v1` 逐字段校验；`bounded-lexical-v1` 和 `claim-lineage-v1` 的结果只作诊断，选择、拒绝原因和结果 hash 都必须可复算。

这不是“证明任意自然语言蕴含”的模型裁决，而是一个保守的、可执行的 bounded-evidence 判定：无法通过规则的自然语言改写一律 `unknown`，不为了提高覆盖率放宽为 supported。接受规则是确定性的：

1. `claim_ids` 必须唯一、全部属于本次 provider input 的 canonical Claim ID；fixture 的 case-local ref 只能通过冻结 mapping 解析，不能直接当作 Claim ID。每个 Claim 必须为 `supported`，owner path 必须在 selected-source-closure，且 block id、content hash、block content hash 和 locator 均匹配当前快照。
2. `support_spans` 必须对每个 `claim_id` 非空且逐项覆盖：`bounded-lexical-v1` 的每个 span 必须是对应 Claim 文本的精确 Unicode 字符区间，`text` 必须与该区间逐字相等且非空；`claim-lineage-v1` 必须使用上面的显式 `claim_full` span。两种诊断方法都使用上面冻结的 tokenizer 和泛词表；去掉泛词后计算 statement 内容 token 覆盖率和支持片段锚点，但该覆盖率只写入诊断指标，不能作为 Reader acceptance 或 `semantic_status=supported` 的充分条件。空 span、只给 claim_id 不给 span、只给泛词或 span/Claim 不一致都为 `unknown`，不能进入 Reader；Reader 必须另行通过每个 concrete frame field 的逐字段闭合。
3. 代码从每个 support span 计算 `source_payload`，从 statement 计算 `statement_payload`；payload 至少包括非泛锚点、protected token、主体/客体/动作 tuple、顺序、数量/比较符、条件范围和 polarity。必须同时满足：所有 source payload 的安全字段（主体、客体、动作、顺序、数量、条件、否定和 protected token）在 statement payload 中逐项闭合；statement 不得新增 source closure 没有的非泛锚点、动作、数量、条件、主体/客体或 protected token；允许的同义表达只能来自冻结 `atom_forms`，否则为 `unknown`。若一个 Claim 含多个不可共同概括的事实，必须拆成多个 KnowledgeUnit；不能用一个空/整条 Claim lineage 免除双向 payload 检查。
4. `relation_sensitivity` 只有 `none|subject-object|ordered|quantified|conditional|mixed`。当 source Claim 或派生 statement 含主体/客体、动作、顺序、数量/比较或条件 cue 时，不能声明 `none`；关系事实由代码从 source Claim 和派生 statement 计算，不能把模型自报的 `relation_facts` 当作证明。代码逐字段检查：主体/客体/动作锚点必须是 source support span 的精确或 NFKC 等价片段，主体与客体不能互换，动作方向不能反转，`order_index` 不能重排，数量值/单位/比较符/量词必须相等，条件 cue 和其作用范围必须保持；无法对齐任何一个字段即 `unknown`。`claim-lineage-v1` 只解决 Claim 全文回查，不豁免这条关系/范围检查。
5. `statement` 必须是 8–800 个字符的短表述，不能等于任何单个 Claim 或连续原文片段；规范化后的 statement 与任一单 Claim 的 `SequenceMatcher` 相似度达到 `0.90` 或以上，或 statement 是 Claim 的连续片段时，`raw_copy_status` 必须是 `copy`，该 unit 失败。数字、版本、URL、路径、命令和配置 key 属于 protected token，必须在 support span 和 statement 中逐项相等；新增 protected token 直接失败。

页面还必须做独立的 `page-rewrite-gate.v1`，输入只能是最终渲染后的 Reader 正文（summary、axis 可见值和 sections），排除导航、标题、slot 标签、`audit_ref` 和内部元数据。gate 必须生成 `page_surface_sha256`、`source_closure_sha256`、`rendered_claim_ids`、`source_claim_ids`、distinct Claim coverage、source/Reader Claim ID 的 LCS 顺序覆盖率和 `bounded-lexical-v1` 诊断指标。对 `source-digest` 固定 `max_reader_body_chars=4800`、`max_reader_sentence_count=24`；当 source Claim 数不少于 8 时，distinct Claim 覆盖率不得超过 `0.75`，且正文句子与单个 Claim 的一对一高相似改写比例不得超过 `0.60`。高覆盖、source 顺序高度一致（LCS 覆盖率 `>=0.75`）且一对一比例同时超限时，状态为 `page_semantic_rewrite`；完整 source closure 被逐条改写时状态为 `whole_source_semantic_rewrite` 或 `one_to_one_claim_rewrite`。短来源仍执行长度、句数、raw-copy 和一对一检查，但不使用高分母比例阈值制造误报。`bounded-lexical-v1`、Claim coverage 和 LCS 只用于发现疑似重写，不能替代 `semantic-frame-field-closure-v1` 的逐字段等价，也不能单独生成 `supported` 或 `KD_WIN`。`copy|unknown` 都不能生成 Reader，projection 只能进入 Audit-only/blocked，不能产生 `KD_WIN`。
6. `semantic_status` 只有等于 `supported` 且 `verification_method=semantic-frame-field-closure-v1`、每个 concrete frame field 与 source frame 逐项等价时才能进入 Reader；`bounded-lexical-v1` 和 `claim-lineage-v1` 只能作为诊断证据，不能单独放行。`unsupported`、`ambiguous`、`unknown`、`blocked` 都只能进入 Audit。`polarity` 必须是 `affirmed|negated|conditional|unknown`，`conflict_status` 必须是 `none|resolved|unresolved`，`raw_copy_status` 必须是 `not_copy|copy`。实现用固定否定 cue（`不/不能/无法/不可/禁止/未/无`）和条件 cue（`如果/当/仅当/取决于/可能`）对 support span 或 Claim 全文与 statement 做同一规则分类；同时出现互斥 cue 或分类不一致就是 `unknown`。
7. Claim 的否定/条件范围必须与 unit 一致：引用否定 Claim 时，affirmed unit 失败；引用 conditional Claim 时，unit 必须为 conditional；任一引用 Claim 有未解决冲突、unknown polarity 或与 unit 极性不一致时，unit 失败。不得通过把否定句中的原子词复制到正文来得分。
8. unit 的每个 `claim_id`、`support_span`、relation fact、polarity、verification method 和 conflict 状态必须写入对应 surface 的 Audit/render ledger；正文表面由编译器绑定派生的 `knowledge_unit_ids`，不是要求 Qwen 在 v2 JSON 中返回它们。只要一个必答 atom 没有通过该谓词，整个 projection 的该维度就是 `UNKNOWN`/blocked，结构分不能补齐。

#### 11.1.2 Relation cue vocabulary and detection order

relation-cues-v1 是代码和测试共同使用的固定词表，模型不能自行扩展或把 relation_sensitivity=none 当作绕过开关。扫描先做 NFKC、小写、连续空白折叠，再按“多词模板优先、同长度按词表顺序、从左到右”匹配；命中任一 cue 时，代码派生的最低敏感度必须覆盖当前页面的派生关系结果，关系事实缺失即 unknown。

- **subject/object/action**：属于、负责、管理、拥有、针对、适用于、分配给、绑定到、注册到、推送到、从...迁移到...、由...创建、由...删除、启用、停用、激活、禁用、回滚、belongs to、manages、owns、applies to、assigned to、bound to、registered to、pushed to、migrate from/to、created by、deleted by、enable、disable、activate、rollback。主体和客体取 cue 两侧最近的非泛词 span；方向按 source support span 的 tuple 保存，不能交换。
- **ordered**：第...步、首先、先、然后、接着、最后、之前、之后、顺序、依次、step、first、then、next、finally、before、after、in order，以及 1./2.、①/②、→。顺序按 source locator 和显式序号同时校验，无法唯一排序即 unknown。
- **quantified**：数字、版本、百分号、时间/容量单位，以及 至少、至多、最多、不超过、超过、不少于、少于、大于、小于、等于、仅一个、only、at least、at most、no more than、greater than、less than、equal to。比较符、数值、单位和量词是一个不可拆 tuple，任何一项变化都失败。
- **conditional**：如果、若、当、仅当、除非、否则、在...时、取决于、可能、if、when、only if、unless、otherwise、depends on、may。条件 cue 到其结论的最小稳定 span 作为 condition_scope；scope 缩窄、扩大、丢失或把条件改成无条件都失败。

检测算法固定为：先扫描 source Claim 和 statement 的上述 cue、protected token、数字/单位；再要求 source 与 statement 的 relation tuple 集合逐项对齐。source 或 statement 命中 subject/object/action、ordered、quantified、conditional 任一类别时，none 不合法；编译器派生的 relation ledger 必须保存精确/NFKC 等价的 subject、predicate、object 和对应 evidence spans，且 order/quantity/condition 字段按类别必填。`relation_facts` 只允许作为编译器内部派生字段，不是 Qwen response 字段，也不是模型自报证明；代码不把模型自报的 relation_sensitivity 当事实，claim-lineage 也不能跳过 scanner。

#### 11.1.3 relation-parser-v1 deterministic boundary

关系解析不是把 cue 表交给模型自由解释，而是固定为 `relation-parser-v1`：

1. **文本与 offset**：输入先按 raw snapshot 规则做 UTF-8、CRLF/CR→LF、Unicode NFKC，关系 token 的 offset 使用该 canonical text 的 Unicode code-point 半开区间 `[start,end)`；每个 span 必须能用同一 canonical text 切片回查，无法建立一一映射或跨行归一导致边界不确定时记 `unknown`。禁止用 UTF-16、byte offset 或模型返回的未经校验 offset。
2. **token 边界**：连续 ASCII 字母/数字与单位作为一个 token；汉字按 code point token 化，但连续的实体候选 span 以非标点、非 cue、非泛词的最长连续片段为边界；数字、版本、百分比、容量/时间单位及比较符组成不可拆 `protected_numeric` token；URL、文件路径、Markdown link destination、代码 fence、inline code 和 HTML 标签整体作为 `protected_opaque`，默认不参与自然语言关系解析。
3. **结构块**：普通段落和列表项按正文解析；表格按“表头 + 当前行 + 当前单元格”组成局部上下文，每个关系只能引用同一行或明确表头，跨行/跨列没有唯一归属就 `unknown`；代码、链接目标、图片 alt、frontmatter、Audit marker 和生成元数据不作为自然语言关系来源，除非 parser 输入带有显式 `structured_claim` 类型和结构化字段，否则只保留原文 locator、不给 `supported` 关系。
4. **候选与优先级**：先找受保护 token 和 cue 的 canonical span，再按条件/否定 scope → 显式 predicate cue → ordered/quantified cue → subject/object 最近非泛词候选的顺序解析。一个 predicate 对应多个同距 subject/object、一个 condition cue 覆盖多个结论、多个 cue 产生相反方向，或表格归属不唯一时不猜最近词，直接 `ambiguous_relation`。同一 Claim 内显式否定/条件范围优先于肯定词；冲突无法在 Claim locator 内消解时为 `conflict_unresolved`。
5. **scope 与关系 tuple**：`condition_scope` 是从 condition cue 到同句结论边界、分号/列表项边界或显式 otherwise/否则边界的最小稳定 span；不能唯一确定结论边界、条件被扩大/缩小或条件 cue 没有结论时 `unknown_condition_scope`。subject/object/action 按 cue 两侧最近但唯一的候选 span 固定；如果只剩泛词、同距并列或需要跨结构块拼接则 `unknown_subject|unknown_object|unknown_action`。ordered 只接受显式序号/顺序 cue 与 locator 顺序同时一致，无法唯一排序则 `unknown_order`；quantity 把比较符、数值、单位和量词作为一个 tuple，任何缺项或不一致则 `unknown_quantity`。
6. **分流**：任一关系类别为 `unknown|ambiguous_relation|unknown_condition_scope|conflict_unresolved`，KnowledgeUnit 不得标 `supported`，Reader surface 不得生成，Audit 必须记录 parser version、block kind、candidate spans、冲突原因和 locator；只有全部适用关系 tuple 唯一闭合且 source/statement 双向一致，才允许 `semantic_status=supported`。该分流对 quality-reader 和 source-direct-audit 都适用，source-direct 仍额外服从 claim-fragment contract。

M253-R/M253 的最小测试矩阵必须覆盖：同一句多 predicate、多 subject/object 同距、否定与条件重叠、表格同列/跨列、列表项顺序、代码/链接/图片块、URL/路径/版本 protected token、条件边界、跨行关系、主体客体方向和无法唯一解析；所有歧义都必须得到 Audit-only/UNKNOWN，不能靠分数或模型自报关系放行。
最低负例集合固定为：有精确 support span 的合法改写通过；claim-lineage 全文回查的合法短表述通过；错误 Unicode offset、正文命中但引用无关 Claim、跨来源 Claim、主体/客体互换、动作方向反转、步骤顺序重排、数量/比较符/量词变化、条件范围缩窄或扩大、否定/条件被改写成肯定、未解决冲突、只有泛词重叠、protected token 新增、整段原文复制、每个 Claim 单独通过但整页覆盖全部 Claim、整页按 source 顺序逐条语义改写和短来源低分母边界分别失败或按合同保留。测试必须断言这些失败不生成 Reader、不产生 `KD_WIN`，并保留 `Audit.reason`、页面级 rewrite gate 指标、关系校验结果和输入 Claim refs。

### 11.2 全量 89 条逐源路由不能靠文件名猜

source-digest 的 manifest route 不是语义证据。D0/R2 先生成 89 条 source-scope ledger，确认每条来源的 source id、快照、内容 hash、Block/Claim 闭包、空源/重复状态和 provider route；这一步不要求原文预先写出 question、page_type 或五轴标签。87 个普通来源都必须进入一次单源 Qwen 请求；Qwen typed output 必须返回页面类型、产品/模块/对象/场景/边界、summary、sections 和 Claim refs，之后由 `source-digest-route-verifier.v1` 从当前 Claim/frame/locator 逐字段重算并校验。字段无支持、主意图多解、关系不闭合、locator 过期或 output/ledger 漂移时，当前来源只能 Audit-only，不能生成 Reader/quality/publication；但不能因为 D0 没有显式 metadata 就提前把 Qwen 请求删掉。原始目录顶层只允许作为结构性产品归属，文件名只允许作为显示标题候选；两者都不能证明对象、场景、边界或答案事实。只有 post-provider route closure 达到 87/87，且五维严格比较全部 `KD_WIN`，才可 `released`。

`config/task5-source-page-manifest-v2.json` 是 89 条逐源闭包唯一 authority（完整 actual/canonical SHA 见 AC-001）。每个 path 只有一个 `SRC-*` case 和 coverage/Audit closure；known_empty 只 Audit，duplicate alias 不重复请求；SND 命中时替换同一 entry 的 source-digest projection，不增加 provider request、Reader 或 coverage row。显式 source-direct-audit 仍 Audit-only；运行前必须校验 89/path/source id/snapshot/hash/status，歧义或失败只 Audit。

来源与投影不是一对一限制：每个 canonical source 至少有一个逐源 coverage projection；普通来源是 source-digest，`source_not_documented` 来源是其替换 projection；duplicate alias 保留自己的 inventory/Claim/Audit link，但继承 canonical Reader link，不重复生成页面；一个 source 可以被多个 QualityCase projection 复用。普通 canonical source-digest 成功或 SND replacement 在扫描和语义零匹配证书都闭合时可进入 Reader，但仍必须有冻结 question、page_type、单源 closure/扫描证据、lineage、Reader/Audit 和 RenderLedger；证书缺失的 SND 只能 Audit-only。QualityCase projection 另必须有实际 embedding selected paths 和五维质量门。显式 source-direct-audit 永不进入 Reader；Q-OPR/Q-BND 的多 projection 不得被单个 source-digest 页面代替。

每个 source case 的必答内容是标题、bounded semantic summary、适用范围、source-backed claims 和 Audit 可回查关系；canonical source-digest 成功或 SND replacement 成功才写业务 Reader，alias/known_empty/provider failure 只写 Audit。显式 source-direct 的 KnowledgeUnit 和 summary 必须按 `task5-source-direct-contract.v1` 的 `claim-fragment-lineage-v1` 校验：只允许 NFKC、空白/标点归一、保持句界的压缩和显式 Claim 片段拼接，不依赖 QualityCase 的 `atom_forms`，也不能自行发明同义词、跨源事实或扩大条件范围。任何 summary 句子没有 KnowledgeUnit 回指、unit 没有非空 support span、Claim 不属于该单一 source closure、关系/否定/条件变化、整篇原文复制或出现来源外事实，都只能生成 `Audit.reason=source_direct_contract_rejected` 的失败 Audit，不能生成“原文整理版” Reader。source-digest 同样不得绕过 typed semantic/page contract；清单本身不是业务知识，不得把字段存在当作内容质量通过。

`source-digest` 独立绑定 `task5-source-digest-reader-v2`（`config/task5-source-digest-contract-v2.json`，contract hash 以当前 runtime authority map 重算值为准）和 `task5-semantic-frame.v1`。它采用两阶段 route：第一阶段是 provider-free `source-scope-producer.v1`，在 Source→Block→Claim 和 raw-coordinate-map 完成后只确认 89 条来源的 identity、可读性、单源边界、Block/Claim closure、空源/重复源状态；它不要求原文先显式写出 question、page type 或五轴，也不把文件名/目录/段落位置当作业务事实。第二阶段由 Qwen 对每条可读普通来源生成 typed question、title、page type 和 product/module/object/scene/boundary，随后由 `source-digest-route-verifier.v1` 逐字段绑定当前 Claim/frame/locator、source/block/claim hash、单源 closure 与 `support_sha256`。顶层目录只允许作为结构性 product route，文件名只允许作为显示标题候选；unsupported、ambiguous、stale locator、closure 外事实或 output/ledger 漂移只写 Audit，不能用整篇原文回退。87 个普通来源必须逐条尝试 Qwen，post-provider route closure 少于 87/87 时最终只能 `not_released`；页面正文仍必须通过 Claim lineage、五类 page type、五轴语义、长度/句数/Claim coverage、顺序重合和一对一改写门禁，失败只进 Audit。

### 11.3 五维评分使用结构化原子裁决

`required_atoms` 只用于列出需要回答的概念，不是简单字符串通过开关。每个 atom 的裁决输入必须包含：provider 生成的 semantic unit statement、引用 Claim、Claim 的唯一 source owner/block/locator/hash、实际投影 surface、scope，以及否定词/冲突范围检查。atom 若只在无关 Claim、selected closure 外 Claim、否定句或未被实际 Reader/Audit surface 使用的文本中出现，结果为 `UNKNOWN`，不能由 keyword hit 制造 `KD_WIN`；selected closure 内的多源 Claim 只有在各自 owner 和 `co_support|conflict|unknown` 关系均可回查时才可支持。

评分器只能在 typed evidence、surface、scope 和 negation/conflict gate 通过后，用同一份冻结 `atom_forms[canonical_atom]` 做归一化观察；完整字符串、关键词命中或词形重合本身永远不是支持证明。对 KD 和 CompanyBrain 必须使用同一份冻结 atom forms/等义表达集合；Reader-Audit 另外使用 baseline v2 的共同 evidence-level 梯度，比较双方实际渲染 Markdown 的 provenance marker、locator 和 claim-exact 回查，不奖励 KD 内部 JSON、Audit 文件数量或 RenderLedger 存在。不能证明 CompanyBrain 某个 atom 的等义表达时记 `UNKNOWN`；只有 CompanyBrain baseline 文件缺失、hash 漂移或 applicability 缺失才记 `CB_MISSING`，不能把“未命中当前措辞”当作低分再制造 `KD_WIN`。两侧都只能从实际 hash-bound 文本和同一 forms 集合取证，不能一边使用 Qwen semantic support、一边让另一边只接受原词。

每个 case×dimension 仍独立计算 `content_score`、`structure_score` 和 `kd_score`，但这些分数只作为诊断输出；`KD_WIN` 还必须满足 §10.1.2 的 surface gate、§10.1.3 的 `path_replay.status=pass` 和严格优势 evidence。缺 semantic support、缺 source manifest closure、缺 Reader/Audit、缺对称 atom forms、业务 atom 只在 Audit、任务阶段缺失或有否定/冲突未裁决时必须是 `UNKNOWN`/`not_released`，不能被分数补回。必须有等义改写、误命中、错误顺序和错误语义关系负例：两侧表达同一事实时不得误判为 CB 缺失；只共享词面、顺序错误或语义不等价时不得计分。

评分字段冻结：每个 `projection_key × dimension` 取 `A=applicable required_atoms`、`M=applicable structure_markers`，`c/s` 是允许 Reader surface 上通过的 atom/marker 数；空 A/M 为 `UNKNOWN`。否则 `content_score=round_half_up(100*c/|A|,2)`、`structure_score=round_half_up(100*s/|M|,2)`、`kd_score=round_half_up(0.7*content_score+0.3*structure_score,2)`，CB 同公式、forms、surface 和分母。缺失/forbidden/unsupported/negative/unknown 不缩分母，forbidden 独立失败；Reader-Audit 等级为 `none=0, metadata=20, source-clue=40, archive-reference=60, source-locator=80, claim-exact=100`，双方同判；两位小数相等为 `TIE`，分数仅诊断。

`KD_WIN` 绝不由 `kd_score > cb_score` 单独产生：必须同时满足所有 hard gate、真实 route/path replay、同一维度存在可回查的 CompanyBrain gap、KD 每个 required atom 都有完成证据，并且每个适用 required atom 都有严格的 KD atom-level advantage；分数只能记录和辅助发现问题，不能创造胜出。M253-R/M253 必须覆盖固定分母、空集合 `UNKNOWN`、两位小数 TIE、forbidden 独立失败、证据等级和公式字段被篡改的负例。

### 11.3.1 唯一实际质量结果 artifact

R3 quality evaluator 是质量结果唯一 writer。每次 actual run 先写不可变 candidate attempt `quality/evidence/task5/actual-run/attempts/<attempt_id>/quality-result.json`，状态固定为 `candidate/not_released`，绑定 `candidate_tree_sha256`，且 `published_tree_sha256=null`，不能产生 released verdict。`candidate-surface-qa.v1` 是独立的发布前检查：它只读 candidate bundle、candidate directory manifest/tree 和渲染入口，不读 quality-result，也不等待 quality-result promotion；通过后，只有同一 R3 owner 执行 Downloads 同盘的原子 rename。rename 成功后，R3 新建不可变 `quality-result-finalize` attempt；该 attempt 先读取最终目录 manifest/tree 和 rename/lock receipt，再在同一 attempt 内完成 `published-surface-qa.v1`，重算 `published_tree_sha256`、Reader/Audit/链接/媒体/禁字段和 cleanup，最后按五维/89 条/状态谓词计算最终 `publication_status`，确认 candidate/published 绑定一致，才原子 promotion 到固定 `quality/evidence/task5/actual-run/quality-result.json`。因此 post-rename surface QA 是 finalize 的输入和结果字段，不是 promoted artifact 的下游前置消费者；run-result、release predicate 和最终 manifest 只在 promotion 之后消费该 artifact，不形成回环。

rename 失败、rollback、finalize 失败、最终 tree/manifest 漂移或 candidate/published 不一致时，只保留 candidate/失败 attempt，固定 promotion 不更新、published tree 保持 null、状态为 `not_released`。若 output 已经 rename 成功但 finalize 失败，owner 必须在同一文件系统把仍匹配本次 `owner_nonce + candidate_tree_sha256` 的 output 原子 rename 到 `<output>.failure.<run_id>.<owner_nonce>` failure sink，再把 lock 原子置为 `failed`；若无法证明归属或补偿 rename 失败，锁置为 `publication_ambiguous`，output 和证据都保留、禁止覆盖/删除/再次发布，后续运行只能 blocked 等待人工处理。进程在 rename 与 lock 更新之间崩溃时，恢复器用 lock、output manifest/tree 和 rename receipt 判定 `published_uncommitted` 或 `publication_ambiguous`，不得把目录当作 published，也不得返回 released。candidate artifact、run-result 或任一 surface QA 都不能单独宣布 released。schema=`task5-quality-result-artifact.v1`；artifact 的 `results` 必须恰好覆盖六个 case、八个 projection、五个 dimension，每行包含 `task5-quality-result.v3` 的 projection/dimension、atom、gap、advantage、Reader/Audit、route、RenderLedger、source-closure、path-replay 和 CompanyBrain observation refs+SHA；顶层还必须绑定 quality/baseline/observation contracts、actual candidate bundle ref、candidate/final directory-manifest ref+SHA、candidate/published tree SHA、`strict_all_kd_win` 派生值和 `publication_status`。不写 raw prompt、response 或 key；缺行、重复、错 projection/dimension、任一 ref/hash/tree 漂移即 `UNKNOWN/not_released`。run-result、release predicate 和最终 Downloads manifest 只能消费同一 promoted ref+SHA。

`bundle/_audit/run-result.json`、M402 release predicate 和最终 Downloads directory manifest 只消费这个 promoted artifact 的 ref+SHA；它们不能各自复制或重新计算质量 verdict。candidate-surface-qa 与 published-surface-qa 的 receipt 由 R3 finalize 写入 artifact 的 evidence refs，published-surface-qa 在 promotion 前完成，不再作为 promotion 后的前置条件。artifact 与最终发布树的绑定通过 candidate/published tree SHA、directory-manifest ref+SHA 和 `publication_status` 完成：未发布时保存 candidate tree，发布时两者必须相等；任何不等或 artifact 缺失都不能 `released`。

### 11.4 回滚必须先比对精确快照

`quality/evidence/task5-repair-baseline-v2.json` 是设计前已存在的只读输入，固定 baseline commit `b69e72985338d966ddc0706ffe9e9e56779fd753`、tree `9f55cd64b3b055647d923a9208d802c60a724d78`、`CONTEXT.md` 原始 blob、R1–R4 分闸门路径和本次新增/修改路径及 SHA-256；它不属于实现阶段 ADD。实现阶段新增两层证据：第一层是每次 attempt 的不可变 `repair-gates/attempts/<attempt_id>/{R1,R2,R3,R4}.json`、`tests/{R1,R2,R3,R4}.json`、`inverse/{R1,R2,R3,R4}.patch`；第二层是固定路径的 promotion/index view `repair-gates/R1.json`–`R4.json`、`tests/R1.json`–`R4.json` 和 `inverse/R1.patch`–`R4.patch`。attempt gate receipt 必须符合 `task5-repair-gate-attempt.v1`，记录 `attempt_id`、单调 `attempt_seq`、`status`、`outcome`、before/after snapshot、每条路径 hash、patch_id、canonical test receipt ref、inverse ref 和锁/父版本 hash；attempt test receipt 必须符合 `task5-test-receipt.v1`。固定 gate view 必须符合 `task5-repair-gate-promotion.v1`，只记录 `latest_attempt_ref`、`promoted_attempt_ref`、完整 `attempt_refs`、当前 snapshot/material 和被 promotion 的 receipt/test/inverse hash；只有通过 attempt 才能成为 `promoted_attempt_ref`。失败 attempt 只追加历史，不被改写或删除；若最新 attempt 失败，`latest_attempt_ref != promoted_attempt_ref`，下一 gate 必须 STOP。R3 的 `R3-events.jsonl` 是全局 append-only event log，事件带 `attempt_id`、全局 `sequence` 和 attempt 内 `attempt_event_index`。M401 另固定写 `quality/evidence/task5/M401-evidence-packet.json`，schema=`task5-m401-evidence-packet.v1`，M401-R 只消费该 packet。回滚前逐项复 hash；任何路径被外部修改就停止，不做模糊删除。只允许按 `rollback_matrix` 恢复仍与 manifest 相同的 ADD/MODIFY 代码、示例配置、测试和 ADR 路径；`CONTEXT.md` 是 read-only identity input，永不修改、恢复或纳入 rollback target。raw corpus、CompanyBrain、旧 Task4/Task5 产物、Downloads 输出和审查证据永不删除或覆盖。任何实现边界变化都必须新建快照并重新 review。

attempt evidence、promotion/index view、R3 event log 和 M401 packet 都是实现阶段新增的 append-only 证据产品，不属于 rollback target：attempt 文件一经写入不能改写；promotion view 只能以原子追加方式记录新 attempt，不得删除历史或把失败记录改成通过；每个 gate 的 test receipt 以该 gate `after_snapshot_tree` 为本地绑定，M401 只要求验证 R1→R4 的 snapshot chain 最终汇聚到 packet 的当前 snapshot，不要求历史 R1 receipt 与 M401 最终 tree 相同。`CONTEXT.md` 不参与回滚。

#### 11.4.1 输出路径安全和新目录合同

provider-required 运行必须在创建 staging、锁文件或任何候选内容之前完成输出路径 preflight。系统解析 `raw_input`、CompanyBrain 和 `--output` 的 realpath，并拒绝以下情况：输出是软链接；输出与 raw/CompanyBrain 相同；输出是任一输入的子目录或父目录；输出与历史候选目录相同；输出路径包含 `..` 逃逸；输出目录已存在（即使为空）。只有目标 output 不存在、其 Downloads 父目录真实存在且安全时才允许继续；任何既有 output、锁或临时目录都必须 `blocked`，不得清空、覆盖、接管或删除。

`--output` 必须是用户明确指定的 Downloads 下新目录；staging 固定为 `<output>.staging.<run_id>.<owner_nonce>`，位于 output 的 Downloads 同级且与 Downloads 同一文件系统，禁止把 `/tmp` staging 直接 rename 到 Downloads；`/tmp` 仅可放不参与发布的诊断缓存。preflight 必须同时校验 staging parent 的 realpath、同文件系统设备号和命名约束；外部 staging、跨设备 staging 或 `/tmp` staging 都是 blocked。preflight 失败先按 `task5-preflight-result.v1` 写 repository evidence root；只有 output/staging 已存在时，才把脱敏 Audit/failure evidence 写入对应 sink。如果连输出目录都不能安全创建，不能为了写报告而创建不安全目录，只返回已绑定的 preflight receipt 和进程结果。路径比较使用 realpath，不使用字符串前缀；每个安全判定记录 `raw_realpath`、`companybrain_realpath`、`output_realpath`、`staging_realpath`、`downloads_root`、`same_filesystem`、`output_exists`、`output_is_symlink`、`overlap_check` 和阻断原因。

测试必须覆盖输出为 raw 目录、CompanyBrain 目录、输入子目录、输入父目录、软链接、既有非空候选和 Downloads 外路径；所有负例都要断言没有写入输入、没有清空既有输出、没有 provider call。新空目录的创建只能发生在这些检查全部通过之后。

输出安全 receipt 的 realpath 字段是 host-only；public bundle 只写 relative path、source_id 和 hash。发布前扫描 `bundle/`，命中绝对路径、用户名、staging、WorkflowHub 路径或 host receipt 即阻断。

#### 11.4.2 Downloads atomic publication lock

输出安全还必须有一个可验证的运行锁，不允许依赖“目录看起来是新的”来处理并发或崩溃：

- preflight 先固定 `downloads_root=realpath('/Users/Hugh/Downloads')`，要求 `output_realpath` 是该 root 的新建直接子目录；raw、CompanyBrain、output 和 staging 的 realpath 不能重叠。`run_id`、`material_id`、`owner_nonce` 在首个 provider 请求前生成并冻结。
- 锁路径固定为 output 的同级 sidecar `<output>.task5.lock`；锁文件使用 `O_CREAT|O_EXCL` 独占创建，schema=`task5-output-lock.v1`，必填 `task_id`、`run_id`、`material_id`、`owner_nonce`、`pid`、`host`、`created_at`、`output_path`、`output_realpath`、`staging_path`、`failure_evidence_path`、`failure_evidence_sha256`、`retention`、`state`。held/published 时 failure fields 可为 null；failed/cancelled 时必须指向持久化 sink。锁中不得写 API key、Authorization 或完整 prompt。
- 只有持有相同 `owner_nonce` 的进程能创建 `<output>.staging.<run_id>.<owner_nonce>`、写 candidate、更新锁状态和执行最终 rename；同一 output 的第二个进程即使看到锁持有者已经退出，也只能 `blocked`，不能抢锁、删除锁、复用 staging 或发 provider 请求。
- 锁状态只能按 `held → rename_committed → finalizing → published` 或 `held → failed|cancelled|publication_ambiguous` 单向转换；`published` 只有 quality-result finalize 已 promotion 后才允许。构建期间所有文件先写 Downloads 同级、同文件系统的 staging，逐文件 fsync、再 fsync staging 目录；只有锁仍归属本次 owner 且 output 不存在时，才用一次目录级 atomic rename 将 staging 发布为 output，写入不可变 rename receipt，随后进入 `rename_committed`/`finalizing`，不先把锁标成 published。rename 前崩溃不会产生 Reader；rename 后锁尚未更新的崩溃由恢复器按 output/tree/rename receipt 判为 `published_uncommitted` 或 `publication_ambiguous`，后续运行停止，绝不覆盖。
- candidate surface QA 通过后，owner 才执行 rename；finalize 失败时，若 output 仍与 owner/tree/manifest 精确匹配，必须原子移入同盘 failure sink 并把锁置 `failed`，同时保留 candidate/finalize attempt；若归属或补偿 rename 无法证明，锁置 `publication_ambiguous`，output、lock、attempt 和 failure evidence 全部保留，不自动删除、接管或再次发布。rename/rollback/finalize 任一失败都不能写 released artifact。
- 失败/取消由 owner 先把完整 staging 或已 quarantine 的 output 原子 rename 到持久化 failure evidence sink，再把锁原子更新为 `failed`/`cancelled`，记录 reason、sink/staging/output hash、rename receipt 和 cleanup result。进程被 kill 或机器崩溃时不自动清理 staging、output 或 lock；后续运行把仍存在的 `held`/`finalizing`/`publication_ambiguous` 锁按 `active_or_stale_lock` fail-closed，保留 owner/run/material 身份，等待人工检查，不在本 revision 自动接管或删除。
- 锁 sidecar、状态转换、staging/output realpath、rename 前后快照和 owner 结果都进入 Audit/发布 receipt；并发竞争必须证明恰好一个 owner 获得锁，另一个没有 provider call、没有写 output、没有清理对方 staging。锁存在、output 已存在、owner 不匹配或状态不一致都不能被“重试”掩盖。

#### 11.4.3 Failure evidence sink

`bundle/Audit` 是用户回查入口，只保存 Claim/source/block identity、snapshot/content/block hash、相对 locator、closure 和 `audit_ref`，不复制 raw source。failure sink 是另一份安全索引；失败/取消时将脱敏 staging 原子 rename 到 Downloads failure sink，不能冒充 output。

`task5-failure-evidence.v1` 只允许状态/reason、run/material/request/provider identity、calls/exit、ledger/Audit ref+hash、source_id/block_id/content hash、相对 locator、cleanup result；禁止 raw source/block、prompt、response、Authorization/key、host path 和自由文本。Audit 未落盘时 `audit_ref=null`。rename 前扫描全 staging/manifest，命中或未声明字段则保留 staging；rename 失败、崩溃和 held lock 都 fail-closed，保留 hash/locator，不自动清理。

### 11.5 当前冻结 fixture 的可核验摘要

以下摘要是审查和实现前置的闭包，不替代 fixture 原始字节；实现必须同时读取并 hash 校验 fixture，摘要不一致即 blocked：

本表的 `源数` 专指冻结 `config/task5-quality-cases-v2.json` 实际字节中该 case 的 `source_paths` 去重数量，`投影数` 专指该 case 的 `projections` 数量；它不是旧叙述、旧 v1 fixture 或 §10.3.1 历史示例中的 source block 数。§10.3.1 中用于解释背景的旧 source path 叙述不具执行权威；当文字叙述与 v2 实际字节冲突时，v2 文件的 schema、hash 和字段值优先，loader 必须按 v2 重算并拒绝过期摘要。实现前置应记录六个 case 的实际计数：POS 6/1、CON 2/1、OPR 2/2、DIA 7/1、EXP 5/1、BND 3/2。

| fixture | 必须存在的字段/数量 | 已冻结闭包 |
| --- | --- | --- |
| quality cases v2 | 6 cases；question/axis/source_paths/page_type(s)/rubric | `源数/投影数`=去重 source_paths 数/该 case projection 数；POS 6/1；CON 2/1；OPR 2/2；DIA 7/1；EXP 5/1；BND 3/2 |
| rubric v2 | 五维各 required_atoms/atom_forms/structure_markers/forbidden_atoms | 每 case 正文原子 3/5/5/3/2 或 3；无静态答案/verdict/score |
| projection set | 每 projection 独立 question/page_type/receipt/Reader/Audit/RenderLedger | OPR=`operation` + subtype；BND=`operation`,`diagnosis`；其余各 1 |
| baseline v2 | baseline_id/case_ids/path/snapshot_id/content_hash/locator/applicability/audit_observation | POS/DIA/EXP/BND 各 2 条；CON/OPR 各 1 条；只读实际文件 |
| source manifest v2 | 89 entries；case_id/source_id/source_path/title/question/page_type/route/lineage/oracle | manifest route label 分布（含 known_empty）：operation 45、concept 33、diagnosis 4、positioning 4、experience 3；当前 88 个 present Reader 分布为 operation 44、concept 33、diagnosis 4、positioning 4、experience 3；path digest=`7484673e…cb6a51` |

每个 rubric dimension 的 `atom_forms` 必须是 canonical atom 到一组显式、可审查的等义表达；空集合、只含泛词或只含实现者临时生成的词形都不合格。source manifest 顶层 `projection_policy.source_digest` 固定普通 present entry 的 route 是 source-digest，`source_direct_audit` 只用于显式审计；quality case 的实际 embedding route 另由 route ledger 证明，不能从 manifest 预填 selected 结果。每个 projection 的 oracle 固定为：成功 Reader route 要有 Reader 文件，所有 route 都要有 Audit 文件、RenderLedger 行、provider receipt、Claim/block/hash/locator，且互相绑定；缺一项就是 Audit-only/UNKNOWN。

### 2026-08-25 evaluator correction contract

质量比较器必须区分三件事：CompanyBrain 的自然语义是否存在、CompanyBrain 是否展示了本维度要求的 Reader 表面、当前证据是否足以断言缺失。完整且哈希绑定的 CompanyBrain 快照才允许把 source-bound stage 的缺失标为 `absent`；不完整快照只能是 `unknown`。taxonomy 的 `meaning_status` 保留自然语义，taxonomy `status` 另要求 Reader 正文有紧凑的产品/模块/对象/场景/边界五轴表面，不能用偶然出现的词代替。

business-answer 的 positioning/concept 页必须有直接回答问题的答案句；“本页用于……”只能算导航目的，不算答案。Q-POS/Q-CON 的 `decision`/`direct_answer` 由实际摘要、问题/轴上下文和 Claim closure 共同验证。CompanyBrain source-bound stage 只在同一可见行/句中出现足够的非泛化 Claim token 才算等义，禁止用跨页面泛词拼接出缺失能力。embedding 质量门还必须消费 live `OpenAIEmbeddingClient` 的成功 HTTP batch 计数；只有 provider identity、transport mode、计数和 route ledger 同时闭合才可通过。

本修正只改变 evaluator 的可证伪观察规则，不把历史 r31 结果升级为 released；新的真实运行、五维 verdict、独立 review 和 WorkflowHub authenticated handoff 仍是独立门禁。

## Repair revision v3：极简生产编译链（2026-08-31）

本节是对实现结构的最新约束；不改变原始输入、五项质量目标、89 条全量、垂直切片和 fail-closed 规则。若前文把旧 Task5 runtime、多个 machine writer 或 renderer 语义重生成描述为可运行路径，以本节为准。

生产唯一写入链为 `digest → compiler.digest → providers → publisher.commit`。生产只保留三个深模块：`compiler`、`providers`、`publisher`。语义事实只由 `Evidence` 和 `ReaderPage` 承载；`RunManifest` 只是 89 条来源、页面、路由、失败和最终字节的闭包索引，不生成事实或正文。`Home.md`、Reader 页面、`Audit.md` 和 `_digest/{run.json,evidence.jsonl,sources.jsonl}` 必须从同一个 `CompiledBundle` 一次派生，不能由旧 writer 或质量脚本另行拼接。

`RunManifest` 的唯一 schema 为 `knowledge-digest-run-manifest.v1`，顶层字段集恰好为 `schema_version`、`source_count`、`sources`、`routes`、`pages`、`tree_sha256`；`run-result.json` 只在顶层字段 `manifest` 内嵌这一对象，不在别处复制或改写。`sources`、`routes`、`pages` 的行 schema 分别沿用本节已声明的 `knowledge-digest-source-row.v1`、`knowledge-digest-route-ledger.v1` 和 page row 固定字段；三组数组的顺序由各自 identity 的 UTF-8 bytes 升序确定，`source_count` 必须等于 `sources` 长度且为本次输入 89 条。`tree_sha256` 是公开 bundle 声明文件集合的 tree hash，不把 `manifest` 自身另行纳入。`run-result.receipt.json.manifest_sha256` 必须等于 `manifest` 对象按本合同 canonical UTF-8 JSON+LF 序列化后的完整字节 SHA-256；它不能只 hash sources、routes 或文件名列表。
`knowledge-digest-page-row.v1` 是 `RunManifest.pages` 的唯一行 schema，字段集恰好为 `page_id`、`page_key`、`page_type`、`axes`、`source_ids`、`path`、`surface_sha256`；`axes` 恰好包含 `product`、`module`、`object`、`scenario`、`boundary` 五个字符串，`source_ids` 按 source id UTF-8 bytes 升序且必须非空，`surface_sha256` 是该 Reader Markdown 文件完整 UTF-8 bytes 的 SHA-256。每个 Reader 页的 `path` 唯一按如下规则生成：`axes.product` 归一化为 `emm-for-android|emm-for-ios|goinsight|merchant-system`，跨产品 selected closure 才用 `shared`，未知值按 Unicode 小写后保留字母数字、空格、`-`、`_`、`·`，把 `&` 替换为 `and`、斜杠替换为空格、连续空格/`_`/`·` 合并为 `-`、去掉首尾 `-`、最多 100 个 Unicode code point，空值为 `general`；`page_type` 使用五个固定英文值之一，`title` 用同一 slug 规则生成 filename，最终拼接为 `products/<product_key>/<page_type>/<filename>.md`。同一 `(product_key,page_type,filename)` 冲突按 `(product_key,title,page_id)` UTF-8 bytes 升序，从第二项起追加 `-2`、`-3`；path 和 `pages` 数组（按 `page_id` UTF-8 bytes 升序）均不依赖输入或模型顺序。`Home.md` 不属于 `pages`，Home.route 仍固定为 `bundle/Home.md`。

Qwen 必须返回版本化 typed JSON：`page_key`、问题/场景、页面类型、五轴、summary、sections 和带 Evidence ID 的 answer units 均为必填；未知字段、缺字段、证据错绑、否定/条件/数值改变、整段原文复制均拒绝。Jina 的 selected source/page closure 必须同时出现在路由收据、Qwen 实际输入、ReaderPage source closure 和 Home route；只记录 Jina 调用不算消费。Renderer 只能排版、分页、链接和锚点，不得写业务句子、缺失标签、案例模板或 overlay；provider 输出失败即 Audit-only/not_released，生产链不做隐藏语义重生成。

页面身份固定为 `source:<source_id>` 或 `answer:<question_id>:<page_type>`；可读文件名只作显示名，同名按稳定 page key 加后缀。来源 `ready/blank/duplicate_alias/failed/unsupported` 五类终态全部进入 RunManifest，blank/failed/unsupported 不进入 Home/Reader，不用空页或 raw-copy 伪装成功；duplicate alias 必须保留自身 Audit 闭包并绑定 canonical Reader。

实现完成的必要证明是：真实 CLI 只 import 新 compiler/providers/publisher；固定 Adapter 能观察 Jina 选中的 closure 进入 Qwen 输入；一个 source page 和一个跨来源 answer page 的 Reader/Audit golden test 通过；非法 provider 输出和旧模块 import 负例 fail-closed；然后同一命令完成切片和 89 条全量。任何五项不是逐 projection `KD_WIN`、来源闭包不完整、Reader/Audit 不可回查、独立审查未绑定同一候选树，均不得 `released`。
