# Task5 当前生效实施计划 v4.7（2026-09-04）

> 只有本节生效：从文件开头到本文件末尾的唯一归档分隔线之前全部属于当前合同；归档分隔线及其后全部内容是历史资料，不再授权执行。

## 当前修订 v4.7（2026-09-04）：页面、状态和 fixture 身份的最小闭合方案

血缘计算采用唯一口径：精确为 `原始资料未明确` 且无 evidence 的 section 同时产生 `Reader.section` 和 `Reader.answer_body` 两行 Audit ledger；两行都是保守缺口，占位行计入 `unknown_units`，不伪造 raw binding，也不计入 `rendered_units`/`lineage_coverage` 分母。其余事实 unit 必须 100% 绑定。

M401 的唯一 promotion view 是 `quality/evidence/task5/M401-evidence-packet.json`，只原样提升 `.../attempts/<m401_attempt_id>/M401/M401-evidence-packet.json` 的 source bytes/hash；M401-R 的 `m401_packet_ref` 必须指向该 attempt-local packet，不能指向 promotion view 或 bundle。

M401-R receipt 的 `source_receipt_ref/source_receipt_sha256` 必须指向同一 M401 attempt 的 `.../M401/attempt-receipt.json` 完整 bytes/SHA；M401-R 自身的 `.../M401-R/M401-R-review-receipt.json` 是被 promotion 的 source receipt，不指向自身。M401 packet promotion 的 source ref/SHA 只由 `.../M401/attempt-receipt.json` 记录，不写入 packet 副本。

执行顺序唯一为：`DESIGN-ADVISORY（可选、不阻断）→ ROOT-CAUSE → C0 → C1 → C2 → C3 → IMPLEMENT-CURRENT → M401 → M401-R → M402`。IMPLEMENT-CURRENT 是独立卡，必须在 C3 之后、M401 之前完成并留下自己的 attempt/inverse 证据；不得把它并入 M401。真实 provider 仅由 M402 调用。

CompanyBrain 的 `companybrain_snapshot_id` 必须哈希与 `companybrain_tree_sha256` 完全相同的 canonical UTF-8 JSON+LF 字节对象，即按相对路径 UTF-8 bytes 排序的完整 `{relative_path, sha256}` 数组；取该完整字节 SHA-256 的前 24 个小写十六进制字符并加 `cb-` 前缀，不得哈希 `tree_sha256` 字符串、仅路径列表或主机路径。

`runtime_contract_hash` 的输入唯一为 runtime authority map、其声明的 17 个 authority 文件和 4 个评价输入，共 22 个文件；按相对路径 UTF-8 bytes 排序后，将每项的 `{relative_path,schema,actual_sha256,canonical_sha256,size}` 数组按 canonical UTF-8 JSON+LF 序列化并 SHA-256。`config/task5-quality-result-v3.json` 是 gate-specific schema input，不进入 `runtime_contract_hash`；`runtime_contract_id` 固定为 `rt-` 加该 hash 前 24 个小写十六进制字符。C0/C1/C2 的只读 attempt 统一使用 `task5-readonly-gate-attempt.v1`，不生成 run-root 或 inverse patch。

机器字段按 active spec 的封闭定义实现：M401 `task5-m401-attempt-receipt.v1` 只允许 `schema_version/gate/attempt_id/command/command_sha256/fixture_bundle_ref/fixture_bundle_sha256/fixture_manifest_sha256/run_root_ref/run_root_sha256/packet_ref/packet_sha256/snapshot_tree/material_id/exit_code/status/reason_code`；`snapshot_tree`、`material_id` 和 `input_snapshot` 的字节与 null 规则使用 spec 同名定义。route `scores`、`embedding_receipt`、`failure` 也只能使用 spec 固定字段，不能让 provider 自由扩展。`reason_code`、attempt status、`terminal_status` 和 M401-R outcome 必须使用 spec 的封闭枚举及 blocked/unavailable 映射。

本节与 `spec.md` 的当前修订 v4.7 成对生效，不增加用户需求；它把实现责任、验收责任和失败边界写成唯一执行路径。设计审查只保留为可选 advisory 事实记录，缺少 `terminal-clean` 设计结果不阻断后续卡片；实现审查、M401/M401-R、真实 provider、Reader/Audit 和五项质量硬门不降低。文末的唯一归档分隔线之后只作审计背景。

实现对 public machine tree 的最终收口：只保留 `spec.md` 当前十一项固定 `_audit` 文件；`quality-result` 由 M402 host-only attempt 和唯一 promoted artifact 承载，public `run-result.json` 只保存其 ref+SHA。旧的 `run-result.receipt.json`、`quality.json`、`sources.jsonl`、`evidence.jsonl` 仅属于 compiler 中间输入或历史资料，不属于 M402 最终 public tree；host-only `host-run-receipt.json` 的 `public_receipt_ref` 固定为 `bundle/_audit/run-result.json`。

### v4.4 当前纠偏：历史门与当前 raw-only 门分离

`D0-H/ROOT-CAUSE` 继续运行并保留精确 V50 缺失的 `blocked/calls=0` 事实，但它不再阻断当前候选、M401、M401-R 或 M402，也不要求 promotion。当前门只读取 D0-R 的 89 条 raw source-scope、M402 当次 CompanyBrain 快照、真实 Qwen/Jina、五项逐格质量和 Reader/Audit 闭包；CompanyBrain 的比较身份以当次快照为准，不再以历史 `RC-CURRENT-BASELINE` 回放成功为前提。SND 使用 `SND-RULE-002` 的描述性语境规则，generic “错误”在明确的优缺点/否定语境中不再阻断 zero-match。

本计划沿用 spec 的唯一 `canonical UTF-8 JSON` 定义：对象 key 递归按 Unicode code-point 升序，数组保持原顺序，使用无空格、`ensure_ascii=false`、`allow_nan=false` 的 UTF-8 JSON，并追加且仅追加一个 LF；未另行说明的 JSON hash 均使用这组字节。

当前计划只认 `knowledge-digest-*` public bundle schema；`task5-*` 可用于 C0 authority/config/provider 输入，以及 WorkflowHub、repair-gate、failure、host-only evidence schema 的身份，但不得产生同义 public 文件。CompanyBrain public snapshot 唯一 schema 为 `companybrain-route-snapshot-public.v1`，身份字段唯一为 `companybrain_snapshot_id`。四个 raw 产品的映射严格复用 `spec.md` 的归一化比较键表，不由文件名、LLM 或输入顺序推断。

执行补充规则与 spec 同步：Home.route 以 `(route_name, home_target_page_identity)` 去重；同 route 同目标直接在渲染前失败。CompanyBrain observation row 的 `status` 只允许 `present|absent|unknown|forbidden`，其中只有 `present` 可比较，`absent` 只能得到 `CB_MISSING`，`unknown/forbidden` 不能产生 `KD_WIN`，`N/A` 只能来自 C0 applicability。`qwen_payload_sha256` 只有一个规则：hash 传给 `model.generate` 的最终逻辑 payload 字符串 UTF-8 bytes；compiler 不 trim、不追加换行，结构化数据先按 C0 canonical JSON+末尾 LF 序列化成该字符串，再对最终实际 bytes 求 hash。

route row 的 `status` 只允许 `ready|failed|blocked|unavailable`，分别表示完整路由通过、局部 source/projection 失败、输入/合同/身份/预算/锁等全局阻断、provider/依赖不可用；不得使用 `picked`、`selected` 或 `candidate`。CompanyBrain 完整 observation rows 的 host-only 文件固定为 `quality/evidence/task5/actual-run/attempts/<id>/companybrain-observation.json`，schema=`task5-companybrain-observation.v1`，固定字段为 `run_id/source_manifest_sha256/companybrain_snapshot_id/companybrain_tree_sha256/rows/observation_sha256`；rows 使用 spec 固定的十字段 row schema 和排序/hash 规则，public snapshot 只作脱敏 projection。

`task5-m401-r-review-receipt.v1` 的固定字段在两份 source/promotion receipt 中都恰好包含 `schema_version/review_kind/m401_packet_ref/m401_packet_sha256/review_result_ref/review_result_sha256/source_receipt_ref/source_receipt_sha256/snapshot_tree/material_id/terminal_status/terminal_clean/all_findings_disposed/finding_dispositions/outcome/status/reason_code`；`status/reason_code` 必须按 spec 的唯一映射落盘，不能只在 prose 或 review-result 外推导。

实现与 verifier 在本计划中只认这一组边界细则：C3/M401 使用 `fixture_source_count` 表示受控 fixture 行数，M402 才要求真实 89 行；`run_root_sha256` 是隔离 bundle 除两个 run-result 文件外的 regular-file tree hash；title slug 只把 Unicode `Letter`/`Nd` 作为字母数字，非空 title 的空 slug 为 `untitled`，空 title 失败；失败索引 basename 是 `bundle`；空 body section 不生成 heading、`section` 或 `answer_body` unit；所有 `manifest.routes` row 都是唯一目标非空的 `Home.route` row。M401 `attempt-receipt.json.packet_sha256` 使用 M401 packet 完整 UTF-8 文件字节，并与 M401-R 的 `m401_packet_sha256` 相同。每个 `(product_key,page_type)` 目录维护全局最终文件名占用集合，按 `(product_key,title,page_id)` UTF-8 bytes 升序，从 `base_slug`、`base_slug-2`、`base_slug-3`……选择首个未占用名，追加后缀前按 `100-len("-N")` 个 Unicode code point 截断 base；其它 base slug 组的基名和后缀名也占用该集合。C0/M401 必须覆盖这些反例，本段与 spec 的同名字段逐字同义。

### A. 入口和输出只保留一条链

符号规则唯一解释：`route_name:page_identity` 与 `route_name:home_target_page_identity` 都表示 `route_name`、ASCII `:` 和 `home_target_page_identity` 实际值的拼接，不把字段名写入 slot。纯 lineage/quality 失败固定为 `not_released`/exit 1；identity、authority、锁、预算或 provider-global 失败才是 `blocked`/exit 2 或 `unavailable`/exit 2。M401-R 唯一 receipt schema 为 `task5-m401-r-review-receipt.v1`，字段还必须包含 `source_receipt_ref` 与 `source_receipt_sha256`，promotion 只原样提升 attempt-local source bytes。

M401 通过 attempt 的 packet 由 authenticated adapter 原样 promotion 到 `quality/evidence/task5/M401-evidence-packet.json`；来源 ref/SHA 只由同一 attempt 的 `M401/attempt-receipt.json` 记录，promotion view 与 attempt-local packet 字节完全一致。隔离 attempt 只是不写 Downloads/public bundle，不否定顶层 promotion view。M402 host-only `quality-result.json` 顶层固定保存 `companybrain_snapshot_id`、`companybrain_tree_sha256`、`observation_sha256`，row 的 CompanyBrain digest 必须属于该顶层绑定；public `bundle/_audit` 不复制整份 quality result，只由 `run-result.json.artifact_manifest.quality_result` 保存 ref+SHA。

`tree_sha256` 与 `companybrain_tree_sha256` 都先建立 `{relative_path,sha256}` 文件项数组：只纳入声明集合中的 regular files，按 `relative_path` UTF-8 bytes 升序排序；再用递归 key 排序、无空格、`ensure_ascii=false` 的 canonical UTF-8 JSON 加单个 LF 求 SHA-256。正式 bundle 集合排除 `bundle/_audit/run-result.json` 和 `bundle/_audit/directory-manifest.json`；compiler 的临时 `run-result.receipt.json`、`quality.json`、`sources.jsonl`、`evidence.jsonl` 在 formal audit 前删除。CompanyBrain 集合是 authenticated scanner 实际读取的 approved snapshot regular files，不含目录、软链接或 KnowledgeDigest 生成文件。`companybrain_snapshot_id` 固定为 `cb-` 加同一 CompanyBrain canonical file-list bytes 的 SHA-256 前 24 个小写十六进制字符，不含 host path、run id 或输入顺序。

§A 的失败条件只针对当前运行实际产出的公开树和编译器输出：若本次输出出现 `_digest`、`modules`、`boundaries`、`knowledge` 或第二个 CLI 输出树则失败；仓库中既有的历史/测试 `_digest` 不构成失败。M402 的通过条件直接引用 spec 的 released 谓词：每个 `applicable=true` 的 projection×dimension 行必须为 `KD_WIN`，每个 `applicable=false` 的行必须恰为 `N/A`，且投影×维度矩阵无缺失、重复或额外行。

- `digest` 仍可由 `knowledge_digest.simple_cli:main` 暴露，但该函数只能解析参数、调用 `compiler.digest` 并映射 `released/not_released/blocked/unavailable/failed/cancelled`；不得在 CLI 层拼接答案、分类、标签、Audit 或质量结果。
- `compiler.digest` 是唯一编排入口：它必须按 `raw → Evidence → Jina route → Qwen typed semantic output → Reader/Audit → quality.py → publisher.commit` 执行；`task5_runtime.py`、`task5_provider.py`、旧 evaluator 不得出现在生产 import graph。
- `publisher.commit` 接收显式 `run_root`，唯一目标是该 run root 下的 `bundle/`；C3/M401 传隔离 repair-gate run root，M402 才传新的 Downloads run root。`bundle/README.md`、`Home.md`、`Audit.md`、`products/` 是读者面，机器面只允许 active spec 开头列出的十一项 `_audit` 文件；host-only `quality-result`、CompanyBrain observation 和 host-run receipt 不进入 public bundle。任何 `_digest`、`modules`、`boundaries`、`knowledge` 或第二个 CLI 输出树都直接失败。

`tree_sha256` 只排除 `bundle/_audit/run-result.json` 与 `bundle/_audit/directory-manifest.json`；formal M402 在写入目录 manifest 前删除 compiler 临时的 `run-result.receipt.json`、`quality.json`、`sources.jsonl` 和 `evidence.jsonl`。`run-result.json.artifact_manifest.quality_result` 只保存 host-only quality artifact 的 ref+SHA，M401/M402/host receipt 必须重算并核对。

### B. CompanyBrain 当前快照必须成为比较输入

M401-R 的状态映射固定为：`available → NONE/passed/semantic`；`needs_human|partial → QUALITY_GATE_FAILED/blocked/semantic`，两者都停止在 M401-R；`unavailable → REVIEW_UNAVAILABLE/unavailable/transport|cancelled`。除 `available` 外不得进入 M402，也不得被改写为普通质量失败。

M401 receipt 的 `fixture_bundle_sha256` 固定等于 C3 fixture `bundle/` 的 `tree_sha256`（除两个 run-result 文件外的 regular-file canonical file-list bytes）；`fixture_manifest_sha256` 固定等于该 fixture `run-result.json.manifest` 的 canonical JSON+LF SHA，且等于 fixture receipt 的 `manifest_sha256`。两者分别绑定文件树和 RunManifest。

M402 在读取质量结果前重新扫描 authenticated runner 传入的 `companybrain_root`，生成不可变 `companybrain_snapshot_id`、`companybrain_tree_sha256`、逐文件 hash/locator 和 `observation_sha256`；实际 root identity 只进 host-only receipt，不进 public bundle。它们必须与本次 raw `source_manifest_sha256`、`run_id` 和 quality result 绑定。`quality.py` 只接受这组绑定，不接受静态 baseline 的单独引用；缺失、漂移、旧 run 或跨 source manifest 一律 `CB_MISSING/UNKNOWN`。

`source_manifest_sha256` 由 C1/compiler 对 RunManifest 的 89 个 source rows 按 `relative_path` 排序后，以 canonical UTF-8 JSON（递归 key 排序、无空格、末尾 LF）计算；`_audit/sources.jsonl` 必须能重算相同结果。`observation_sha256` 由 M402 snapshot scanner 唯一生成：对 canonical UTF-8 JSON（递归 key 排序、无空格、末尾 LF）中的 `run_id`、`source_manifest_sha256`、`companybrain_snapshot_id`、`companybrain_tree_sha256`、按 `case × projection × DIM-01…DIM-05` 排序的 `case_id/projection_id/dimension_id/status/score/source_refs/visible_ref/audit_ref/gap_ref/kd_ref` rows 求 SHA-256。`kd_ref` 必须指向同一 KnowledgeDigest comparison projection 的 Reader `page_path#unit_id`，不能只指向 Audit；public snapshot、quality rows 和 run-result 只原样引用这个 digest，不各自生成。 `authority_manifest_sha256` 固定等于当前 `runtime_contract_hash`，其输入就是 runtime authority map、17 个 authority 文件和 4 个评价输入的 22 文件闭包；不另建或临时推导第三种 authority hash。
`RunManifest` 的唯一 schema 为 `knowledge-digest-run-manifest.v1`，顶层字段恰好为 `schema_version/source_count/sources/routes/pages/tree_sha256`，只内嵌在 `run-result.json.manifest`；`sources` 按 `source_id`、`routes` 按 `query_id`、`pages` 按 `page_id`，均按 UTF-8 bytes 升序。M402 真实运行的 `source_count` 才固定为 89；C3/M401 使用自身受控 `fixture_source_count`，但仍须满足同一 schema 和闭包。运行级 manifest 由 `run-result.json` 的 canonical hash 和 `directory-manifest.json` 一起回查，不再生成 public `run-result.receipt.json`；不能另取 source rows 或路线摘要，因此 compiler、quality.py 和 verifier 都消费同一对象。

`observation_sha256` 的 observation rows 固定按 `case_id`、`projection_id`、`dimension_id` 三个字段依次以 UTF-8 bytes 升序排列；不使用配置数组位置、输入顺序或模型输出顺序。`source_refs` 在每行内同样按 UTF-8 bytes 升序，其他 JSON 字节遵守上述 canonical UTF-8 JSON 定义。

`RunManifest.pages` 使用唯一 `knowledge-digest-page-row.v1`，字段恰好为 `page_id/page_key/page_type/axes/source_ids/path/surface_sha256`；`axes` 恰好是五轴，`source_ids` 非空且按 UTF-8 bytes 排序。`page_type` 只允许 `positioning|concept|operation|diagnosis|experience`，分别对应 DIM-04 的定位/概念/操作/诊断/经验；Reader path 统一按 `products/<product_key>/<page_type>/<filename>.md` 生成：产品键、title slug、100 code point 截断、同名按 `(product_key,title,page_id)` 排序追加 `-2/-3` 的完整字节公式以 spec 为准。未知一级产品固定 `unclassified/unsupported` 且不生成 page row；`pages` 数组按 `page_id` UTF-8 bytes 排序；写者、quality.py、M401/M402 verifier 只实现这一套公式。

### C. 逐句血缘覆盖率是硬门

渲染前枚举每个可见 Reader 标题、问题、业务句、五轴值、页面类型值、section 和 Home route，生成稳定 `unit_id`。`unit_id` 的输入不是可见字符串转义，而是四段 UTF-8 byte array 按顺序拼接：`page_path bytes`、单个 `0x00` byte、`page_key bytes`、单个 `0x00` byte、`surface bytes`、单个 `0x00` byte、`slot bytes`；取 SHA-256 前 24 个小写十六进制字符并加 `u-`。`slot` 对 title/question/summary/page_type 使用固定值，对 axis 使用轴名，对 section/answer_body 使用 heading，对 Home.route 使用记号 `route_name:<home_target_page_identity>` 的字节公式，字段名不进入 bytes。`bundle/_audit/evidence.jsonl` 必须对每个 unit 恰好写一行唯一的 `knowledge-digest-render-unit.v1`：`unit_id`、`page_key`、`page_path`、`surface`（八项完整枚举 `Reader.title|Reader.question|Reader.summary|Reader.answer_body|Reader.section|Reader.axis|Reader.page_type|Home.route`）、`slot`、`text_sha256`、`raw_source_id`、`raw_hash`、`block_id`、`claim_id`、`locator`、`support_sha256`、`audit_ref`、`claim_ids`、`evidence_ids`、`source_ids`、`evidence_bindings`；`unit_id + page_path` 唯一。每个 page 先锁定唯一主 route row，再按 `(source.relative_path,start_line,evidence_id)` 选择首个 binding：title/question/page_type 取 summary binding，summary 取 summary 自身 binding，section/answer_body 取自身 binding，axis 取自身 binding，Home.route 取同一 route row 的首个 binding。`audit_ref` 固定为 `Audit.md#evidence-<evidence_id>`，Audit 必须实际存在该 anchor。axis/page_type/title/question/Home.route 的 binding 必须来自 route ledger 的同一 `evidence_bindings`，与触发它的 raw block/claim/locator/support hash 相等；没有触发证据就不生成该 unit。README、Audit 和 Home 的非 route 内容只能是从本次 machine evidence 确定性重建的固定模板，检测到动态业务句即失败，不扩展 surface。quality.py 是 lineage coverage 的唯一计算/判定者，compiler 只执行其失败结果，要求 100% 绑定当前 raw、无跨源或错位引用；publisher 只校验已生成 bytes，不再计算第二个 lineage 结果。

`knowledge-digest-render-unit.v1` 的四个“surface 名即 slot”固定字面量是 `title`、`question`、`summary`、`page_type`；`axis`、`section`/`answer_body` 与 `Home.route` 仍分别使用前述固定 slot 公式。quality.py 按 surface 直接推导这些值再重算，不能信任输入行的 slot。`page_key` 固定为 source page 的 `source:<source_id>` 或 quality answer page 的 `answer:<question_id>:<page_type>`；`question_id`、Home route 的五个 `route_name`、`page_identity` 和 route page key 均按 spec 的 route identity 段逐字节公式生成。
实现约定：`surface` 字段实际保存完整枚举值（含 `Reader.` 或 `Home.` 前缀），`slot` 才保存不带前缀的 `title|question|summary|page_type` 或对应轴名、heading、`route_name:page_identity`；两个字段都参与 unit_id 重算，不能把 surface 前缀省略到 slot。

### D. 直接对应的测试与 receipt

在 M401 focused/full 集合加入四组行为测试：`ENTRY-001` 验证 public `digest` 只调用 compiler；`OUTPUT-001` 验证只产生 `bundle/_audit` 正式树；`BASELINE-001` 验证 CompanyBrain snapshot/observation 绑定和漂移 fail-closed；`LINEAGE-001` 验证无血缘、错 hash、错 locator、重复 unit 和 100% coverage 负例。每组 receipt 绑定当前 snapshot/material 和命令 hash；绿测试不能替代 M401-R、M402 或五项真实质量证明。M401/M401-R 自身也必须在 `repair-gates/attempts/<id>/M401/` 和 `repair-gates/attempts/<id>/M401-R/` 生成 `attempt.json` 与 `inverse.patch`，固定 promotion view 只引用该 attempt。
M401 与 M401-R 的 attempt 都执行同一回滚校验：保存目标文件 before/after SHA-256、`inverse.patch` SHA-256 和 attempt identity，并在独立临时副本执行 `git apply --check --reverse <inverse.patch>`；任一 hash、路径或反向应用不相等，attempt 只能 failed/blocked，不能更新 promotion view。ROOT-CAUSE 是唯一例外，因它不修改仓库且独立使用 root-cause receipt。

`knowledge-digest-render-unit.v1` 保存 `slot`，由 `page_path/page_key/surface/slot` 重算稳定 `unit_id`；Home.route 的 slot 固定为 `route_name`、ASCII `:`、`home_target_page_identity` 实际值的拼接（文档记号为 `route_name:<home_target_page_identity>`），避免同一入口选中多个页面时发生碰撞。quality.py 是 lineage coverage 的唯一计算和判定者，compiler 只拒绝未达 100% 的结果，publisher 不重复裁决。

## 1. 先收敛合同

运行计数只能由输入派生：`P=len(quality projection ids)=12`；`R_full=count(row.status=ready AND row.source_digest_eligible=true)=87`；`R_slice` 对派生的 27 条 slice source rows 使用同一公式，当前为 25。唯一允许的 source status 是 `ready`、`known_empty`、`duplicate_alias`、`provider_failed`、`unsupported`；只有 `ready` 且 `source_digest_eligible=true` 才进入 R，其他状态必须逐行保留在 RunManifest/Audit，不能进入未定义的 `other` 桶。实际 `P/R_full/R_slice` 必须写入 call plan；这些数值不是手写运行结果。

当前 3rd-review 已确认旧材料同时包含两条架构、两套输出树、两套 semantic schema、重复 authority hash 和未定义的 RunManifest/hash/budget 规则。先以 `spec.md` 与本节顶部合同为准，重新生成当前材料身份；不再在历史段落上继续打补丁。切片、89 条 full、真实 provider 和五项对照仍是同一 Task5 的明确范围，不因 mini-task 名称而拆成后续任务。

slice 的 case/path/数量只从 `config/task5-slice-cases-v1.json` 派生，当前为 11 case/27 unique paths；运行器不得读取旧 slice 口径的 14 case/12 path 常数。C0 只把旧常量作为当前生效字段值时视为冲突；当前合法的 `P=12` projection、11 case、27 unique path 不触发该规则。每个 authority 的 actual/canonical SHA、size、schema 由 C0 从唯一文件 `config/task5-runtime-authority-map-v1.json`（schema=`task5-runtime-authority-map.v1`）及其真实指向文件重算，不能从 prose 恢复。map 自身只计 1 个文件，`authorities` 数组指向 17 个 authority 文件，另有 4 个评价输入和 1 个 gate-specific schema input，共 23 个 C0 文件；gate-specific schema input 是 `config/task5-quality-result-v3.json`，不计入 runtime_contract_hash。`config/task5-reader-quality-provider-v2.json` 是其中唯一的 `reader_quality_provider` 文件，不是第二个 map；第 23 项是 gate-specific quality-result schema，且不进入 runtime_contract_hash。材料不重复维护第二套 hash 副本。

## 2. 唯一实现边界

route ledger 的固定字段还必须包含 `home_target_page_identity`；`page_key` 允许且只允许三种形态：source page 的 `source:<source_id>`、quality answer page 的 `answer:<question_id>:<page_type>`、Home.route 的 `route:<sha256(NFKC(route_name))[:20]>`。写者、`quality.py` 和 M401/M402 verifier 必须按 `spec.md` 的同一公式重算这些字段，不能把 Home.route 当作前两种 page key。未定义 source 状态不能归入模糊的“other”。

`run-result.json` 内嵌的 `manifest` 由该文件自身的 canonical hash 和 `directory-manifest.json.tree_sha256` 闭合，不再单独生成 public `run-result.receipt.json`。不得只 hash source rows 或省略 routes。M401 的 `attempt.json` 与 `attempt-receipt.json` 的 `command`/`command_sha256` 只记录唯一 packet-writer 命令；focused/full pytest 的命令、退出码和输出 hash 只进 AC trace/test receipt。任何写隔离 run-root 的 gate 都按相同规则把 `run_root_ref` 写进 attempt.json。

`_audit/route-ledger.jsonl` 只允许由同一个 `manifest.routes` 生成：逐行、同顺序、完整保留 route row 的所有字段和值，以 canonical UTF-8 JSON+LF 序列化；它不是第二个 ledger/schema。写者、C3/M401 fixture verifier 和 M402 published-closure verifier 都必须重算预期 JSONL 的完整字节和 SHA-256，并与实际文件逐字节及逐 SHA 相等；行数/顺序/字段/值任一漂移都停止。`manifest.routes` 是唯一权威事实来源，JSONL 只作为公开 machine projection，不能被其它消费者独立重建或反向覆盖。

Home.route 的机器归属必须明确：它的 `page_path` 固定为 `bundle/Home.md`，`selected_page_ids` 只能有一个主目标，`home_target_page_identity` 必须等于该目标 ReaderPage 的 `page_identity`；零个或多个目标都记录确定性失败。`slot` 固定为 `route_name`、ASCII `:`、`home_target_page_identity` 实际值的拼接，文档记号为 `route_name:<home_target_page_identity>`，不能把字段名本身写入 slot，也不能用 Home 自身 identity 或多个候选中的第一个代替。host-only `quality-result.json` 的每条 `quality_rows` 固定包含 `projection_key`、`dimension_id`、`verdict`、`kd_observation_ref`、`cb_observation_ref`、`observation_digests`、`advantage_basis`；`kd_observation_ref` 只能指向同一 projection 的 Reader `page_path#unit_id`，Audit-only 引用无效。

生产链固定为 `digest CLI → compiler.digest → providers → quality.py → publisher.commit(run_root)`；`pyproject.toml` 的 `digest` 必须指向 `knowledge_digest.simple_cli:main`。`--gate M401` 的必填参数是 `--fixture-bundle`、`--m401-attempt`、`--m401-run-root`；`--gate M402` 的必填输入是 raw、Downloads run-root、CompanyBrain root、runtime `--config`、secret-bearing `--provider-config` 及三方身份绑定。两种模式都只能由 simple_cli 调 compiler.digest；M401 fixture 不能读取 raw/CompanyBrain/provider，M402 才允许真实输入和 provider。这里 `--config` 只指非秘密 runtime 配置，`--provider-config` 只指本地 provider 配置；真实路径只在 host-only receipt 中出现。`run-result.json.manifest.routes` 是唯一 `knowledge-digest-route-ledger.v1`，由 compiler 写入，Reader/Home 与 quality.py 读取。route row 固定字段的完整集合是 `query_id/question/scene/route_name/product_key/projection_id/candidate_source_ids/selected_source_ids/selected_page_ids/scores/embedding_receipt/qwen_payload_sha256/evidence_bindings/home_target_page_identity/status/failure`；不得删字段、改名或另建 route schema。每行还必须按 spec 的 route identity 段生成 `query_id`，其中 `route_name` 只能是五个冻结 `ROUTE_QUERIES` 之一，`product_key` 是主页面产品键或 `shared`，`projection_id` 是当前 quality projection 键；`question_id` 与 `query_id` 相等，selected page 的 `page_key/page_identity` 也按同一段公式重算，并以这些 route name 驱动 Home route。route row、ReaderPage、Home 和 evidence ledger 不得各自实现另一套 identity 算法。跨产品答案只有在 selected closure 命中至少两个不同 product_key 时才落到 `products/shared/`，source row 永不改写为 shared。

- Provider 配置的默认位置固定为 `~/.config/knowledge-digest/config.json`；M402 的 authenticated runner 可用显式 `--provider-config` 指定同一 v2 schema 文件，显式参数优先。`llm` 必须使用 `https://dashscope.in.whatspos.cn/v1` 上的 `qwen3.8`，`embedding` 必须使用 `https://llm.paxszapp.com/v1` 上的 `jina-embeddings`，receipt 记录实际 model。key 解析顺序是 provider section 的 `api_key`、再到 `api_key_env` 兼容回退；根级 `api_key` 仅作为迁移兼容直接 key 补入缺失 section，不能覆盖已有 section `api_key`。schema、key、endpoint、model 或 calibration 在首个请求前失败时必须 `blocked|unavailable` 且 provider calls=0；key 不进入 payload、receipt、cache、bundle 或报告，绝对 config path 只进 host-only receipt。
- Provider adapter 每个 `(provider, request_identity)` 只允许一次 HTTP attempt（`retry=0`）；编译器恢复是单独的有界逻辑：source 全局最多 12 次 recovery call、单 source 最多追加 3 次，quality projection 校验失败最多再发 1 次完整 Qwen 页面。质量事实校验固定一页一请求，避免多页响应的 page identity/结果数漂移。每次 recovery 必须落 trace、hash 和 call plan，不能拼接或由 Python 改写正文；耗尽预算后保留 Audit-only/not_released。
- `compiler.py`：raw snapshot、Evidence、ReaderPage、Home、Audit、RunManifest。
- `providers.py`：Qwen typed semantic output、Jina selected route；key 只在内存。
- `publisher.py`：输出 preflight、manifest/tree hash、原子提交；不生成或改写质量对象。
- `simple_cli.py`：参数解析和结果摘要。
- `quality.py`：唯一纯质量裁决边界；读取本次 Reader/Home/Audit/route ledger 和 CompanyBrain observation，返回不可变 `knowledge-digest-quality-result.v3`，不生成正文、不落盘；compiler 负责将该对象序列化为 host-only `quality-result.json` 并把受控 ref+SHA 写入 `bundle/_audit/run-result.json`，publisher 只提交已生成的 bundle 字节。`quality.py` 只使用 `DIM-01.route`、`DIM-02.taxonomy`、`DIM-03.business-answer`、`DIM-04.page-type`、`DIM-05.reader-audit`，不接受旧自由文本维度。
- `task5_runtime.py`、`task5_provider.py`、旧 evaluator：历史/回归用途，生产零 import；暂不删除，避免破坏历史证据和不可逆迁移。

### 2.1 实施文件边界和回滚

M401-R 的写入 allowlist 与回滚集合统一为四项：authenticated `mini_task.implementation` adapter 在该 attempt 目录写 `review-result.json` 和 `M401-R-review-receipt.json`，并由同一 attempt 写 `attempt.json`、`inverse.patch`；四项都进入 before/after 快照、路径 hash 和 inverse 校验。顶层 promotion view 只原样提升 attempt-local `M401-R-review-receipt.json`，不另写 review-result。

实现只能新增或修改以下生产路径：`src/knowledge_digest/compiler.py`、`src/knowledge_digest/providers.py`、`src/knowledge_digest/publisher.py`、`src/knowledge_digest/simple_cli.py`、`src/knowledge_digest/quality.py`；provider 兼容修复只允许触及现有 `src/knowledge_digest/llm.py`、`src/knowledge_digest/embedding.py`、`src/knowledge_digest/reader_bundle.py`。对应 focused/full 测试只能位于 `tests/test_simple_*.py`、`tests/acceptance/test_task5_*.py`，配置只能使用 active authority 已声明的 `config/task5-*.json`。slice→full 共享 run context 由 `compiler.py` 的明确编排入口负责，`simple_cli.py` 只负责参数解析和调用；`task5_runtime.py`、`task5_provider.py`、旧 evaluator 完全只读历史/回归资料，不得修改、导入或成为生产入口。

以下均为只读：raw、CompanyBrain、main、旧候选、旧产物、`/private/tmp` 候选、其他仓库和历史 evidence。不得删除、重命名或覆盖任何已有文件。任何写隔离 run-root 的 C3、M401 attempt 都必须在自身 `attempt.json` 写 `run_root_ref`；IMPLEMENT 只写自己的 attempt receipt/inverse.patch，不生成或保留 run-root；IMPLEMENT/M401-R 的 repair attempt 固定写 `run_root_ref=null`，C3/M401 才写非空隔离 run-root 引用。

C0、C1、C2 是只读合同/反例核对，只写各自 `attempt.json`，不写 `inverse.patch`；三者的 `attempt.json` 统一使用 `task5-readonly-gate-attempt.v1`，固定字段为 `schema_version`、`gate`、`attempt_id`、`material_id`、`input_snapshot`、`command`、`command_sha256`、`observed_files`、`output_ref`、`output_sha256`、`run_root_ref`、`exit_code`、`status`、`reason_code`，其中 `observed_files` 为按相对路径排序的 `{path,size,sha256}` 数组，`output_ref/output_sha256/run_root_ref` 必须为 null，且不得增加字段。C3、IMPLEMENT、M401、M401-R 才在写 receipt 前保存 allowlist 每个路径的 `before_sha256`，并写 `after_sha256`、`changed_paths`、`patch_sha256`、完整 unified-diff inverse patch、`inverse_patch_sha256` 和 `inverse_base_after_snapshot`。M401 的 `attempt.json` 必须把隔离输出写成 `run_root_ref` 字段；它不是单独文件。M401-R 虽不写 run-root，但它的四项 allowlist 固定为该 attempt 的 `review-result.json`、`M401-R-review-receipt.json`、`attempt.json` 和 `inverse.patch`，顶层 `quality/evidence/task5/M401-R-review-receipt.json` 只能是 authenticated adapter 对 attempt-local source 的原样 promotion，不包含源代码或 M401 bundle；回滚目标是删除/恢复这些审查证据文件。回滚只允许在当前 after snapshot、路径集合和 inverse hash 全部相等时应用；任一漂移即停止并保留现状。M401 packet 只消费通过 attempt 的 receipt，不以文字“可回滚”替代 patch。

回滚证据的当前路径和动作固定为：C3、IMPLEMENT、M401、M401-R 分别写入各自卡片列出的 `quality/evidence/task5/repair-gates/attempts/<attempt_id>/<card>/`，不再使用可自由替换的 `<gate>` 路径记号；其中 C3、M401、M401-R 还写完整逆向补丁 `inverse.patch`，IMPLEMENT 也写自己的 `inverse.patch`。C0/C1/C2 只保留 `attempt.json`，因为它们不修改 allowlist 文件。需要回滚的 gate 的 `attempt.json` 的 `schema_version` 为 `task5-repair-gate-attempt.v1`，由对应 gate owner 在测试完成后、promotion 前生成，固定字段全集为 `schema_version`、`gate`、`attempt_id`、`attempt_seq`、`material_id`、`command`、`command_sha256`、`before_snapshot`、`after_snapshot`、`changed_paths`、`before_sha256`、`after_sha256`、`patch_sha256`、`inverse_patch_ref`、`inverse_patch_sha256`、`inverse_base_after_snapshot`、`run_root_ref`、`exit_code`、`status`、`reason_code`，其中 `run_root_ref` 在 C3/M401 为非空、在 IMPLEMENT/M401-R 为 null。验证命令固定为在临时 after 副本执行 `git apply --check --reverse <inverse.patch>`，并逐项重算路径 hash；任何路径、快照或 hash 漂移都停止，不应用补丁、不覆盖 attempt。固定 promotion view 只能由通过 attempt 原子更新，失败 attempt 永不 promotion。

## 3. 执行顺序

运行计数只能由输入派生：`P=12`；`R_full` 是 89 个 manifest rows 中 `status=ready` 且 `source_digest_eligible=true` 的数量；`R_slice` 是派生的 27 个 slice rows 中同样条件的数量。按当前冻结 raw/manifest/slice 输入重算时，预期审计分解为 `87 ready + 1 known_empty + 1 duplicate_alias` 和 `25 ready + 1 known_empty + 1 duplicate_alias`；这只是当前输入的校验基线，不是运行器可读取的硬编码，实际 call plan 必须从本次 manifest/slice rows 重新计算并记录。未定义状态直接 blocked 并计入 call plan。

1. DESIGN-ADVISORY：如 WorkflowHub 能返回当前设计审查，就记录其事实和风险；没有 canonical result、结果 partial 或 transport unavailable 都只记为 advisory，不阻断后续卡片，不伪造通过。
2. ROOT-CAUSE：执行 provider-free 精确旧结果回放；不可回查就留 `blocked/calls=0` receipt，不得用 raw-only 结果替代，但该历史状态不阻断当前 raw-only 门。
3. C0：校验四份 active material、authority schema/hash/枚举和 slice 派生闭包。
4. C1：离线只读验证冻结 89-row manifest、受控 fixture 的 Block/Claim locator 和 source 状态；不读取真实 raw、不写 host receipt。真实 raw snapshot、89 行 manifest 和 host-only root identity 只在 M402 的 authenticated `compiler.digest` 中生成。
5. C2：fake no-network 验证 Qwen 合同、Jina selected closure、无 overlay/无 raw fallback，并用“只改变 fake vector/rank”的因果反例证明 selected paths、route hash 和 Qwen payload hash 确实改变；真实 provider 仅由 M402 调用。
6. C3：只用 fake adapter 和受控小 fixture 验证四产品 Reader、Home/Audit/RunManifest、五项重算和失败语义；输出只写 `quality/evidence/task5/repair-gates/attempts/<attempt_id>/C3/run-root/`，其下只有唯一 `bundle/`；不读取 raw/CompanyBrain、不发网络、不写 Downloads，也不产生真实质量结论。M401 的输出测试同样只使用 `quality/evidence/task5/repair-gates/attempts/<attempt_id>/M401/run-root/` 下唯一 `bundle/`，不写用户 Downloads；M401-R 不产生 run-root，只审查 M401 packet。
7. M401：按 `spec.md` 的 AC-v4-01…AC-v4-13 生成当前测试/AC/实现证据和 packet，不做真实质量结论。
8. M401-R：authenticated WorkflowHub 执行 `mini_task.implementation`，terminal clean 后生成 successor。
9. M402：只用 authenticated runner 传入的用户批准 raw/CompanyBrain 执行 slice→full 89；按全量闭包和五项硬门决定 released/not_released，并在 `quality/evidence/task5/actual-run/attempts/<id>/host-run-receipt.json` 写 host-only receipt。不得把 host path 写进 active contract、public bundle 或 provider payload。

## 4. 失败语义

`task5-failure-evidence.v1` 是 bundle 外部的失败 sink，不是第二个 public bundle schema；它只保留脱敏状态、identity、调用数、Audit/ledger 引用和相对 locator。

合同、identity、authority、预算、配置、路径、锁或 provider policy 无法判断：`blocked`、calls=0。单源/单 route/Qwen 失败记录 Audit/RunManifest，允许时继续其他来源，但最终至少 `not_released`。known_empty 只有 manifest/hash/locator/status=known_empty 终态全部闭合才不阻断；duplicate_alias 只有 canonical hash、双 coverage row、Audit 和 canonical Reader link 全部闭合才不阻断。任一 `applicable=true` 的 projection×dimension 行不是 `KD_WIN`，或任一 `applicable=false` 的行不是 `N/A`，或矩阵缺行/重复/多出其它 verdict，或 source 未闭合、Jina 未消费、Reader/Audit 断链或输出树漂移：`not_released`。`simple_cli` 退出码唯一映射为 `released=0`、`not_released=1`、`blocked=2`、`unavailable=2`、`failed=3`、`cancelled=4`。发布失败必须把最小失败索引原子写入 Downloads failure sink，不能留下可被误读的半成品 bundle；旧已发布目录不得被覆盖。

Jina/embedding 失败按两类处理：单个 source/projection 的 HTTP/JSON/超时失败是 local failure，写入本次 Audit/route ledger，继续允许的 full 清单，但最终只能 `not_released`、退出码 1；DNS/TLS、认证失败、配置错误、预算超限、返回数量不一致、partial embedding 或 route closure 无法判断是 global failure，立即 `blocked/unavailable`、退出码 2，停止后续 slice/full。C3 的 network deny 是预期负例，不代表 M402 provider 可用。

### 4.1 C3、M402 的真实调用边界

预算补充：共享 run context 必须按本次实际 `R_slice`、`R_full`、`P` 和实际请求图重算 call plan；不再使用 140/133 这类脱离实现的固定数字。compiler 的 `_provider_call_plan` 是唯一计算者，必须把每个实际 provider call site 都列入计划：source compile、显式 source recovery、质量页首次生成、质量页逐页事实校验、质量页有界 repair，以及 embedding batch/probe。每一项都要分别记录 `planned`、`observed`、`http_attempt_count`、`retry_attempts` 和 request identity；slice→full 只有在 prompt/identity/response receipt 完全相等时才扣除 `exact_hit_reuse`，不能凭路径或数量猜复用。`planned_provider_calls = planned_llm_calls + planned_embedding_calls`，且必须在首个 provider 请求前写入 run plan；`budget.max_provider_calls` 必须不小于本次动态 worst-case plan，当前 provider v2 默认上限为 180。实际 provider calls 超过 plan、计划遗漏了调用档位、或运行前无法证明预算闭包，统一 `blocked/calls=0`，不得先调用再补 receipt。质量事实校验与 source recovery 都属于计划内调用，不得藏在“重试”字段里。

C3 永远是 fake/no-network contract test；它不能用“从实际页面重算”这句话暗示真实 provider。真实页面和 CompanyBrain 只在 M402 读取。M402 采用一个共享 run context：先记录 slice 结果，再用精确 identity 命中复用 slice 已成功的 source-digest 响应，最后扩展到 89 条 full；没有 receipt-bound exact hit 才计新调用。当前 raw 的 `R_slice=25`、`R_full=87`、`P=12` 只是本次输入重算出的观察值，不是代码常量；LLM/Jina 的计划上限由 `_provider_call_plan` 按实际调用图生成，provider v2 默认 `budget.max_provider_calls=180` 只作为配置上限，不代替动态计划。LLM timeout 上限 300 秒、embedding timeout 上限 180 秒；Qwen 单源 schema/引用/原文复制失败是 local failure，记录该 source/projection、继续其他 source，最终 `not_released`/exit 1；鉴权、配置、contract hash、全局身份、预算或所有请求不可用是 global failure，立即 `blocked`/`unavailable`/exit 2，并停止新调用。Jina 的相同 local/global 规则保持不变。运行前必须把实际 R/P、每个调用档位、复用项和预算写入 call plan；计划与 observed calls 不一致时不得 released。

### 4.2 设计审查和根因前置

预算公式的含义固定为：`87` 是每个 ready source 一次 source-digest；`2×P` 是每个质量 projection 的 typed compile 与受控 repair 预留；`2×min(2,P)` 是最多两个失败 projection 的 repair 预留，每个失败 projection 固定保留 compile+repair 两档；Jina 的 batch `8` 是 provider contract 的最大输入批量，`+12` 是质量 projection query 向量，前半段为 slice、后半段为 full。公式中的这些常数只能由本段和 provider authority 推导，实际运行仍以 call plan 的 R/P 重算值为准。

`DESIGN-ADVISORY` 是可选的事实记录，不是 M401/M402 的前置任务：如果 WorkflowHub adapter 能消费当前 `make-decision` `design_preflight` handoff，就绑定当前 task/worktree、材料 revision、Talk choices、contract identity 和 writer attestation；如果 review unavailable、partial、材料漂移、finding 未处置或没有 terminal-clean canonical result，只记录状态和风险，不停止 M401/M402，也不把它写成通过。M401/M402 的硬门改由当前代码、测试、M401 packet、authenticated `mini_task.implementation` 和真实运行证据承担。

`ROOT-CAUSE` 在 provider 前执行 `replay_root_cause()`。它只读取冻结的 root-cause input manifest、旧结果路径和 CompanyBrain/raw 元数据，不写 Reader、不发 provider。V50 精确路径不可回查时，输出 `blocked/calls=0` attempt，明确“根因未证实”；该事实只进入 M401 的 AC-v4-13 历史限制记录，不进入当前 raw-only release predicate，不能用 raw-only 运行填补。它是独立的前置诊断，不属于 repair-gates，不使用 `attempt.json/inverse.patch`；唯一 receipt 是 `quality/evidence/task5/root-cause/attempts/<id>/root-cause-evidence.json`，schema=`task5-root-cause-evidence.v2`。repair-gates 的 inverse 规则只适用于 C3、IMPLEMENT、M401、M401-R；C0/C1/C2 只写各自只读核对 attempt。

失败索引的唯一位置是 `<downloads_root>/<output_basename>.failure.<run_id>.<owner_nonce>/failure.json`；它使用 `task5-failure-evidence.v1`，只保存 reason、调用数、脱敏 Audit/ledger ref+hash 和 source/block identity。失败 sink 不包含 bundle，不创建第二个 `_audit` 入口；若运行已经创建 staging，`run-result.json.reason_code` 必须指向同一 failure ref，否则按 failed=3 处理。

### 4.3 Publisher 状态机

M402 的 Downloads run root 由 authenticated runner 传入并创建为新目录，公开结果是其中唯一的 `bundle/`；实际绝对路径只写 host receipt。publisher 状态为 `preflight → locked → staging → written → verified → committed`；失败为 `blocked/failed`，只原子写 `failure.json`，不得留下可读半成品 bundle。锁使用同一父目录的 `O_CREAT|O_EXCL`，staging 用唯一 `<run_root>/.bundle.staging-<run_id>`，每个文件写入并 fsync 后才算 written；目标不存在且 tree/manifest 重算相等才 rename。旧锁、非空目标、跨文件系统、rename/fsync 失败都停止，不覆盖、不自动清理其他 run。

## 5. 维护边界

不新建产品目录层、不新建评分维度、不复制 CompanyBrain、不使用旧候选填空、不在旧 runtime 上继续堆逻辑。新增规则必须先改 active contract 并记录设计影响；设计审查是可选 advisory，不以 terminal-clean 作为继续实现或真实运行的硬前置，不能在实现阶段用隐含约定补需求。

## ARCHIVE-NON-ACTIVE: previous root material

# mini-task plan：Reader 质量整合

## 实现

1. 扫描普通来源，按顶层目录建立稳定 product key/display name。
2. 读取可选语义候选；只有 source URI/指纹匹配才合并候选正文。语义候选由固定小批量、零重放的受控编译器生成，失败来源保留 fidelity-only 回退。
3. 建立唯一逻辑 `source_id → reader_paths` 映射；无法归属使用 `unclassified/general`，推断原因、指纹和完整身份写 Audit。
4. 生成根入口、产品 index/overview、知识类型入口、模块 index 和 `knowledge/<source>.md`；超过 300 行按顺序拆成 part 页面并互链。
5. 正文用语义候选或保真清理版：去 frontmatter、内部字段、hash 脚注、重复 H1，保留 Markdown、表格、代码、链接和事实顺序。
6. Reader frontmatter 只保留人需要的 title/type/status/description；根索引不输出逐页 signals、hash 或 topic id。
7. 编译后执行覆盖、泄漏、导航、事实保真和行数检查；复用既有 Task3 质量/发布边界，并计算 100 分 Reader 质量代理。
8. 使用 run-scoped 候选目录；检查前不替换旧包。

## 依赖接口

输入 source manifest 的最小字段是 `source_id/source_uri/relative_path/title/content_fingerprint/line_count/validation_status`；语义候选的最小字段是 `source_uri/content_fingerprint/title/summary/body/module/semantic_status`；Audit 映射的最小字段是 `source_id/reader_paths/product/module/mapping_reason/content_fingerprint/semantic_status`。TopicIndex 仅作为可选只读输入，读取 `source_members/source_ids/product/module/object_intent/published_path`。

## 文件边界

- `specs/task3-reader-quality-integration/` 是 WorkflowHub TaskHandle 使用的四份材料镜像，必须与根目录四份材料逐字一致；不另立一套需求。
- 新增 `src/knowledge_digest/reader_compiler.py`。
- 修改 `scripts/task3_full_release.py`，增加 `--raw-input` 模式并保留 `--steps-json`。
- 新增 `scripts/task3_semantic_compile.py` 和 `scripts/task3_reader_comparison.py`，分别负责固定批次语义候选和真实结果对比。
- 新增 acceptance fixture/test，覆盖成功、无法归属兜底、超长拆分、空内容/事实损失、缺源、泄漏、导航逃逸、旧包保护和 80 分代理。
- 同步必要命令说明，不改 Task2-C 合同。

## 测试

先写失败 fixture，再实现；跑相关 acceptance；跑完整 pytest；再用 `/Users/Hugh/Downloads/confluence 原始数据` 写入新的 Downloads 目录；最后用新增的 `scripts/task3_reader_comparison.py` 与 CompanyBrain 对比数量、层级、入口、泄漏和覆盖。

## 回滚

只回滚本 mini-task 新增代码/测试；保留 Task3 基线、失败证据和旧正式包。merge、push、archive、cleanup 不在实现阶段执行。
