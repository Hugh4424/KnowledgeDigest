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

当前计划只认 `knowledge-digest-*` public bundle schema；`task5-*` 可用于 C0 authority/config/provider 输入，以及 WorkflowHub、repair-gate、failure、host-only evidence schema 的身份，但不得产生同义 public 文件。CompanyBrain public snapshot 唯一 schema 为 `knowledge-digest-companybrain-route-snapshot.v1`，身份字段唯一为 `companybrain_snapshot_id`。四个 raw 产品的映射严格复用 `spec.md` 的归一化比较键表，不由文件名、LLM 或输入顺序推断。

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

Home.route 的机器归属必须明确：它的 `page_path` 固定为 `bundle/Home.md`，`selected_page_ids` 只能有一个主目标，`home_target_page_identity` 必须等于该目标 ReaderPage 的 `page_identity`；零个或多个目标都记录确定性失败。`slot` 固定为 `route_name`、ASCII `:`、`home_target_page_identity` 实际值的拼接，文档记号为 `route_name:<home_target_page_identity>`，不能把字段名本身写入 slot，也不能用 Home 自身 identity 或多个候选中的第一个代替。host-only `quality-result.json` 的每条 `quality_rows` 固定包含 `projection_key`、`dimension_id`、`verdict`、`kd_observation_ref`、`cb_observation_ref`、`observation_digests`、`advantage_basis`；`kd_observation_ref` 只能指向同一 projection 的 Reader `page_path#unit_id`，Audit-only 引用无效。

生产链固定为 `digest CLI → compiler.digest → providers → quality.py → publisher.commit(run_root)`；`pyproject.toml` 的 `digest` 必须指向 `knowledge_digest.simple_cli:main`。`--gate M401` 的必填参数是 `--fixture-bundle`、`--m401-attempt`、`--m401-run-root`；`--gate M402` 的必填输入是 raw、Downloads run-root、CompanyBrain root、runtime `--config`、secret-bearing `--provider-config` 及三方身份绑定。两种模式都只能由 simple_cli 调 compiler.digest；M401 fixture 不能读取 raw/CompanyBrain/provider，M402 才允许真实输入和 provider。这里 `--config` 只指非秘密 runtime 配置，`--provider-config` 只指本地 provider 配置；真实路径只在 host-only receipt 中出现。`run-result.json.manifest.routes` 是唯一 `knowledge-digest-route-ledger.v1`，由 compiler 写入，Reader/Home 与 quality.py 读取。route row 固定字段的完整集合是 `query_id/question/scene/route_name/product_key/projection_id/candidate_source_ids/selected_source_ids/selected_page_ids/scores/embedding_receipt/qwen_payload_sha256/evidence_bindings/home_target_page_identity/status/failure`；不得删字段、改名或另建 route schema。每行还必须按 spec 的 route identity 段生成 `query_id`，其中 `route_name` 只能是五个冻结 `ROUTE_QUERIES` 之一，`product_key` 是主页面产品键或 `shared`，`projection_id` 是当前 quality projection 键；`question_id` 与 `query_id` 相等，selected page 的 `page_key/page_identity` 也按同一段公式重算，并以这些 route name 驱动 Home route。route row、ReaderPage、Home 和 evidence ledger 不得各自实现另一套 identity 算法。跨产品答案只有在 selected closure 命中至少两个不同 product_key 时才落到 `products/shared/`，source row 永不改写为 shared。

- Provider 配置的默认位置固定为 `~/.config/knowledge-digest/config.json`；M402 的 authenticated runner 可用显式 `--provider-config` 指定同一 v2 schema 文件，显式参数优先。`llm` 必须使用 `https://dashscope.in.whatspos.cn/v1` 上的 `qwen3.8`，`embedding` 必须使用 `https://llm.paxszapp.com/v1` 上的 `jina-embeddings`，receipt 记录实际 model。key 解析顺序是 provider section 的 `api_key`、再到 `api_key_env` 兼容回退；根级 `api_key` 仅作为迁移兼容直接 key 补入缺失 section，不能覆盖已有 section `api_key`。schema、key、endpoint、model 或 calibration 在首个请求前失败时必须 `blocked|unavailable` 且 provider calls=0；key 不进入 payload、receipt、cache、bundle 或报告，绝对 config path 只进 host-only receipt。
- Provider adapter 每个 `(provider, request_identity)` 只允许一次 HTTP attempt（`retry=0`）；编译器恢复是单独的有界逻辑：source 全局最多 12 次 recovery call、单 source 最多追加 3 次，quality projection 校验失败最多再发 1 次完整 Qwen 页面。质量事实校验固定一页一请求，避免多页响应的 page identity/结果数漂移。每次 recovery 必须落 trace、hash 和 call plan，不能拼接或由 Python 改写正文；耗尽预算后保留 Audit-only/not_released。
- `compiler.py`：raw snapshot、Evidence、ReaderPage、Home、Audit、RunManifest。
- `providers.py`：Qwen typed semantic output、Jina selected route；key 只在内存。
- `publisher.py`：输出 preflight、manifest/tree hash、原子提交；不生成或改写质量对象。
- `simple_cli.py`：参数解析和结果摘要。
- `quality.py`：唯一纯质量裁决边界；读取本次 Reader/Home/Audit/route ledger 和 CompanyBrain observation，返回 `knowledge-digest-quality-result.v3`，不生成正文、不落盘；compiler 只把中间 quality view 交给 M402 host evaluator，host evaluator 是 `quality-result` artifact 的唯一 writer，publisher 只提交已生成的 bundle 字节。`quality.py` 只使用 `DIM-01.route`、`DIM-02.taxonomy`、`DIM-03.business-answer`、`DIM-04.page-type`、`DIM-05.reader-audit`，不接受旧自由文本维度。
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

## ARCHIVE-NON-ACTIVE: 历史计划（非生效）

> 以下所有内容（包括 `Repair mini-task plan v2`、R1–R5 和旧命令）都是历史执行记录，不再授权运行；当前唯一实施计划是本文件顶部 v4.2。

## 当前目标和判断标准

- 89 条 raw 资料先快照、保留空源和全量 CoverageLedger；87 条普通 present 非空来源必须逐条尝试 source-digest，但只有当前 raw→Block→Claim→semantic-frame route support 通过且 Qwen Reader 闭包完整，才算成功 Reader。唯一 SND entry 只有在完整 `semantic_zero_match_certificate.v1` 存在时才生成 diagnosis Reader/guard 闭包，否则只能 Audit-only/not_released；唯一精确 known_empty 仅 Audit；任何其他 canonical present 缺 Reader 都让包级 released 谓词失败。`duplicate_alias` 只有在自身 coverage/Claim/Audit/link 完整、`canonical_source_id`/hash 匹配且 closed 时继承 canonical Reader link，不生成第二个 Reader；alias 缺闭包或绑定不符仍阻断 released，不能用整篇原文包装成 Reader。
- 六个冻结 QualityCase 通过真实 embedding 问题/场景路由，Reader 只发布五类业务答案页；每个 Reader 单元都能从 Audit 回到 Claim、Block、hash、locator。
- 五个维度逐 case×projection 严格比较：问题/场景路由、五轴分类、业务化答案正文、页面类型、Reader/Audit；任一不是 `KD_WIN`、任一 guard/lineage/source closure 失败，终态 `publication_status=not_released`，并用 `outcome/reason_code` 保留具体原因。
- 执行顺序固定：无 provider 的 D0 根因/路由预检 → R1–R4 实现 → focused/full tests → `mini_task.implementation` terminal clean → M401 → M401-R → M402 真实 89 条运行。`mini_task.design` 只作可选 advisory；D0 未通过时保留 blocked attempt，不生成伪造 promotion；M401 只复核 D0 的历史限制记录和当前实现证据。

## 复用边界

- 复用 `llm.py` 的 OpenAI-compatible Qwen client、`embedding.py` 的 Jina client、calibration binding、稳定 source identity 和现有原子 staging 思路。
- Task5 只在隔离模块中扩展，不改正式 `pipeline.py` S1–S6；Task5 provider 失败、语义不确定、冲突、空源、路径不安全和审查不可用都 fail-closed。

## 当前纠偏冻结（2026-08-21）

本节优先约束本轮继续执行，直到重新取得对应的 design/implementation review 证据：

- 质量比较双方统一使用 `0-100` 可观察分数；证据绑定、Audit 闭合和 RenderLedger 只能决定是否可用/可发布，不能转换成 KnowledgeDigest 私有加分。
- `KD_WIN` 必须同时满足真实可观察分数严格高于 CompanyBrain、同维度存在冻结且相容的 CompanyBrain gap、逐原子严格改进且无回退、Reader surface 和 Audit evidence 完整。没有真实 gap 或逐原子映射时不得用 `kd_evidence_strength`、平均分或其他替代理由制造胜出。
- Provider 输出是唯一 Reader 业务文案来源。编译器不得在输出后追加必答标签、路由标签、分类标签、页面类型标签或业务答案前缀；缺少 required atom 时失败并进入 Audit，不得用 `compiler_overlays` 修复表面文本。
- v28–v33 是失败候选，v34 是取消运行；旧报告和旧评分不可作为新合同的通过证据。新的质量合同变更必须先重算 fixture/config hash，再运行离线聚焦测试。
- 本轮顺序固定为：合同纠偏 → focused offline tests → 真实垂直切片 Reader/Audit 生成与逐 case 复核 → 在切片完成诊断复核且没有 global fatal 时，继续同一任务内的 89 条全量 → Downloads 正式结果审查。切片复核是强制的诊断检查点，不是“切片五维全通过后才允许 full”的前置门；预期 `source_not_in_slice/not_evaluable` 和其他 slice-local 语义失败都必须留下复核 receipt 后继续 full，但会阻断最终 `released`。身份、配置、预算、输入、锁、传输或发布等 global fatal 才立即停止全 run；不得用下一轮 provider 重试掩盖失败。

### 用户复核后的输出与全量内容修正

- 全量合同：87 个普通非空来源各走一次 Qwen `source-digest`；SND replacement 用固定扫描且需逐 Block `semantic_zero_match_certificate.v1`，否则 Audit-only/not_released；known_empty 只进 Audit；失败不回退原文。
- 公开合同：唯一入口为 `bundle/`，Reader 为 `products/<product>/<page-type>/<readable-title>.md`；Audit 合并为人读入口 `Audit.md` 与 `_audit/` 下十一份固定 machine files（含 `companybrain-route-snapshot.json`、`raw-coordinate-map.json`、`source-not-documented-zero-match.json`、`source-not-documented-verifier.json`、`run-result.json`）；禁用 `modules/boundaries/knowledge` 和 hash 文件名。
- provider 合同：typed JSON 使用 semantic-output-v2，`title==expected_title`；source-digest/SND/policy/layout authority 已冻结，漂移必须新版本并重审。
- 以上是同一 Task5 的合同变更；历史根因 identity/离线门禁只约束历史回放，不得被当前候选替换。当前 raw-only provider 启动前必须绑定新的 raw/source-scope/input identity 和当前实现合同；旧 v1 和旧 fallback 仅作历史。
## Repair mini-task plan v2：provider-backed semantic compiler

### Canonical contract ownership

`spec.md` 是产品行为、用户边界、失败语义和验收标准的权威；`plan.md` 是实现前冻结的 schema、canonical bytes、文件边界、证据生命周期和 gate 依赖的权威；`tasks.md` 只把这些权威拆成可执行卡片、命令和 STOP 条件，不得引入第二套字段或序列化规则。三份材料中必要的重复只作交接索引；发现冲突时以 `spec.md` 的行为合同和 `plan.md` 的机器合同为准，tasks 必须停卡并同步修正。M401 packet 记录三份材料的 current snapshot/material 绑定，防止实现阶段静默漂移。

### D0 — design successor 前的根因与 89 条路由预检

D0 是 `mini_task.design` terminal-clean 的前置，不是 M101 的内部补步骤。owner 是 R1/M101；运行无 provider、无 embedding、无 RED、无代码写入，固定入口为 `scripts/task5_reader_quality.py root-cause-preflight --root-cause-input-manifest config/task5-root-cause-input-manifest-v1.json --root-cause-contract config/task5-root-cause-evidence-v2.json --raw-input '/Users/Hugh/Downloads/confluence 原始数据' --companybrain '/Users/Hugh/Hugh/Knowledge/CompanyBrain' --evidence-root quality/evidence/task5 --network-policy deny`。它先锁定当前 task snapshot/material，逐项读取五个 `RC-*` 输入并核对 manifest 的 snapshot/file/byte/hash；然后写不可变 `root-cause-evidence` attempt，逐条绑定 blocking/major observation、CompanyBrain 的 `case × projection × dimension` 配对、合同缺口和 repair mapping。任一输入漂移写 `blocked` attempt，`provider_calls=embedding_calls=0`，不 promotion。

D0 同时对当前 raw 的 89 条清单生成 provider-free source-scope ledger：逐条记录 source identity、快照、内容 hash、Block/Claim 闭包、空源/重复状态和 route attempt 状态。它不要求原文预先存在 question、page_type 或五轴业务标签；这些由 Qwen typed output 从单源 Claim 生成，再由 route verifier 做逐字段 Claim/frame/locator 校验。87 个普通来源必须逐条尝试 Qwen；语义路由失败的来源写 Audit-only，不能静默丢弃。只有 post-provider route closure 87/87、Qwen typed compile、Reader/Audit lineage 和五维严格比较全部通过，release predicate 才能继续为真；不能用文件名、目录或整篇原文补齐语义事实。root-cause evidence 和 source-scope receipt 必须绑定同一 current material/input manifest。

当前已知事实是精确 `RC-USER-V50` 路径只剩 0 个普通文件（只剩空的 `audit/`、`products/` 目录），与冻结的 652 文件/111865500 bytes 不符；同时 repair baseline 的既有 preflight 已记录 `config/task5-provider.example.json` hash drift，当前无 provider 复查实际 hash 又变化为 `a3f506759552c510c4572023e3cc6adaf95250f732ff4d9243304c8f50c00eb9`。因此历史 D0 回放必须 `blocked`，不能用 v47/v49/Downloads 候选替代、不能恢复/覆盖漂移文件，也不能把 H-001–H-006 直接当作已证实根因；这不阻断另行绑定当前 raw 89 条的候选预检，候选失败仍只能 `not_released`。

### Goal

在同一 Task5、同一 89 条 raw 输入和同一垂直切片边界内，修复真实编译入口：Qwen 负责 typed semantic compile，embedding 负责实际问题/场景路由，evaluator 读取真实 Reader/Audit 和冻结 CompanyBrain snapshot 重算五维质量。provider 失败不生成 raw Reader；运行中可有 `candidate` 检查点，任何终态质量/完整性失败统一为 `publication_status=not_released`，具体 `outcome/reason_code` 不得丢失。

### WorkflowHub review metadata boundary

WorkflowHub outer `stage` 固定为 `build-code`；本次内层审查用 `review_kind=mini_task.design`、`phase_id=mini-task-design`，不能把内层值写入 `stage`。在任何设计 provider dispatch 前，adapter 必须先通过当前 authenticated make-decision parent preflight；缺 parent 立即 blocked 且 provider calls=0。`mini_task.design` packet 只含四份材料和 contract/skill，不含 raw、CompanyBrain 或完整 authority；设计检查声明与 rehash/STOP 责任。

`workflowhub-identity.v1` 只有 `design_preflight`、`implementation` 两种 handoff。当前 design packet 的 host evidence 绑定 parent canonical stage-outcome 的 result/attempt ref+SHA、独立 `attempt_id`、原始需求/Talk attestation、当前 snapshot/material revision/material_id、worktree id、WorkflowHub `design_review_contract_id/design_review_contract_hash/semantic_hash`、TaskKernel writer attestation 和可重算 validation receipt；canonical provider projection 的 `authenticated_parent.attempt_id`、`parent.attempt_id`、handoff `validation.parent_attempt_id` 与 validation receipt `parent_attempt_id` 必须等于同一个 parent attempt，不能只靠相同 result/attempt 路径。Task5 `runtime_contract_id/runtime_contract_hash/semantic_contract_id/semantic_contract_hash` 另行绑定，不能把两套合同混成一个 `contract_id`。host 先重算并拒绝 scalar identity。缺失、循环、漂移或校验失败在 review/raw/provider 前 `blocked`、exit 2、observed_calls 0；design clean 后 adapter 才生成 implementation successor。

Implementation successor 不是一个“文件存在”标记：WorkflowHub authenticated adapter 只有在 M401-R promoted receipt 通过后，才能写 `quality/evidence/task5/workflowhub-implementation-handoff.json`。它必须符合 `workflowhub-implementation-successor.v1`，同时绑定 design review 的 result/attempt/report ref+SHA、implementation review 的 result/attempt/report ref+SHA、M401 packet/M401-R receipt ref+SHA、全部 finding dispositions、当前 snapshot/material/worktree、WorkflowHub writer attestation 和 Task5 runtime/semantic identity；固定 `review_kind=mini_task.implementation`、`terminal_status=semantic`、`terminal_clean=true`。Task5 只读消费该 host-owned handoff；M402 在读 raw/CompanyBrain 和首个 provider 前复核 canonical SHA，缺失/漂移/未处置 finding 即 `blocked/calls=0`。

`material_id` 是语义材料身份：读取 provider-visible manifest，按 UTF-8 path byte order 排序每项 `{path,bytes,sha256}`，排除 `manifest.json` 与 `canonical-evidence.json`，以无空格 UTF-8 JSON array + LF 求 SHA-256；完整 delivery manifest 仍逐项绑定两者实际字节和 SHA。该 recipe（`workflowhub-material-identity.v1`）必须同时写入 handoff、validation receipt、provider binding 和 packet；这样 handoff 可携带自身 material_id 而不产生自引用哈希。

身份派生不能靠手填摘要：Task5 `runtime_contract_hash` 的唯一算法是读取 `config/task5-runtime-authority-map-v1.json` 的 `authorities`，按 `key` 的 UTF-8 byte order 排序，保留每项完整七字段 `{key,path,schema,actual_sha256,canonical_sha256,rehash_owner,role}`，对数组和对象递归按 UTF-8 key 排序，序列化为无空格 UTF-8 JSON array 加单个 LF，再求 SHA-256；当前值由该 map 的实际字节计算，不在 plan 中复制。map 自身的 actual/canonical SHA、17 项纳入集合和 5 项排除集合仍独立校验，不能用 map SHA 代替 derived runtime hash。WorkflowHub `semantic_hash` 不属于 Task5 runtime hash：必须由 WorkflowHub `buildSemanticProjection()` 重算，使用 `projection_version=wh-review-semantic-projection.v1`、`surface=mini-task/design`、当前 `contract_id/contract_hash`、`stage-materials.json` 注册的字段列表和 provider-visible fixed materials 过滤后的 semantic input；canonical projection 递归按 key 排序，使用 `JSON.stringify(projection)`（无 LF）求 SHA-256。M401/M402 只接受 authenticated handoff/packet 中的值与该重算值完全相等，禁止 caller 自报或把 `provider_semantic` 文件 SHA 冒充 WorkflowHub semantic hash。

Task5 运行合同的 `runtime_contract_id` 固定为 `task5-reader-quality-provider-v2`；`runtime_contract_hash`、17 项 authority 的实际/规范化 hash 和 5 项排除项只从 `config/task5-runtime-authority-map-v1.json` 读取。不要在 plan 中维护第二套 hash 副本；WorkflowHub review 合同另行绑定。

### Frozen boundary

- **只读输入**：`/Users/Hugh/Downloads/confluence 原始数据`、`/Users/Hugh/Hugh/Knowledge/CompanyBrain`、`config/task5-slice-cases-v1.json`（schema=`task5-slice-cases.v1`，actual SHA-256=`4ebccc3d151dd805ed27f1394bff49298e3fdf7b9f3d813f089f5eb30efb96ef`，canonical=`f3337ac149e2a9bb374e8adf7b86a0585f0a59bea91bf93607c8d2a257d4e764`）、`config/task5-source-page-manifest-v2.json`（schema=`task5-source-page-manifest.v2`，actual SHA-256=`b7d6e3f59c0c6ccc6fd04a059007c7a320fd40e85af1d090686a6a0d8272107f`，canonical=`46d65dc22e3b822efa3dc7c965264378b054556e807620837e4b25e2643ab0b1`）、`config/task5-companybrain-observation-v2.json`（actual SHA-256=`c075caef3933360522935798f81f728662ad6cc69e7825ec61d1ab814197d313`，canonical=`17787d2106686604bc30aa76386ccc79a85d79908e6f65685e4f6cc2dd74fa12`）和 `config/task5-quality-result-v3.json`（actual SHA-256=`4e41ef9def7c1f08872f6ffc8676a3ebad6ff7425adc4a14b3a41ba362175ef8`，canonical=`2de7c3aa87c6a193f29c941ecf9333ebbd03320a05e35122dff4c65baf34ad80`）。
- **只读运行配置**：`config/task5-reader-quality-provider-v2.json`（schema=`task5-runtime-config.v1`，文件 SHA-256=`c0a166530cc9cfa05b602c2fd2e57845eaa58f59b5dadf0b87434de9c2a37f18`，canonical SHA-256=`0974d48eb51a7b8b52253968330ec67003b6a300c038f08cc01b4893ea6a7307`）；它是 M402 的运行参数绑定，不再独自声称 runtime map；必须和 authority-map 一起校验。
- **SND authority**：`config/task5-source-not-documented-contract-v2.json`（actual SHA-256=`762f09595fe33d33531dd373cb0bf4f3cf1ee468442d0ebccb68314af7534fa5`，canonical=`253de24de01625c4fa14c5bfab57e81c3ef56dbbd6319fd89f4150152b4263fc`）；v1 仅作历史，v2 冻结 `snd-status-v1`、逐 Block `semantic_zero_match_certificate.v1`、独立 deterministic verifier 和 `semantic-zero-match-verifier-receipt.v1` 的 attempt/promotion/public projection 合同，缺 verifier receipt/certificate 只能 Audit-only/not_released。
- **机器证据合同**：`config/task5-machine-evidence-contract-v1.json`（actual SHA-256=`df96f45ab66aa58c02867834ea1d3f01051fb750a401ce2c71c46d52d0eb01ae`，canonical SHA-256=`2afc28ccabd930d77ddf9278f546b1a81b3d72e6df66b129d00b70406685f882`）；它冻结 parent/Talk projection、S0/S1 preflight、CompanyBrain host/public snapshot、SND certificate/verifier receipt、raw-coordinate map、output lock、directory manifest、failure evidence、run-result、root-cause 和 implementation successor 的字段/绑定/禁字段。
- **只读运行结果合同**：`config/task5-run-result-v1.json`（schema=`task5-run-result.v1`，文件 SHA-256=`8fea27acc460007fb0ac14ea90e92dfe7580f5bc7f34248d2e3cb5a462096858`、canonical SHA-256=`bbad39d78de3feb29b9a49367caa3187581f32953e53957310dc1904d6395f66`）；只有已创建 output/staging 的 run 才必须写 `bundle/_audit/run-result.json`；S0/S1 失败改写入 `quality/evidence/task5/run-preflight/attempts/<attempt_id>/preflight-result.json`，不创建不安全 output 只靠 shell exit 判断。
- **最终输出**：用户指定的 Downloads 新目录；发布 staging 固定为 Downloads 同级、同一文件系统的 `<output>.staging.<run_id>.<owner_nonce>`，`/tmp` 仅可放不参与发布的诊断缓存。
- **根因证据输出**：R1/M101 在任何 provider/embedding 前读取 `RC-OLD-TASK4`、`RC-USER-V50`、`RC-CURRENT-BASELINE`、`RC-RAW-89`、`RC-COMPANYBRAIN`，生成 `quality/evidence/task5/root-cause/attempts/<attempt_id>/root-cause-evidence.json`，通过后 promotion 到 `quality/evidence/task5/root-cause/root-cause-evidence.json`。每行必须绑定输入 snapshot/tree/manifest hash、观察 locator、合同缺口、修复 owner/ref/status；M401 重新验证并把 AC-020 绑定到 packet。旧研究 Markdown 只能作线索，不能作证据替代；缺失或漂移即 `blocked/calls=0`。
- **允许修改**：Task5 runtime、Task5 provider/config、Task5 quality evaluator、Task5 acceptance tests、四份材料和本 ADR；实现阶段的文件边界以「Repair file boundary v2」为唯一准则。
- **禁止修改**：正式 `src/knowledge_digest/pipeline.py` S1–S6、Task4 代码/产物、CompanyBrain、raw source、用户已有 Downloads 产物；不建新 task、不引入数据库/向量库/调度器。

### Design-review authority appendix

审查包不复制 89 条 raw 文件或 CompanyBrain；下面是 packet-visible 的冻结夹具清单。实现前和 M401 必须对实际文件重算 SHA-256，并同时核对条目摘要；路径、hash、数量或关键枚举不一致就 STOP，不能从摘要猜测 authority。

该 appendix 只证明设计材料引用了哪些外部 authority，不把摘要或路径当作已验证的文件字节。M101 baseline bootstrap 只验证 handoff、baseline 和五项根因输入/证据，生成 `task5-baseline-preflight.v1`；它不承担完整 external-authority appendix 的唯一验证职责。M102/R1 是 provider、embedding、R1 promotion 和 M102 前的唯一 external-authority validator：它必须逐项读取 runtime map、17 项纳入 authority、5 项排除项、calibration manifest/artifact 和命令显式传入的 authority，校验存在性、schema、actual SHA、canonical SHA、条目摘要和相互引用，并把 `included_keys`/`excluded_paths`/derived runtime hash 写入 R1 receipt；任何缺失、不可读、漂移或 schema 不匹配都只能 `blocked/calls=0`，不允许把设计审查或 M101 bootstrap 当作替代证据。

| authority | SHA-256 | packet-visible entry summary |
| --- | --- | --- |
| `config/task5-runtime-authority-map-v1.json` | actual `2f4df2ac…`; canonical `7c1f202c…` | 17 项 runtime 纳入 authority、5 项排除项、rehash owner 和 derived runtime hash 规则；唯一 runtime 集合 authority |
| `config/task5-machine-evidence-contract-v1.json` | actual `df96f45a…`; canonical `2afc28cc…` | parent/Talk、preflight、host/public snapshot、SND certificate/verifier receipt、coordinate/lock/manifest/failure/run-result、root-cause、implementation successor 机器证据合同 |
| `config/task5-reader-quality-provider-v2.json` | actual `c0a16653…`; canonical `0974d48e…` | runtime-config.v1；M402 provider-required 运行参数，绑定 v2 case/baseline/result/observation/source-block-claim/path-relation/handshake/layout/machine-evidence/root-cause/semantic-closure identity，不含凭据 |
| `config/task5-source-block-claim-contract-v1.json` | actual `02898de0…`; canonical `4baa6760…` | Source→Block→Claim parser/ledger、完整覆盖、稳定坐标和 Claim identity authority |
| `config/task5-reader-path-relation-contract-v1.json` | actual `c3f12166…`; canonical `16de1b3c…` | relation parser、五类 ReaderTaskPath、route descriptor 字段支撑、stage aliases、ambiguity 和负例 authority；canonical hash 为 loader 派生 identity，不回写文件 |
| `config/task5-provider-config-v2.json` | actual `c6923528…`; canonical `e28334be…` | provider-required config schema；Qwen/Jina const、retry=0、api_key 优先、api_key_env 兼容回退、Unicode code-point input limit semantics、secret/identity contract |
| `config/task5-source-page-manifest-v2.json` | actual `b7d6e3f5…`; canonical `46d65dc2…` | 89 entries；source-not-documented 命中时替换该 entry 的 source-digest，不增加第二次请求或第二个 Reader；含 source status/hash/bytes/lines/locator |
| `config/task5-quality-cases-v2.json` | actual `8d2a5024bce31bd48709d363bbf8cf578b18b46be732f58e4bd133f881c32f67`; canonical `281ced2464a2d7dfd035aecf084cc21ef87ed8f8c6485993a6287375e8af1654` | 6 cases、5 dimensions；语义 contracts 冻结五项评价入口；Q-OPR-01/Q-BND-01 是多 projection case |
| `config/task5-companybrain-baseline-v2.json` | actual `ba69f3ce…`; canonical `43225cd4…` | 10 entries；8 个 projection keys；每 entry 显式 projection、locator、evidence level |
| `config/task5-slice-cases-v1.json` | actual `4ebccc3d…`; canonical `f3337ac1…` | 11 cases、14 descriptors、13 risk tags；`G-EMPTY-89` 是唯一 known-empty case |
| `config/task5-calibration-manifest-v1.json` | actual `b18610b2…`; canonical `dd44cd1f…` | `phase4-jina-embeddings-adopted-v1`；Jina 1024d；artifact SHA=`c31b1f8c…` |
| `evidence/phase4/calibration-artifact.json` | actual/canonical `c31b1f8c…` | adopted；25 cases；endpoint `llm.paxszapp.com/v1`、model `jina-embeddings`、dimension 1024 |
| `config/task5-provider-contract-handshake-v3.json` | actual `c15c0612…`; canonical `fc821c355…` | fake/local handshake；按 route_case_matrix 覆盖 `source-digest`、`quality-reader`、`source-direct-audit` 全部 LLM route、embedding route、成功/拒绝/no-network/calibration identity |
| `config/task5-provider-prompt-contract-v1.json` | actual `1e8888cb…`; canonical `791ac7e1…` | prompt/template identity；三类 route、expected title、closure、claim semantic frames、typed output 和 prompt 变更必须换 contract |
| `config/task5-provider-semantic-output-v2.json` | actual `630d7757…`; canonical `3a712852…` | route-scoped Claim closure；每个 supported Claim 先生成 semantic frame，再允许 Reader statement |
| `config/task5-source-digest-contract-v2.json` | actual `247fbc8…`; canonical `5449076d…` | 87 个普通来源各一次 Qwen source-digest；先过 route-verifier.v1，再做单源 closure、semantic frame、summary/slots/rewrite gate；失败 Audit-only |
| `config/task5-source-direct-contract-v1.json` | actual `ba0d350f…`; canonical `c1fc0f97…` | one-source closure；6 negative cases；Audit/coverage only；forbids raw full-source |
| `config/task5-publication-layout-v2.json` | actual `26764a58…`; canonical `f8d75e90…` | bundle exact tree、Home reachability、Reader path、十一份 machine audit files（含 public CompanyBrain snapshot 和 SND verifier receipt） |
| `config/task5-source-not-documented-contract-v2.json` | actual `762f09595fe33d33531dd373cb0bf4f3cf1ee468442d0ebccb68314af7534fa5`; canonical `253de24de01625c4fa14c5bfab57e81c3ef56dbbd6319fd89f4150152b4263fc` | G-SOURCE-ND diagnosis-status Reader、`snd-status-v1`、固定文案、Audit scan、逐 Block certificate、独立 verifier 和 receipt contract；无 verifier/certificate Audit-only |
| `config/task5-external-processing-policy-v1.json` | actual `145339af1da2170e386ccbb41a82e8041e1e08743ae610d5b20aa48f3c47b01a` | endpoint/scope/source-sensitive scan authority；pre-socket allowlist 与 M401 deny profile；当前不主张 retention/no-log |
| `config/task5-source-sensitive-content-scan-v1.json` | actual `1253ab1e1e31ae7d737183d8ac8ffb85d9e5f83a2bc76b534195bbc4339d53d5`; canonical `5836aa46…` | 完整 raw/NFKC 扫描算法、最终 LLM wire payload/embedding 出站字段、匹配回执和 fail-closed 状态 |
| `config/task5-semantic-frame-v1.json` | actual `e864fd5f…`; canonical `4f00f2e4…` | subject/predicate/object/action/order/quantity/condition/polarity/scope 的闭合中间层 |
| `config/task5-replay-store-v1.json` | actual `56e2198d5bb1d16c0c99d61fb3abd0e5a728619622d1d2fe8ac0409a25bd6457`; canonical `70269988…` | real provider receipt、HTTP attempt、run/compiler/parser identity 绑定的 owner-only replay store |
| `config/task5-m401-r-review-receipt-v1.json` | actual `b1e47525cc224af1d12c675e5cda2903e9aacd7355557c2054f9d42643b92e6c`; canonical `74584b624c2c672e6aa4f6d76ca98165f2a06e2fb5c40fca36b39f1807990d1a` | M401-R terminal-clean receipt and M402 dependency |
| `config/task5-companybrain-observation-v2.json` | actual `c075caef3933360522935798f81f728662ad6cc69e7825ec61d1ab814197d313`; canonical `17787d2106686604bc30aa76386ccc79a85d79908e6f65685e4f6cc2dd74fa12` | five-dimension CompanyBrain observation, per-atom status and gap contract |
| `config/task5-run-result-v1.json` | actual `8fea27ac…`; canonical `bbad39d7…` | 运行级状态/退出码/WorkflowHub identity/产物绑定；唯一输出 `bundle/_audit/run-result.json` |
| `config/task5-root-cause-input-manifest-v1.json` | actual `2909de6d…`; canonical `52e86dd5…` | 五个固定历史/基线/raw/CompanyBrain 输入及目录、manifest、当前 baseline 身份；不可用研究文档替代 |
| `config/task5-semantic-frame-field-closure-v1.json` | actual `d2a560e7…`; canonical `a3c7bd6b…` | Reader 逐字段闭合算法、受限 normalizer、阻断原因码和负例；独立于 semantic-frame 数据结构 authority |
| `config/task5-root-cause-evidence-v2.json` | actual `6b75d70e…`; canonical `cd4751b9…` | R1/M101 观察、CompanyBrain 配对差异、合同缺口、因果修复映射和 89 条 source-scope promotion 证据；缺输入/locator/hash/比较/映射只能 calls=0 |

该 appendix 是设计审查的可核对摘要，不是第二套数据源；完整 JSON 仍由上述路径和 SHA 唯一决定。

`config/task5-provider-config-v1.json` 保留为历史 legacy schema；Task5 v2 使用 `config/task5-provider-config-v2.json`，允许本地 `api_key` 优先、`api_key_env` 兼容回退。`config/task5-provider.example.json` 只是可修改的脱敏示例，必须符合对应 authority。任何用户配置（包括 `~/.config/knowledge-digest/config.json`）先按 v2 schema 校验，再把 config path、canonical config hash、provider identity 和 calibration refs 绑定到 R1–R4/M401/M402 receipt。

Fixture rehash owner 固定为：M102/R1 先读取 runtime authority map，再重算其 exact sorted 17-key set：`external_processing_policy`、`machine_evidence`、`publication_layout`、`provider_handshake`、`provider_prompt`、`provider_semantic`、`reader_path_relation`、`reader_quality_provider`、`replay_store`、`root_cause_evidence`、`root_cause_inputs`、`semantic_frame`、`semantic_frame_field_closure`、`source_block_claim`、`source_digest`、`source_not_documented`、`source_sensitive_content_scan`，并逐项核对 path/schema/actual/canonical SHA、5 项排除集合和 derived runtime hash；R1 receipt 必须记录 included/excluded 集合 exact equality，后续 gate 只消费该 receipt。M102 同时重算 provider config、calibration manifest/artifact 和 root-cause input/evidence；M252/R3 在质量 oracle 首次消费前重算 quality cases、CompanyBrain baseline/observation、source-direct contract、source-page-manifest、slice cases，并同时核对 actual/canonical SHA；M301/R4 在 runtime 首次读取前再次校验 source-page-manifest、slice cases、publication/machine-evidence；M401 finalize 再重算上述全部 authority（含 run-result schema）并把每个 path/SHA、canonical SHA、纳入/排除和缺失/漂移原因写进 packet。任何 fixture 不存在、SHA 不符、schema/关键枚举不符、map 出现 extra/missing authority 都在 provider 前 `blocked`，保留失败 receipt，不能只相信 appendix 摘要。

### File map

`task5_provider_config.py`/`task5_provider.py`：R1/R2 provider 身份与 typed 编译；`task5_semantic_model.py`：Claim/KnowledgeUnit/lineage；`task5_quality_gate.py`：R3 五维与 CompanyBrain observation；`task5_projection.py`：Reader/Audit/route projection；`task5_runtime.py`：R4 slice→full、锁、Downloads；`scripts/task5_reader_quality.py`：R1-owned preflight/gate/M401/M402 CLI，R4 只调用；对应 acceptance tests 按 R1–R4 分组。

- **ADD/MODIFY/READ-ONLY/DO NOT TOUCH**：完整路径 allowlist 见下一节「Repair file boundary v2」；权威 fixture 的路径、SHA 和摘要见前面的 authority appendix。实现阶段不得改写 frozen authority；需变更时必须先新版本化并重新 design review。

四份设计材料 `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` 不是实现路径。它们只能在当前 `mini_task.design` 尚未 terminal clean 时同步修正；一旦取得 terminal clean，WorkflowHub snapshot/material 会把四份材料和 frozen authority 一起锁定。实现、M401、`mini_task.implementation` 和 M402 阶段不得修改它们；若发现必须修改，先停止当前阶段、生成新的 design snapshot/material 并重新跑 `mini_task.design`，随后重新校验所有 gate 的设计 hash。

### Repair file boundary v2

R4 的 `ADD/OWN` 还明确包含 `quality/evidence/task5/snd-verifier/attempts/<attempt_id>/verifier-receipt.json`、`quality/evidence/task5/snd-verifier/verifier-receipt.json` 和 M402 真实 bundle 的 `bundle/_audit/source-not-documented-verifier.json`；attempt receipt 的 owner 是独立 deterministic SND verifier，promotion view 只能由通过 attempt 原子更新，M401/M402 只读消费。三条路径的 schema/ref/SHA、promotion、失败保留和 rollback exclusion 必须进入 R4 gate receipt；没有路径授权不能以“机器证据合同已声明”代替。

实现阶段只能修改上面 `ADD/OWN` 与 `MODIFY` 列出的路径；不得新增未列出的代码、配置、测试、ADR 或脚本路径。`READ-ONLY frozen authority` 及 `quality/evidence/task5-repair-baseline-v2.json`、`config/task5-slice-cases-v1.json`、`src/knowledge_digest/task5_source_model.py`、历史 v1 fixture、`docs/adr/0009`–`0011` 和旧 P1–P4 evidence 都是只读输入；baseline 的 canonical bytes 已放入本计划 appendix，不能以“实现阶段新建”解释缺失。设计材料本身可以在 `mini_task.design` 重新审查前同步修正；设计审查通过后，代码阶段不得以实现便利为由扩大文件边界。
每个 R1 attempt 还允许在同一 attempts 目录写 `baseline-preflight.json`；它是 M101 bootstrap 证据，不是产品输出，必须由 R1 attempt 引用，其他 gate 只读复核，不能覆盖或 promotion。

RED/GREEN 的 receipt 状态必须分离：RED 测试写 `quality/evidence/task5/repair-gates/red-tests/attempts/<attempt_id>/<gate>.json`，schema=`task5-red-test-receipt.v1`，`status=expected_failed`，只证明实现前的负例确实失败，不能写入 R1–R4 promotion view，也不能以 `failed` 状态阻断 GREEN。GREEN 卡必须显式消费对应 `red_test_ref+sha256`；M101 的 `baseline-preflight.json` 由 `validate_baseline_contract()`→`replay_root_cause()`→`write_baseline_preflight()` 的独立无 provider bootstrap 生成，不是 M101 RED receipt。只有 GREEN 的 `task5-repair-gate-attempt.v1` 使用 `status=passed|failed`；GREEN failed attempt 才阻断下一 gate。这样“测试预期失败”和“实现闸门失败”不会共用一个状态机。

R1/M101 另允许写 `quality/evidence/task5/root-cause/attempts/<attempt_id>/root-cause-evidence.json`，通过后才允许原子更新 `quality/evidence/task5/root-cause/root-cause-evidence.json`。两者必须符合 `config/task5-root-cause-evidence-v2.json`，绑定 `config/task5-root-cause-input-manifest-v1.json` 的 actual/canonical SHA、五个 RC 输入 snapshot/hash、当前 task snapshot/material、旧结果与 CompanyBrain 的 case/projection/dimension 配对差异和逐行 observations/causal_mapping；缺失、不可比较或漂移时 calls=0。WorkflowHub adapter 写入的 `quality/evidence/task5/workflowhub-implementation-handoff.json` 是 host-owned successor，Task5 只读消费，不能由脚本 caller 自报或由 R1–R4 代写。该 successor 必须按 `workflowhub-implementation-successor.v1` 写出唯一 `handoff_sha256`，同时列出 design/implementation 的 result、attempt、report ref+SHA，M401 packet、M401-R receipt、当前 snapshot/material/worktree、runtime/semantic identity、writer attestation 和逐项 finding dispositions；缺任一项或路径越界均不得被 M402 读取。

**Design-successor root-cause gate**：上述根因行在设计阶段只能作为 `H-###/待验证` 假设。WorkflowHub 产生 terminal-clean `mini_task.design` successor 前，R1 owner 必须在无 provider、无 embedding 的 preflight 中调用既有 `replay_root_cause()`，读取 `RC-OLD-TASK4`、`RC-USER-V50`、`RC-CURRENT-BASELINE`、`RC-RAW-89`、`RC-COMPANYBRAIN` 五项输入，并 promotion 一份 `task5-root-cause-evidence.v2`。每条 blocking/major observation 必须同时有输入 ref+SHA、relative locator、`case × projection × dimension` 对照、合同缺口和 repair mapping；缺任一项、不可比较、输入变更或假设与回放不一致，都不得生成 successor、不得写代码，必须新建 snapshot/material 并重新执行 `mini_task.design` review。M101 后续只消费这份 promoted evidence 并重新核对，不是首次发现根因的阶段。

以下是实现阶段的完整可执行边界；`MODIFY` 的 owner 与 before SHA 以 baseline v2 为准，未列路径即越界：

- `MODIFY/OWN`：R1=`src/knowledge_digest/task5_provider_config.py` (`0378edc5d1f692dbeb21c3198f1224bd0599c21be422a5e0d1c85bff9c64f5c3`)、`config/task5-provider.example.json` (`5e782e47d10f2e89d09ae9856bb720eada53382846e6b575b448a1642ae04568`)、`tests/acceptance/test_task5_provider.py` (`8ae5d72268c1f8f934219b9f62047c2d7bd5e461b40a6254af3c9105cb352f31`)、`docs/adr/0012-task5-provider-backed-compiler-repair.md` (`8416ad0229dbe0cfad0ff6349773c765d24a8152c52179599f5ec5ce3e00b5fa`)、`scripts/task5_reader_quality.py` (`ade6c8d730d58e307f5d89a39e8095623cd45c747e7f29234ed1dcb504b9512d`)；R2=`src/knowledge_digest/task5_semantic_model.py` (`1438f02919246cd6ee8591f55093496f8273b029588a8ff055ce3672f9963a36`)、`src/knowledge_digest/task5_provider.py` (`e79948e06266c5353b0a115b0009e7cab8c3e149428e248eec0a98b169acb99e`)、`tests/acceptance/test_task5_source_semantic.py` (`582a17e02e785d2f4d1d6f793ea3719949aa27b5b3c9fb300b0bed172c31f088`)；R3=`src/knowledge_digest/task5_quality_gate.py` (`6110355170e2dabaec5f60d648cfd0a6255795743dbb9f31f9d60f830076abfb`)、`tests/acceptance/test_task5_quality_gate.py` (`07858e7bcfe513c6fc29eff81467b22e23efa81e2228566630294b6d634c89d4`)；R4=`src/knowledge_digest/task5_runtime.py` (`f8c166c6bc3b444c80f2fcb3faa48ae9deb8bb0fc031b4df191f93f5834f36f4`)、`src/knowledge_digest/task5_projection.py` (`643e936888d2a156a86aaa9d83272f4f31fde47b36fe8d611aa94c0b8a5f9304`)、`tests/acceptance/test_task5_full_run.py` (`4ce25a15d497e268ef236ba2c5e242ca68dbb0f74b56b46c11da9a83327ab8be`)、`tests/acceptance/test_task5_projection.py` (`5b2fce045cc7b45b2b375817e1c269f8fecf2238f1698a9968c153b0b72e524a`)。scripts/task5_reader_quality.py 是 R1 的唯一 gate/preflight CLI owner；R4 只能调用它，不能修改它。其余路径单 owner。
- `ADD/OWN`：`quality/evidence/task5/repair-gates/red-tests/attempts/<attempt_id>/<gate>.json`（RED expected-failed receipt）以及 `quality/evidence/task5/repair-gates/attempts/<attempt_id>/{baseline-preflight.json,R1.json,R2.json,R3.json,R4.json,tests/R1.json,tests/R2.json,tests/R3.json,tests/R4.json,inverse/R1.patch,inverse/R2.patch,inverse/R3.patch,inverse/R4.patch,R3-events.jsonl}`；S0/S1 另允许 `quality/evidence/task5/run-preflight/attempts/<attempt_id>/preflight-result.json`，它是 output 目录创建前的 host-only machine evidence。通过 attempt 才能追加固定 promotion view `quality/evidence/task5/repair-gates/{R1.json,R2.json,R3.json,R4.json,tests/R1.json,tests/R2.json,tests/R3.json,tests/R4.json,inverse/R1.patch,inverse/R2.patch,inverse/R3.patch,inverse/R4.patch}`。另允许 `quality/evidence/task5/M401-evidence-packet.json`、`quality/evidence/task5/m401-receipts/attempts/<attempt_id>/companybrain-route-snapshot.json`、`quality/evidence/task5/m401-receipts/{M401-focused-test-receipt.json,M401-full-regression-receipt.json}`、`quality/evidence/task5/M401-R-review-receipt.json`、`quality/evidence/task5/m401-r-receipts/attempts/<review_attempt_id>.json`、`quality/evidence/task5/m402-surface-qa/attempts/<attempt_id>/surface-qa.json` 和由 WorkflowHub authenticated adapter 独占写入的 `quality/evidence/task5/workflowhub-implementation-handoff.json`。这些证据只能 append-only/原子 promotion，不能改写失败历史；successor 不是 Task5 caller 可自行创建的 fallback；M402 surface-QA receipt 是 host evidence，不增加 public bundle 的第十一个 machine file。
- `READ-ONLY`：raw、CompanyBrain、全部 frozen authority/config/fixture、baseline、`CONTEXT.md`、`src/knowledge_digest/task5_source_model.py`、历史 Task4/Task5 产物和旧 evidence、未列的现有源码/测试/文档；`DO NOT TOUCH`：raw 目录、CompanyBrain、旧 Downloads 输出、任何 `/tmp` 候选、WorkflowHub/3rd-review 仓库及其配置、其他 repo、任意密钥/日志/缓存。实现只能在上述 MODIFY 和 ADD 路径写字节。

- `ADD/OWN` 补充：`quality/evidence/task5/M401-companybrain-route-snapshot.json` 是唯一通过 attempt 的 CompanyBrain host snapshot promotion view；它只引用不可变 attempt，不产生质量 verdict，M402 仍重新生成 public snapshot。
- `ADD/OWN` 补充：`quality/evidence/task5/actual-run/attempts/<attempt_id>/quality-result.json`（每次实际运行的不可变质量结果 attempt）和 `quality/evidence/task5/actual-run/quality-result.json`（唯一 promoted quality-result artifact）。R3 quality evaluator 是唯一 writer；run-result、release predicate、M402 surface QA 和 Downloads manifest 只读消费 promoted ref+SHA，不得从各自的 prose、静态 fixture 或重复字段重算另一份 verdict。

### Canonical machine-evidence paths

SND verifier 的 host evidence 由 R4 独占写入并纳入 Repair file boundary：每次 attempt 新建 `quality/evidence/task5/snd-verifier/attempts/<attempt_id>/verifier-receipt.json`，只有 `status=passed` 且绑定当前 source snapshot、certificate、material_id、recomputed/comparison digest 的 attempt 才能原子 promotion 到 `quality/evidence/task5/snd-verifier/verifier-receipt.json`；M401 finalize 和 M402 只读消费 promoted ref+actual/canonical SHA。失败/unknown/blocked attempt 只保留，禁止覆盖、删除或回写实现代码；promoted view 不是 rollback target，回滚只作用于本计划明确列出的代码、测试和 ADR。通过 SND replacement 的真实 bundle 还必须写 `bundle/_audit/source-not-documented-verifier.json`，并由 directory manifest/run-result 绑定同一 promoted receipt。

以下两份证据不是“schema 已声明就算存在”，而是发布树中必须实际写出、加入 directory manifest、绑定当前 source snapshot/content hash，并被指定消费者读取：

- `bundle/_audit/raw-coordinate-map.json`：S1 source snapshot/Block ledger 写出；每个 Block 记录 raw byte/line、canonical code-point 和 canonical→raw segment map。ClaimSemanticFrame、Reader/Audit replay、M401/M402 在发布前读取它；缺失、覆盖不全、重叠、host path/raw bytes 泄漏或 hash 漂移均 blocked/not_released。
- `bundle/_audit/source-not-documented-zero-match.json`：S2 SND analyzer 在任何 SND Reader promotion 前写出；逐 Block 绑定 analyzer id/SHA、source snapshot/content hash、coverage 和 zero-match 结论。SND Reader gate、directory manifest、run-result 和 M401/M402 release predicate 必须消费同一文件；缺失证书不能把 zero-match 变成 Reader，最多 Audit-only/not_released。
- `bundle/_audit/run-result.json`：S2-S4 output/staging 已安全创建后写出，唯一的运行级状态入口；`bundle/Audit.md` 是人读入口，不是 JSON 目录。S0/S1 失败仍只写 repository evidence root 的 preflight receipt，不为了补 run-result 创建不安全 bundle。

`task5-publication-layout-v2` 的 `expected_machine_audit_files` 与 `task5-directory-manifest.v1.required_paths` 必须逐项包含 `raw-coordinate-map`、SND zero-match certificate、SND verifier receipt 和现有八份审计文件，共十一份；写入顺序、owner、manifest entry 和消费者以 `task5-machine-evidence-contract-v1` 为准。SND verifier receipt 只能来自 `quality/evidence/task5/snd-verifier/attempts/<attempt_id>/verifier-receipt.json` 的通过 promotion，并按 `semantic-zero-match-verifier-receipt.v1` 绑定当前 source snapshot、certificate、material_id、recomputed/comparison digest；M401 finalize、M402 release predicate 和 SND Reader promotion 必须消费同一 promoted receipt。文件缺失、额外未声明、receipt 未通过 promotion 或绑定漂移都阻断发布。

补充的证据生命周期优先于下面的固定路径简称：每个 RED 先生成独立 `red_test_attempt_id` 并写 expected-failed receipt；每次 GREEN R1–R4 调用再生成唯一 gate `attempt_id`，所有 GREEN gate/test/inverse 证据先写入 `repair-gates/attempts/<attempt_id>/`，失败、取消、超预算和重跑证据永不覆盖或删除。固定 `repair-gates/R*.json` 是可追加 latest history 的 promotion/index view；只有 GREEN `status=passed` 的 attempt 才能更新 `promoted_attempt_ref`，固定 `tests/R*.json` 和 `inverse/R*.patch` 只来自 promoted attempt。下一 gate 只能消费对应 RED 的 `expected_failed` receipt 加上 `latest_attempt_ref == promoted_attempt_ref` 且 `status=passed` 的 GREEN attempt；没有任一绑定、没有 promotion 或最新 GREEN attempt 失败就 STOP。

M101 在任何 RED 命令、代码写入或 gate receipt 生成前只做已完成 D0 的消费核验：读取 D0 的 `root-cause-evidence` promotion、`source-scope` receipt、当前 input manifest 和 authenticated snapshot/material，逐项比对 ref/SHA；缺失、blocked、漂移或 route support 不完整立即 STOP。baseline 校验仍只在内存读取 `RC-CURRENT-BASELINE` 并核对 `baseline_schema`、actual/canonical SHA、`repair_snapshot.path_hashes`、R1–R4 rollback matrix、ADD/MODIFY before hash、owner 和 patch scope。`replay_root_cause()` 不再在 M101 第一次执行，避免设计 successor 与 M101 互相等待；它只能作为 D0 的独立无 provider 命令运行。`write_baseline_preflight()` 最后把 D0 promoted refs、baseline identity、parent snapshot/material 写入 `repair-gates/attempts/<attempt_id>/baseline-preflight.json`。M101 RED、M102 GREEN 和 promotion 命令必须显式传入并校验同一 D0/baseline receipt；任一参数缺失或漂移时 calls=`0`、不写 gate receipt。

上述 M401 packet 还必须引用 source-direct contract、provider handshake 和 M401-R receipt schema authority 的 path/SHA，并提供 AC-RP-014 trace；它不写生成后的 M401-R receipt/ref/hash。M401-R 只能在当前 packet SHA 和当前 material 上生成 terminal-clean promotion，且只能消费 R1/R3 已通过的 fake handshake receipts，不能把它们当成真实 provider 结果；WorkflowHub authenticated adapter 随后生成 implementation successor，M402 再绑定该 successor 和 M401-R promoted receipt。

### Phase R1 — provider identity/config and preflight

**Goal**：加载用户配置、校验批准 provider、解析环境变量 key、校验 calibration、计算调用预算和稳定 run identity；先用冻结 handshake fixture 以 fake LLM 按 `route_case_matrix` 逐项验证三种 LLM route 的 named success/negative case 及 embedding route 的 typed receipt，再允许实现接入真实 provider；首个网络请求前失败就停。

**Breadth contingency**：R1/R2/R3/R4/M401 各自必须先写本阶段 canonical receipt；阶段失败只保留失败证据并把包置为 `not_released`/真实 `blocked|unavailable`，不得缩小切片或 89 条清单、跳过下游验证、复用旧 receipt 或宣称 released。只有所有阶段最小条件、两次 WorkflowHub review、切片/全量闭包、五维逐 case 和真实产物 surface QA 同时闭合，才允许 `released`。

**Design**：显式 `--provider-config` > `~/.config/knowledge-digest/config.json`；v2 配置允许明文 `api_key`，值只在进程内使用，receipt/report 只写脱敏 identity/config hash；LLM 固定 qwen endpoint/model，embedding 固定 jina endpoint/model。

**Authenticated WorkflowHub identity**：M101 先校验 parent make-decision result/attempt ref+SHA、attempt/material、原始需求/Talk、task/worktree 和 writer，再由 TaskKernel 生成 `workflowhub-identity.v1`；缺失、跳阶段、`build-spec` 补需求或漂移即 STOP。canonical evidence 还绑定 parent full `decision_log.md` SHA、provider `requirements/decision_log.md` projection 路径+SHA、raw requirement 路径+SHA 和三轮 Talk selection ref+SHA；compact SHA 不得冒充 full SHA。后续 gate 只继承该 handoff，拒绝 scalar identity。

**M101 bootstrap contract**：D0 的 `root-cause-preflight` 是 design successor 前的独立、不可跳过的无 provider 阶段；它读取五个固定 RC 输入、生成/校验 v2 根因证据，并生成全 89 条 source-scope ledger。M101 的 `BASELINE_BOOTSTRAP` 只验证已认证 handoff、D0 promoted refs、固定 baseline ref/SHA、本次 attempt、baseline schema/path owner，再写 baseline-preflight。任何 D0/baseline 缺失、漂移、路径未列、before hash/owner/parent 不一致或根因不可比较，都立即 `blocked/calls=0`；post-provider 的 87/87 route closure 由 R2/R4 产生和校验，不得被 D0 预先伪造。gate 不得自行重新生成、替换或只按文件存在放行。

输出固定为 `quality/evidence/task5/repair-gates/attempts/<attempt_id>/baseline-preflight.json`：记录 handoff ref/SHA、认证后的 task/snapshot/material identity、baseline/path checks、promoted root-cause ref/SHA、patch scope、failures 和 outcome；canonical JSON 使用 UTF-8、排序 key、紧凑分隔符、单个末尾 LF，`canonical_sha256` 排除自身。写入必须是新目录、临时文件 + flush/fsync + `os.replace`；禁止创建缺失输入、调用 provider 或触碰未列路径；只有 `replay_root_cause()` 阶段读取 raw/CompanyBrain/历史包，`validate_baseline_contract()` 和 `write_baseline_preflight()` 不得读取这些输入。退出码固定为 `0=passed`、`2=blocked/drift`、`3=malformed/internal`；outer WorkflowHub event 另记 argv、Python version 和 stdout SHA。M102 必须暴露三个可区分阶段并用同一 fixture 做 bootstrap/CLI canonical bytes replay，后续 gate 只消费该 receipt；任一步骤失败即 STOP。

**Tests (RED → GREEN)**：缺配置、明文 key、未知字段、endpoint/model 漂移、缺 key、calibration mismatch、预算不足、secret redaction、precedence、idempotency 和隐式 retry；冻结 `task5-provider-contract-handshake-v3` 的 `route_case_matrix` 必须逐项执行 `source-digest`、`quality-reader`、`source-direct-audit` 的 named success/negative cases，另执行 embedding route 的所有 named cases、canonical request/receipt hash 和 no-network 断言。`llm.retry_attempts`、`embedding.retry_attempts` 只接受显式 `0`；timeout、429、5xx、坏 JSON/部分向量都必须证明不会发第二次 HTTP attempt。

**STOP**：无法证明 provider identity/calibration、预算或 fake LLM handshake 在网络前可算且可回查时，停止，不接 runtime；R1 未 promotion 的 handshake 不得被后续 gate复用。

Calibration identity contract：R1 必须只读 `config/task5-calibration-manifest-v1.json`（SHA-256=`b18610b2a3ffe0dccb854509cd9b826aace0fe18b18af836f6679aebefa8f510`），再读取其 `artifact_path=evidence/phase4/calibration-artifact.json`（schema=`calibration-artifact.v1`，SHA-256=`c31b1f8c78a889dff4cdbbab0fb695871c513844b5c8392d52dbbd8ad33e4c06`）。manifest、artifact schema/SHA、Jina endpoint/model/dimension 必须全部匹配；manifest 或 artifact 缺失、越界、漂移或字段不一致时在网络前 `blocked`。embedding handshake 的 request/success receipt 必须同时写入 manifest ref/SHA 和 artifact SHA；provider config、R1/R3 receipts、M401 packet、M401-R 和 M402 preflight 都必须复核同一 identity，不能只写一个裸 calibration hash。

### Phase R2 — typed semantic compiler and no raw fallback

**Source ledger authority**：实现先读取并 hash 校验 `config/task5-source-block-claim-contract-v1.json`（actual=`02898de03f72ad2ccfe7998cff9b4c4362cde95e71ed3aa0cdd35a5a00ce9b71`，canonical=`4baa67603f01aa1e1f114b08cf352a03d51d67035071feb3894f499af6983639`）。Block parser 按合同冻结结构块、raw byte/line 坐标和完整覆盖；每个 Block 恰好一个 raw EvidenceClaim，Claim 不等于 semantic support。缺块、重叠、坐标漂移、重复/越界 Claim 或 closure 不闭合在 provider 前 blocked；该 authority hash 进入 runtime contract 和 request identity。

**Goal**：复用现有 OpenAI-compatible LLM client，但给 Task5 一个严格 typed JSON contract；模型不能写 Markdown，失败不能进入 raw Reader。`route_kind=quality-reader` 由编译器从已接受的 page surface 派生并验证 ReaderTaskPath 和 Reader surface；`route_kind=source-direct-audit` 只要求 source-backed semantic audit、KnowledgeUnit/Claim lineage、coverage 和 Audit/RenderLedger，固定 `reader_eligible=false`，不得生成 Reader/Home，也不以 ReaderTaskPath 判定通过。Qwen v2 不直接返回 KnowledgeUnit、ReaderTaskPath 或 relation facts。

**Design**：输入是当前 source/block/Claim ledger；Qwen typed output 必须符合 `task5-provider-semantic-output-v2`（SHA=`630d77570a66808fc497800b9b657ebb403e65ada16525b10b0203c286e6efa4`）。每个 Qwen prompt 的长度按 `config/task5-provider-config-v2.json.max_input_chars_semantics` 使用 Python `len(prompt)` 的 Unicode code-point 数，固定上限 `llm.max_input_chars=120000`；request、preflight 和 receipt 记录 `input_chars` 与 `input_length_unit=unicode_code_points`，超限只写 Audit/blocked，不截断、不发送、不重试。编译器先按 `task5-semantic-frame.v1`（SHA=`e864fd5f976a5641ffda5db662eceb2ce85687f5fabf250dc7e337b73f264ae6`）为每个 supported Claim 生成 subject/predicate/object/action/order/quantity/conditions/polarity/scope frame，再接受 Reader statement；新增连接词可保留，但保护语义必须逐字段闭合。`source-digest`/`source-direct-audit` 的 Claim ref 只能来自各自单源 closure；`quality-reader` 允许 selected source closure 内多源 Claim，但每条 Claim 必须带唯一 owner/source/block/locator，并对跨源事实显式标记 `co_support|conflict|unknown` 后通过关系闭包。未知字段、closure 外事实、raw-copy、编译器发明和 raw fallback 一律拒绝。`source-digest` 另受 `task5-source-digest-contract-v2`（actual=`4ae5de71be1cbdbf5987af2b54814ce716412f1e3e219146d7f8f1f7638ec5b2`、canonical=`94af4a1f1d48921b0d2b1de2c59f87b7c4073d38022aa02dc75db7d99256bfa8`）约束：D0 只生成 89 条 source-scope ledger；每条可读普通来源必须尝试 Qwen，Qwen 返回 typed route/page fields 后再执行 `source-digest-route-verifier.v1`，逐字段绑定 question/title/page_type/primary_intent/五轴 support refs、closure 和 support hash。缺字段、支持不明、主意图歧义或 ledger 漂移时只写 Audit，不回退原文；显式 `source-direct-audit` 只进 Audit/coverage。R1–R4/M401 复核 authority path/hash，漂移在 provider 前 blocked。

页面级 oracle 检查最终正文：长度、句数、Claim coverage、source 顺序 LCS、bounded lexical 诊断、一对一和 whole-source rewrite；覆盖/相似度同时超限为 `page_semantic_rewrite`，短来源仍执行长度、raw-copy 和一对一检查。bounded lexical/claim lineage 只能作为诊断，Reader acceptance 必须走 `semantic-frame-field-closure-v1` 的逐字段等价，不能用 `0.80` 覆盖率放行。`copy|unknown` 只进 Audit，不生成 Reader/KD_WIN。完整阈值和负例以 v2 contract 为准。

### External-source safety contract

原始 Confluence 属于 `internal_business_content`；用户已明确授权把必要的 source-backed 片段交给两个冻结的内部代理 endpoint，但实现不能把这理解成“可把整个目录上传”。Qwen outbound 只允许携带当前 route 选中的 canonical source block；Jina embedding outbound 只允许携带冻结的 `route-descriptor.v1` 元数据（title/question/page_type、source identity/hash），绝不携带 `canonical_text`、Block、媒体或未选 source 内容。Jina 调用前必须按 `task5-reader-path-relation.v1.embedding_route_descriptor` 逐字段回查当前 raw Block/Claim ledger 或 authenticated CompanyBrain route observation，并重算 support/closure hash；只闭合路径/hash 但 descriptor 字段无语义支撑时，route=`unknown`、不发 embedding、不得 KD_WIN。两类 payload 都不发送 raw 目录、CompanyBrain、API key、Authorization 或完整本地路径；receipt 只保存 payload hash、长度和 source/block/lineage identity，不保存原始 prompt/response。

ledger lifecycle 固定：`_audit` 写两份人读索引、一个 public CompanyBrain snapshot、四个既有 machine ledger，加 raw-coordinate-map、SND zero-match certificate、SND verifier receipt、run-result，共十一份固定 machine files；每行 canonical JSON+LF，由 runtime 单写者按 `attempt_seq` 追加。compile/response 行绑定 request、source、合同、provider、payload/response/normalized hash；response create-only，冲突写 `response_variant` 到 failure sink。每行 `canonical_sha256` 不含自身字段，directory manifest 绑定十一份文件；SND verifier receipt 只接受通过 attempt 的 promoted bytes，并绑定当前 source snapshot、certificate、material_id、recomputed/comparison digest。PageProjection、RenderLedger、Audit、quality 和 CLI 只消费这些 refs。原始 prompt、Authorization 和 scan 失败响应永不持久化。

发送前按 runtime authority map 校验 `external_processing_policy`=`config/task5-external-processing-policy-v1.json`（SHA=`145339af1da2170e386ccbb41a82e8041e1e08743ae610d5b20aa48f3c47b01a`）及其 `source_sensitive_content_scan` 引用的扫描规则（actual SHA=`1253ab1e1e31ae7d737183d8ac8ffb85d9e5f83a2bc76b534195bbc4339d53d5`、canonical SHA=`5836aa4631c29d5d6117eed42c47f886e1edfe36df3c03ee97bbfcc2743dff2e`），并校验 provider config SHA、policy mode、exact endpoint 和 payload scope；17 项 map authority 任一改变都必须重算 runtime/material identity 并重跑 design review，禁止保留“待重算”状态。Task5 唯一 provider transport seam（`task5_provider.py`/`task5_provider_config.py`）必须在构造/调用 LLM 或 embedding client 前执行 approved host allowlist（只准 `dashscope.in.whatspos.cn`、`llm.paxszapp.com`），并在同一 seam 记录 retry=0 和每次 HTTP attempt；未知 endpoint 固定 calls=0、blocked。M401 测试进程必须用 `/usr/bin/sandbox-exec` 的 `(version 1)(deny network*)` profile，并主动探测 `socket.create_connection`、`socket.getaddrinfo`、`urllib.request.urlopen`，把 profile/命令 hash、exit 和实际 calls 写入 validation receipt；sandbox 不可用也只能 calls=0。每个 selected Block、每个 embedding route descriptor/query，以及唯一的 `Task5ProviderTransport.call_once` 在组装最终 LLM JSON wire payload 后、socket 前，都必须递归枚举所有 text-bearing JSON pointer（至少 `messages[*].content`、title/question/page_type、provider-visible URI、claim/route metadata、semantic frame），对原始与 NFKC 视图逐字段扫描；每个字段回执绑定 JSON pointer、source/block/claim refs、scanner actual/canonical SHA、match digest 和 payload digest。只扫描原始 Block、只扫描 prompt 模板或字段缺失都不算通过；字段未扫描、扫描结果与最终 payload 漂移或 scanner 缺失时必须 `SOURCE_POLICY_UNVERIFIED`、calls=`0`，不得建立 socket。scanner 命中写 `SOURCE_SENSITIVE_CONTENT`、calls=0 并阻断，不静默脱敏；receipt 只留 source/block/locator/hash/category/match digest。本 revision 不作 retention/no-log 声明；若要求该证明而缺 path/schema/SHA，固定 `SOURCE_POLICY_UNVERIFIED`、calls=0、exit=2。结果只写脱敏 Audit。

**Transport receipt authority**：所有真实 Qwen/Jina 网络流量只能经过 R2-owned `Task5ProviderTransport.call_once`；client、batcher、replay loader 和测试不得自行填写 `provider_mode`、`http_attempt_count`、response hash 或 `observed_calls`。该 seam 在 DNS/TLS/socket 前验证 approved host/TLS policy，并在每个实际网络尝试开始前登记不可变 attempt identity；无论收到 HTTP 响应、DNS/TLS/连接失败还是 read timeout，都以 create-only 方式写 `task5-provider-transport-attempt.v1` 行到 `_audit/semantic-response-ledger.jsonl`。无响应行必须含 `transport_phase/error_class/socket_attempted/http_attempt_count=0/retry_attempts=0/observed_calls/response_normalized_sha256=null/error_digest`；HTTP 行才含 response normalized digest/status。所有行固定含 `writer_id=Task5ProviderTransport.v1`、单调 `transport_event_id`、run/request identity、endpoint/model、TLS peer validation digest、request payload digest/byte count 和 observed monotonic timestamps；不写 prompt、response、key、Authorization 或 raw source。每个 semantic response/route/failure receipt 和 replay entry 必须引用该行的 ref+SHA；缺 seam receipt、writer_id 不符、event 序列不连续、attempt count 由 caller 自报或 ref/hash 不匹配均 blocked、calls=0，不能记 provider_calls=0。fake handshake 只能写 `provider_mode=fake` 的测试证据，永远不能满足 real replay。

安全错误矩阵固定：`SOURCE_SENSITIVE_CONTENT` 是 source/projection-local，当前 mode 该项 `blocked`、`observed_calls=0`、写 failure sink，继续同 mode 的其他来源；full 终态为 `not_released`、`full_status=failed`、exit `1`，该 coverage 只能 Audit/blocked，绝不发布或脱敏。`SOURCE_POLICY_UNVERIFIED` 是 global preflight fatal，停止 slice/full、`outcome=blocked`、`exit=2`、calls=0；两者都不能被 retry 或 replay 掩盖。

**多来源原子失败规则**：`quality-reader` 的 selected-source projection 是一个不可拆分的请求。只要任一选中来源命中 `SOURCE_SENSITIVE_CONTENT`，或任一选中字段出现漏扫、扫描 contract 漂移、payload 漂移或 closure 不完整，整个 projection 必须在 socket 前失败，写 `SOURCE_SENSITIVE_CONTENT` 或 `SOURCE_POLICY_UNVERIFIED` 的 failure sink，且 calls=`0`；不得删除命中的来源、改写 selected closure、重算 request identity 后重试、发送剩余来源的部分 payload，或把失败来源伪装成未选中。只有不相关的 route/projection 可以继续；同一 projection 的 Reader、quality、publication 均不得生成。

`source_not_documented` 不是普通 diagnosis Reader 的缩减版，而是独立的 `diagnosis` page-type / `source-not-documented-status` projection contract：`config/task5-source-not-documented-contract-v2` 定义固定五个 status slots 和 `reader_task_path.snd-status-v1`，不要求普通 diagnosis 的 `symptom→check_order→cause/evidence→action→escalation` 五阶段。SND 五段只能是：`source_scope`（扫描对象/范围）、`scan_coverage`（规则和逐 Block 覆盖）、`zero_match_result`（明确/含糊匹配均为零）、`interpretation_boundary`（只说明资料没有记录，不推断系统状态）、`verification_next_step`（如需诊断系统行为，必须补充独立观测/来源）；普通 diagnosis 的 cause/action/escalation 在 SND projection 中标记 `not_applicable` 并说明证据边界，不得编造处理方案。SND-RULE-001 全量扫描且 explicit/ambiguous 均为空时，只进入 guard；还必须有逐 Block 的 `semantic_zero_match_certificate.v1` 才能替换同一 entry 的 source-digest projection，不增请求、Reader、coverage row。缺证书时保留 Audit-only/not_released。证书通过也只能生成明确标注扫描范围和局限性的资料状态页，不产生“系统没有异常”的语义结论。其 identity 固定为 `guard.source-not-documented.<source_id>`、`quality_case=null`、`applicable_dimensions=[]`、`coverage_class=guard_case`，不是 8 个 QualityCase projection；Q-DIA-01 是独立 quality projection，可复用 source，但必须有自己的 closure/route/五维结果。只保留一个 Reader/Audit/coverage 闭包。Reader/Audit 绑模板、扫描和证书证据；有证书时 projection 为 `not_evaluable`、不进 KD_WIN，guard+硬门通过才可 package `released`。

**Tests**：fake provider success、malformed JSON、wrong claim、missing slot、cross-source fact、protected token loss、timeout、provider error、页面总长度/句数超限、`whole_source_semantic_rewrite`、`one_to_one_claim_rewrite` 和短来源低分母边界；明确断言这些失败不生成 Reader，且不存在 `full-source` Reader。

**STOP**：实现只能把原文换个标题、无法将正文单元绑定 Claim 或需要凭空补事实时，停止。

### Phase R3 — actual quality evaluator and route ledger

**Goal**：让 quality case/baseline 变成 evidence-only 输入，并让 embedding 真实参与六个 QualityCase 的 8 个 projection 问题/场景 route；related-topic route 明确延期，不在本 revision；五维 verdict 只能从实际输出重算。

**Design**：拒绝带 `answer_lede`/`slot_ledes`/静态 verdict 的 v2 config；冻结 CompanyBrain snapshot manifest。89 条逐源入口另由 `config/task5-source-page-manifest-v2.json` 冻结，每个 canonical path 恰好一个 source case/question/page type/one-source route/oracle，运行前校验 89、path digest、source_id、无重复/额外项。Quality evaluator 读取实际 Reader/Audit file hash、route record、render ledger 和 CompanyBrain file hash，先检查 typed semantic unit、surface、scope、negation/conflict，再计算五维 verdict，并分开写 `quality_cases_proven`、`source_closure`、`publication_status`；keyword 只是最后观察信号，不能单独创造 `KD_WIN`。R3 评分前还必须生成 `8 projection × 5 dimension` feasibility matrix；每格没有真实可回放 CB gap 就输出 `UNKNOWN`，不伪造 basis，并将 matrix 绑定 snapshot/tree digest 和结果 receipt。

**Tests**：静态 baseline/answer template 被拒绝；实际 Reader 改动会改变 verdict；缺 Audit/错 hash/route only probe/全 source fallback/slice-only page existence/guard failure 都阻断；冻结 handshake fixture 的 fake full/slice embedding、extra selected path 和 selected vector 未消费负例必须有 canonical receipt；摘要不能改 verdict；feasibility matrix 覆盖 8×5，缺 gap、重复 gap、跨维复用和 snapshot 漂移都变为 `UNKNOWN`/not_released。

**STOP**：evaluator 仍信 `strict_advantage`、只统计页数、不能读取实际文件或没有 R3 fake embedding handshake 时，停止，不进入真实运行。

### Phase R4 — runtime wiring and Downloads artifact

**Goal**：把 R1–R3 接入 `slice → full`，全量处理 89 条，切片失败仍跑 full，最终目录可从 Downloads 找到。

**Design**：provider mode 逐源建立 semantic compile ledger；route ledger 在 slice/full 都生成；非空失败源 Audit-only；质量和 source closure 结果独立；发布只在所有硬门满足时原子写入新候选。默认 output 不再是隐式 `/tmp`，发布 staging 必须位于 Downloads 同级同文件系统，跨设备或外部 staging 直接 blocked。请求错误矩阵固定为：preflight/identity/budget/lock/publish→global `blocked|overrun`、exit `2`；transport/auth/timeout/429/5xx/partial embedding→global `unavailable`、exit `2`，不继续 full；2xx 坏 JSON/schema/lineage/relation/raw-copy→当前 `evaluation_mode` 的 mode-local failure：slice 标记 `slice_failed` 后继续 full，full 标记对应 `full_failed` 并继续剩余 full 请求，二者最终均 `not_released`、exit `1`；known_empty/not_evaluable 为 diagnostic；user cancel→`cancelled`、exit `4`。每类都写 reason/class/mode/request identity/observed_calls/continue decision 并测试，不重试、不跨模式复用 receipt。

**Tests**：slice mode-local bad JSON/schema/lineage 继续 full；full mode-local failure 写 full_failed 并继续剩余 full；slice/full transport timeout/auth/429/5xx/partial embedding 停止 full；89 inventory closure、empty source、duplicate/conflict、cancel/race、failure evidence sink、old output untouched、Downloads manifest、real status/exit and no secret scan。

**STOP**：任何 provider-required path 仍回退 raw Reader、输出不含 provider/route evidence、或全量不是 89 条时，停止。

### Repair gate receipt contract

两层文件语义固定：attempt 是完整 `task5-repair-gate-attempt.v1`（`status=passed|failed`），固定 R1–R4 是 `task5-repair-gate-promotion.v1` index；attempt/test/inverse 都绑定 before/after snapshot、path SHA、patch_id、rollback preflight、material 和 canonical bytes，inverse 方向为 `after → before`。锁、expected-parent-hash、临时文件、fsync、atomic rename 和 R3 全局 sequence 是硬约束，失败事件保留。

R1/M102、R2/M202、R3/M252+M253、R4/M302 分别生成 gate receipt；R3 event 绑定 attempt、input snapshot/material/hash、case/projection、前序 digest，M253 追加前复核 quality/baseline/source inputs。固定 tests/inverse view 只来自 passed attempt；下一 gate 发现缺字段、漂移、未列路径、inverse 缺失或上一 gate failed 即 STOP。

失败 attempt 只写不可变 attempts 目录；index 可追加 history 但不能 promotion。M401 只引用 canonical attempt ref/hash。

canonical bytes 统一为 UTF-8、sort_keys、无空格 JSON + LF；receipt 记录 command、exit/status、counts、stdout/stderr/result hash、snapshot/material。M401 focused/full 各有独立 `task5-m401-test-receipt.v1` attempt receipt；inverse patch 只触及 changed_paths，并由后续 gate/M401 在临时副本真实 apply 复核。

M401 顺序固定为：同一 attempt 先 `write-evidence --phase preflight`，再 focused receipt、通过后 full-regression receipt，执行只针对唯一 `candidate_bundle_ref` 的 `surface-qa`，最后 `write-evidence --phase finalize` 只校验已有证据、R1–R4 promotion、candidate bundle ref、R4 attempt ref、directory-manifest SHA、candidate tree digest、当前 `mini_task.design` terminal-clean identity（`review_kind/result/report/attempt/design_review_contract_id/design_review_contract_hash/semantic_hash/snapshot_tree/material_id`）和 Task5 runtime identity（`runtime_contract_id/runtime_contract_hash/semantic_contract_id/semantic_contract_hash`）后原子生成 packet/views；finalize 不得补造证据，缺失/失败 STOP 且不发 provider 请求。surface-qa 发现多个候选、bundle/manifest/tree 漂移或未清理 staging 时，M401 只能失败，不能选择一个继续。

证据序列化细则固定为 Python 等价的 `json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'`：nested object 递归按 Unicode code-point 升序，数组保持原顺序，不做 ASCII escape，文件只写一行 canonical JSON 加 LF。`task5-test-receipt.v1` 的文件 SHA 按该整行计算；`task5-m401-evidence-packet.v1` 顶层必须有 `canonical_sha256`，其值是删除该字段后按同一算法计算的 SHA-256，M401-R 先复算 packet 再消费它。R3 event 的 `event_sha256` 也不包含自身：对删除 `event_sha256` 字段后的 event object 按同一算法计算，`previous_event_sha256` 参与 hash，第一事件固定为空字符串；最终写入的 event 行再按完整 object canonical 化。R3 event 必须逐条记录 8 个 projection keys：`Q-POS-01.positioning`、`Q-CON-01.concept`、`Q-OPR-01.qr.operation`、`Q-OPR-01.zero-touch.operation`、`Q-DIA-01.diagnosis`、`Q-EXP-01.experience`、`Q-BND-01.operation`、`Q-BND-01.diagnosis`，最终 quality oracle 也必须对这 8 个 projection 分别绑定 route、Reader、Audit、RenderLedger 和五维 observation。

R3 event schema补充：旧段列出的 event fields 是缩写；正式 `task5-repair-gate-event.v1` 必填 `attempt_id`、`attempt_event_index`、全局 `sequence`、event type、input snapshot/material、input hashes、case/projection set、previous/event digest。`attempt_event_index=1` 是该 attempt 的首个 preflight，不是全局 sequence；R3 preflight/final/failed 都属于同一不可变 attempt history。

### Phase R5 — verification and real run gate

R3 重跑只向同一 `R3-events.jsonl` 追加：每个 event 带 `attempt_id`，`sequence` 在全文件严格递增；失败 attempt 追加新的 preflight/failed event，不复用 sequence、不删除旧行、不重算旧 digest。M401 必须校验完整 event history，并确认 promotion view 指向的通过 attempt 是最后采用的完整链路。

1. 设计 review：冻结四份材料，保留 provider/unavailable 事实和 dispositions。
2. RED/GREEN：按 R1→R4 分阶段实施，先聚焦测试。
3. 回归：Task5 acceptance + 正式 digest 全量测试；测试绿只证明实现行为。
4. `mini_task.implementation`：审查当前 diff、tests receipt、AC trace、AC-RP-007 的 pre-M402 readiness、coverage limits 和剩余风险；先把审查结果写入不可变 `quality/evidence/task5/m401-r-receipts/attempts/<review_attempt_id>.json`，只有 `available + terminal_clean=true` 且所有 finding 已处置的 attempt 才能原子 promotion 到 `quality/evidence/task5/M401-R-review-receipt.json`（schema=`task5-m401-r-review-receipt.v1`，canonical SHA-256=`74584b624c2c672e6aa4f6d76ca98165f2a06e2fb5c40fca36b39f1807990d1a`；actual 文件 SHA 不作为 frozen schema identity）。真实用户结果保持 pending，不把未执行的 M402 当作实现证据。任何 actionable finding 先修复。
5. 真实运行：只读 raw/CompanyBrain，输出 `/Users/Hugh/Downloads/KnowledgeDigest-task5-reader-quality-provider-real-20260824`；固定入口同时接收 `M401-evidence-packet.json`、独立的 `M401-R-review-receipt.json` 和 authenticated `workflowhub-implementation-handoff.json`，先校验三者的 canonical SHA、`handoff_sha256`、`m401_packet_sha256`、snapshot/material/worktree、design/implementation/runtime/semantic identity 和 writer attestation，再允许读取 raw/CompanyBrain 或发 provider。运行参数必须同时注入当前 design review 的 `review_kind=mini_task.design`、terminal-clean result/report/attempt ref+SHA、`design_review_contract_id`、`design_review_contract_hash`、`semantic_hash`、`runtime_contract_id`、`runtime_contract_hash`、`semantic_contract_id`、`semantic_contract_hash`、`snapshot_tree`、`material_id`，并与 M401 packet、M401-R receipt、implementation successor、M402 invocation 四方逐项相等；记录实际 provider calls、embedding route、89 closure、slice/full、五维 verdict 和最终 status/exit。S3 形成真实 candidate 后，必须在最终 run-result 写入前执行一次独立的 R1-owned surface QA；它绑定本次实际 candidate bundle、R4 promoted attempt/ref+SHA、pre-publish directory manifest/tree digest，并逐项验证渲染后的 Home/Reader/Audit、相对链接、媒体/链接目标、禁字段和 staging cleanup。QA receipt 写入 `quality/evidence/task5/m402-surface-qa/attempts/<attempt_id>/surface-qa.json`，`bundle/_audit/run-result.json.artifact_manifest.surface_qa` 同时绑定该 receipt 和最终 published manifest/tree digest；M401 fake candidate QA 不能替代这次 actual QA。凭据缺失时真实结果必须是 blocked/unavailable，不得改配置或伪造通过。

### R5 oracle

SND 读前顺序固定为两段：S2 先校验 `task5-source-not-documented-contract-v2` 静态 schema/actual/canonical identity；通过 M401-R 和 output preflight 后建立本次 raw snapshot、Block ledger、producer certificate，由独立 verifier 在任何 SND Reader/Qwen/embedding 前生成并 promotion current receipt。只有本轮 receipt 才能被 SND Reader、M401 finalize、release predicate、manifest、run-result 消费；失败仅保留 attempt 并 `not_released/blocked`，不接受历史 receipt 或静态 contract 冒充当前扫描结果。

`candidate` 是中间状态，不是成功态；若运行结束仍为 candidate，结果可以保留候选诊断，但必须对外归一为 `not_released` 并返回退出码 `1`。测试必须验证“有文件但 candidate”不能返回 `0`。

`blocked` 和 `unavailable` 都返回冻结码 `2`；两者不靠 shell code 区分，必须靠 `_audit/run-result.json`（schema=`task5-run-result.v1`）和 Audit 中的 `publication_status`、`outcome`、`reason_code`。该 JSON 是运行级唯一消费者入口；读取不到、损坏、schema/WorkflowHub identity 不完整、结果与退出码不一致或 `unavailable` 返回 `0` 都按 `failed=3` 处理。M401-R 缺失/过期/漂移只在 S1 已拿到 lock、创建 staging 后进入 S2；失败 Audit 随 staging rename 到 failure sink；若 S0/S1 自身失败，则不创建 sink，保留 preflight/lock evidence 和真实 `failure_evidence_path=null`。

真实完成不是“命令退出 0”。最低可回查证据：`_audit/run-result.json`（schema=`task5-run-result.v1`）、provider call ledger、embedding route ledger、source manifest=89、实际 Reader/Audit file hashes、六 case×五维 verdict、quality/source/publication 三状态、输出目录 manifest 和原始退出码。CLI 退出码固定为 `released=0`、`not_released=1`、`blocked=2`、`unavailable=2`、`failed=3`、`cancelled=4`；任何缺失、未知、TIE、CB_MISSING、未声明/不匹配空源或 lineage 失败都保持 `not_released`。与冻结 manifest 精确匹配且 Audit 闭合的 `known_empty` 不生成 Reader，但不单独阻断发布；provider unavailable 不能返回 0。

### Git delivery boundary

本任务不自动 commit、push、merge、archive 或 cleanup；M401-R 只绑定最终 snapshot/tree、允许文件边界和当前 diff。Git 交付需单独授权，不能把“没有 commit”伪装成代码通过。

## Repair revision v2.2 — comparable five-dimension score contract

每个 `case × dimension` 用同一 rubric 从实际 Reader/Audit 与 CompanyBrain 可见表面计算 `content_score`、`structure_score`、`score`（0–100），五维逐项必须 `KD_WIN`，不允许平均分抵消。维度分别检查：问题/场景 route、产品/模块/对象/场景/边界 taxonomy、业务答案槽位与证据、五类 page type、Reader 可读与 Audit 可回查。

CompanyBrain gap 固定为 `route={unreachable,wrong_relation}`、`taxonomy={missing_taxonomy_axis,wrong_relation}`、`business-answer={missing_stage,unsupported_answer_claim,wrong_relation}`、`page-type={untyped_contract,wrong_page_type}`、`Reader-Audit={missing_provenance,untraceable_claim}`；每个 `advantage_basis` 必须带对应实际文件 hash/定位、gap、KD surface 和 evidence ref，否则 `UNKNOWN`。不奖励内部 JSON、文件数量或静态 verdict。

QualityCase 只提供 atoms/markers/forbidden；baseline 只提供真实 Reader-Audit observation。embedding closure 按 `evaluation_mode` 分流：`full` 使用 `full_required_source_paths` 作为 authenticated Qwen closure；`slice` 只能消费冻结 slice fixture 的 `slice_required_source_paths`，并记录 `missing_full_source_paths = full_required_source_paths - slice_required_source_paths`。Jina 的 top-k 只负责稳定排序；显式 required closure 在 route 后按排名顺序完整并入 `selected_source_paths`，不因 closure 大于 top-k 而截断。slice 缺失项只能是 `source_not_in_slice/not_evaluable`，不得进入 full Reader、full quality verdict 或 `KD_WIN`；不属于冻结 closure 的 top-k 候选记为 route-only，不进 Qwen、Reader、Audit 或评分。每个 embedding route descriptor 的 title/question/page_type 必须先通过 `reader-path-relation` authority 的字段级 semantic support verifier，支持闭包来自当前 raw Block/Claim 或 authenticated CompanyBrain route observation；路径/hash 闭合但字段支撑不成立时 route=`unknown`，不发 embedding。Qwen typed output 的 page type、五轴、summary、slot 都必须有字段级 Claim refs。结果使用 `task5-quality-result.v3` 与 `task5-companybrain-observation-v2` authority，预算按 full/slice 独立 embedding probe/batch 重算。

**source-digest route verifier**：manifest 的 `question`、`expected_title`、`page_type`、主意图及产品/模块/对象/场景/边界关系只是 route 候选，不是事实证明。D0/R2 先按 `source-scope-producer.v1` 从当前 source bytes 生成 89 条 source identity/Block/Claim 闭包，provider calls=`0`；它只确认来源能否安全进入一次单源 Qwen 请求，不因为缺少显式 route metadata 而丢请求。Qwen typed output 返回 route/page fields 后，再由 `source-digest-route-verifier.v1` 逐字段绑定 Claim/frame/locator、source/block/claim hash、单源 closure 和 `support_sha256`。原始目录顶层只可作为结构性 product route，文件名只可作为显示标题候选，不能证明 object/scene/boundary 或答案事实。字段无支持、主意图多解、关系不闭合、stale locator 或 output/ledger 漂移时，当前来源 route=`unknown`、只写 Audit、Reader/quality/publication 不生成；但不能把 D0 没有显式 metadata 当成 Qwen calls=`0`。87 个普通来源必须逐条尝试，post-provider route closure 少于 87/87 时最终只能 `not_released`。authority=`config/task5-source-digest-contract-v2.json` actual=`4ae5de71be1cbdbf5987af2b54814ce716412f1e3e219146d7f8f1f7638ec5b2`、canonical=`94af4a1f1d48921b0d2b1de2c59f87b7c4073d38022aa02dc75db7d99256bfa8`。

**唯一实际质量结果载体与生命周期**：R3 evaluator 是唯一 writer。每次 actual run 先写不可变 candidate attempt `quality/evidence/task5/actual-run/attempts/<attempt_id>/quality-result.json`，状态固定为 `candidate/not_released`，必须有 `candidate_tree_sha256`，且 `published_tree_sha256=null`；它不能产生 released verdict。候选 bundle 完成 pre-publish surface QA 后，只有同一 R3 owner 执行 Downloads 同盘的原子 rename，才进入发布后 finalize。rename 成功后，R3 新建不可变 `quality-result-finalize` attempt，重新读取最终目录 manifest/tree，计算 `published_tree_sha256`，确认它与 rename 前 candidate/tree/manifest 的绑定关系一致，再原子 promotion 到固定 `quality/evidence/task5/actual-run/quality-result.json`，写入最终 `publication_status` 和 `published_tree_sha256`。rename 失败、rollback、finalize 失败、最终 tree/manifest 漂移或 candidate/published 不一致时，只保留 candidate/失败 attempt，固定 promotion 不更新、`published_tree_sha256` 保持 null、状态为 `not_released`；不得把 candidate artifact、run-result 或 surface QA 当作 released。

artifact 的 `results` 必须恰好保存六个 case、八个 projection、五个 dimension 的逐行 result（每行复用 `task5-quality-result.v3` 的 projection/dimension/atom/gap/advantage/evidence 字段）、Reader/Audit/route/RenderLedger/source-closure/path-replay/CompanyBrain refs+SHA、actual candidate bundle ref、candidate directory-manifest ref+SHA、candidate/published tree SHA、`strict_all_kd_win` 派生结果和 publication status；不保存 key/raw prompt。任何行缺失、重复、projection/dimension 不全、ref/hash/tree 不闭合即 `UNKNOWN/not_released`。`bundle/_audit/run-result.json`、M402 release predicate、post-rename surface QA 和最终 Downloads manifest 只能引用同一 promoted artifact 的 ref+SHA，禁止各自生成质量 verdict。
`gap_atom_mapping` 是可执行 authority：每个 `projection_key × dimension × gap_type` 必须由同一映射生成 `mapping_digest`、`atom_ids`、`cb_status=absent`、`evidence_field` 和 locator；atom ID 只能来自该 projection/dimension 的冻结 required atoms。结果的 `gap_atom_refs` 必须与 CompanyBrain observation 的 `atom_ids` 逐项相等，`strict_improvement_refs` 只能引用真实 `CB absent → KD present` 的 atom；缺失、错维度、错 gap 或 digest 漂移一律 `UNKNOWN`，不能由总分或 case-level gap 补成 `KD_WIN`。

### Design review follow-up：接口与测试隔离

LLM 固定走 `llm.call_llm`→`task5_provider._default_llm_call`，embedding 固定走 `OpenAIEmbeddingClient.embed/probe_fingerprint`；route ledger 保存实际 vector/top-k/selected closure/selection_kind，并把 authenticated closure 作为 Qwen 输入。calibration 由 `load_calibration_artifact` 复核 endpoint/model/dimension/hash；pytest 只注入 fake，M402 才联网，v1 fixture 在网络前拒绝。LLM model 必须是批准集合 `qwen3.6|qwen3.8` 中且通过 live capability check；receipt 使用实际 model。

### Design review corrections now frozen

- v2 case/baseline 使用 `config/task5-reader-quality-provider-v2.json` 中绑定的两个 SHA-256；六 case、每维 atoms/markers、source refs、baseline locators 和 projection keys 由冻结 fixture 提供，代码不能补写判定项。当前 quality fixture 实际 SHA-256=`41e36e889f5cb36eb28ddc691d488580d5e1cae02b22f67bead294e64c45798b`，规范化完整 JSON SHA-256=`281ced2464a2d7dfd035aecf084cc21ef87ed8f8c6485993a6287375e8af1654`；五维语义合同也由同一实际 JSON 的 `semantic_contracts` 提供；旧 §10.3 和 v1 fixture 只读历史，不得被 provider-required evaluator 消费。
- 每个 projection 独立走 typed compile、Reader/Audit/render lineage 和五维硬门；case×dimension 取 projection 最低分，缺 required atom 时先 blocked/UNKNOWN，不能由结构分补回来。
- `GENERATED_BY/generated_by` 只允许在 Audit rubric、Audit ledger 和内部元数据中出现，不是 Reader.body required atom；每个 projection 的 boundary refs 必须有独立 projection id、source closure 和 scope，Q-OPR 的 QR/Zero Touch 不得共享 case-level boundary evidence。

### Mini-task 设计范围风险

`accepted_risk=true`：用户要求同一 mini-task 覆盖 provider、LLM、embedding、五维评价、切片、89 条全量和 Downloads 真实运行，不能拆后续任务。补偿是四个独立 repair gate、每 gate 的 snapshot/owner/RED-GREEN/attempt-promotion/inverse、`mini_task.design`、focused/full、M401、`mini_task.implementation`；任一缺失即 STOP，失败证据保留，不得进入 M402。改变契约、输入或文件边界必须新建 design snapshot/material 并重审；该风险不等于通过。

### 回滚

只丢弃 candidate；失败/取消按 spec 将 staging 原子 rename 到 Downloads failure sink，保留 Audit/run。输入或合同 identity 变化就新 run。baseline v2 是 ADD/MODIFY 的 immutable before-SHA authority；gate receipt 才是 after-SHA/patch/inverse authority，回滚前逐项复 hash，外部改动、缺 inverse 或 hash 不符就 STOP。raw、CompanyBrain、旧产物、Downloads、审查证据和 failure sink 永不触碰。

Failure sink 使用 `task5-directory-manifest.v1`：fsync 后按 Unicode path 记录 `relative_path/byte_count/sha256`，拒绝 symlink/socket/临时文件，rename 前后 bytes 必须一致。用户 Audit 只保留 Claim/source hash/relative locator；`task5-failure-evidence.v1` 只允许状态、reason、run/material/request/provider identity、calls/exit、ledger/Audit ref+hash、source/block/content hash、relative locator 和 cleanup，不允许 raw prompt/response/source bytes、凭据、host path 或自由文本。全 staging/manifest 扫描命中敏感或未声明字段即不 rename；Audit 未落盘时 `audit_ref=null`。测试覆盖排序、崩溃、rename/临时文件/敏感字段负例。

### Source manifest implementation boundary

**Duplicate alias execution**：同 hash alias 保留自己的 89-row CoverageLedger、Claim/Audit link 和 `duplicate_alias` 状态，但不重复发 source-digest/生成 Reader，Audit 回指 canonical Reader；预算按 canonical present source 计数。闭合 alias 可通过 canonical Reader link 满足包级 released，但 alias 自身 coverage、canonical_source_id/hash 或 Audit/link 任一缺失/不匹配必须阻断 released。当前无 alias：87 个普通 source-digest + 1 个 SND replacement；只有 SND 证书闭合时才是 88 个 present Reader 闭包，否则包级 not_released。

`config/task5-source-page-manifest-v2.json` 是实现必须消费的冻结输入。M302 preflight 校验 schema、89 entries、唯一 `SRC-*` source-digest case、page/question/required paths、lineage/oracle 和 `source_snapshot` 的 status/hash/byte/line/locator；缺项、重复、额外来源、path/raw drift 在首个 provider 请求前 blocked。manifest hash/snapshot_id 写入 run、staging、source receipt、projection 和 quality evidence。

每个非空 source entry 产生一个 `route_kind=source-digest` request，manifest 固定 question/page/source path/closure，成功才有一个 Reader PageProjection+Audit/coverage/RenderLedger；ambiguous、证据/关系/provider failure 只进 Audit。`source-direct-audit` 固定 `reader_eligible=false`。QualityCase 另走真实 `route_kind=quality-reader` embedding：full 使用 `full_required_source_paths`，slice 使用冻结 fixture 的 `slice_required_source_paths`；两种 mode 都要求 selected paths 精确等于该 mode 的 `top_k ∩ required_source_paths`，且完整覆盖该 mode closure。slice 额外写 `missing_full_source_paths`，缺失项标记 `source_not_in_slice/not_evaluable`，其 slice surface 只能用于诊断，禁止进入 full Reader、full quality verdict 或 `KD_WIN`；route-only 不进 Qwen/KnowledgeUnit/Reader/Audit/评分。三类 route 证据不可互换，M301/M302 覆盖 manifest/path/page/route/closure 越界和泄漏负例。

### Embedding source descriptor boundary

QualityCase 的 embedding 候选不是隐含的文件名列表，而是冻结算法生成的 `source-descriptor.v1`。每个非空 manifest entry 的 descriptor canonical object 固定为 `{descriptor_id=source_id, provider_visible_source_uri, source_snapshot_id, raw_content_hash, byte_count, line_count, title, question, page_type, canonical_text_sha256}`；`provider_visible_source_uri` 和 `source_id/block_id/claim_id` 必须完全按 spec §10.3.1a 计算，任何 host path、`raw://` 别名或输入顺序均不得进入 provider-visible identity。`canonical_text` 由 manifest 指向的 raw bytes 严格 UTF-8 解码，先把 CRLF/CR 归一为 LF，再做 Unicode NFKC，不 trim、不截断、不丢表格/代码/图片/链接/命令标记，但只在本地用于 hash/lineage。Jina 实际接收的 `route_descriptor_text` 固定为 `title + LF + question + LF + page_type`，不含 canonical_text 或 source block；发送前用 scanner authority 对 `title`、`question`、`page_type`、`provider_visible_source_uri`、`query_text` 的 raw/NFKC 视图逐字段扫描，scanner 缺失、漂移或任一命中均 calls=0、`SOURCE_POLICY_UNVERIFIED|SOURCE_SENSITIVE_CONTENT`，不发送部分 descriptor。descriptor object 使用 UTF-8、递归 Unicode code-point key sort、无空格 JSON + LF 求 `descriptor_sha256`，并把 `canonical_text_sha256`、`descriptor_sha256` 和 provider identity 写入 route ledger；输入 bytes/hash/字节数/行数任一不等于 frozen source_snapshot 就在网络前 blocked。

full candidate set 是 88 个 present descriptor，slice 是 frozen slice 去重排序后排除 expected empty 的 13 个 descriptor。route ledger 记录 candidate kind/ids+hash、descriptor/vector hash、query、完整 top-k/rank/score/tie-break、selected 与 route-only paths；相同输入置换必须稳定，tie-break 为 canonical path→source_id。`full` 必须满足 `selected_source_paths == top_k ∩ full_required_source_paths == full_required_source_paths`；`slice` 必须满足 `selected_source_paths == top_k ∩ slice_required_source_paths == slice_required_source_paths`，并把 full closure 中不在 slice 的路径逐项记为 `source_not_in_slice`。extra/截断/临时 descriptor/source-direct 混入/route-only 进入 Qwen 或 selected vector 未绑定 prompt/PageProjection 均 blocked；slice partial surface 不得进入 full Reader/quality/KD_WIN。测试覆盖 descriptor、候选集、顺序、并列、绑定、mode-specific closure 和越界 drift。

**Top-k 冻结**：`config/task5-provider-config-v2.json.routing.top_k=8`，是所有 QualityCase projection 的统一候选排序上限，不是 required closure 的大小上限。候选集为空、NaN/无效分数、并列未按 `(score desc, canonical_relative_path asc, source_id asc)` 排序、descriptor/closure 漂移、selected closure 与 required closure 不相等，均在 provider 前 `blocked`；只因 top-k 未命中某个冻结 required path 不阻断，route 后必须把完整 required closure 按排名并入 Qwen。只有不属于 required closure 的 top-k 路径才是 route-only。request identity、budget、handshake、prompt、route ledger 和 tests 都写 `top_k=8` 与 `selection_kind=frozen_closure_union_ranked`。

### Raw-coordinate and semantic evidence boundary

规范化文本不能直接冒充原文坐标。实现必须生成 `raw-coordinate-map.v1`：每个 Block 同时保存 raw UTF-8 byte/line span、canonical code-point span，以及 CRLF/CR→LF、Unicode NFKC 的 canonical→raw segment map；`support_span` 同时写 canonical span 和 raw locator，按 raw bytes/hash 重放。一个 canonical span 若映射到非连续 raw 区间、组合字符边界不确定或无法唯一得到 raw line/byte range，则 Claim 只能 Audit-only/blocked，不能进入 Reader 或 `KD_WIN`。R2/R3/M253-R 必须覆盖 CRLF、CR、NFKC 扩展/合并、组合字符和映射不确定负例；Reader/Audit 只能把 raw locator 作为最终来源定位。

### Semantic-unit, ReaderTaskPath and score implementation boundary

M202 将 Claim 作为 evidence pointer；只有 Qwen v2 typed page、Claim/block/hash/locator、极性/冲突、非原文包装和保守闭合都通过，semantic unit 才进入 Reader。`quality-reader` 必须渲染完整 typed `ReaderTaskPath`；公开的 `source-digest`/`source-not-documented` Reader 也必须通过同一 page-type stage contract、入口回放、Reader/Audit 配对、source closure、lineage 和 page rewrite gate，但不进入 8 个 QualityCase 的五维严格胜出矩阵；`source-direct-audit` 永不进入 Reader。任何公开 Reader gate 缺失或失败都只能 Audit-only/not_released，不能 raw fallback。M252 只消费真实 Reader surface 和绑定 unit；字符串命中、无关/跨源 Claim、否定句不计 support。KD/CompanyBrain 共用冻结 atom/page contract，错误顺序和“正文有词但无语义支持”必须失败。

`KnowledgeUnit` 谓词代码化：statement 8–800 字符、唯一 claim_ids、每个 Claim 有非空精确 support span、scope/status/polarity/conflict/raw-copy 齐全；先生成 `task5-semantic-frame.v1`，frame 的每个 concrete subject/predicate/object/action/order/quantity/conditions/polarity/scope 都必须有 raw-coordinate support span；unknown/not_applicable 使用冻结的空 span 结构，不能满足 Reader 必答字段；`claim-lineage-v1` 只有 claim_full 诊断 span。Normalizer 复核 span、owner/block/hash/locator、非泛词、非 raw-copy 及 statement frame 与 source frame 的主体/客体/动作/顺序/数量/条件/否定/protected token 双向闭合；bounded lexical coverage 只记诊断，不是 acceptance。未知/冲突/不一致只进 Audit，R2 保存正负例和业务化改写正例。
关系安全遵守 spec §11.1.3 `relation-parser-v1`：Unicode code-point offset、protected token、块边界、条件/否定优先级、唯一候选和 unknown 分流固定；cue 冲突、同距主体客体、表格跨列或条件边界不唯一均 unknown，不交给模型兜底。receipt 保存 parser/candidate/tuple/scope/ambiguity/source locator；M253-R 先 RED 再 GREEN。

`ReaderTaskPath` 的 contract 固定为：positioning=`identify→audience/scope→distinction→boundary/choice`；concept=`definition→object/relation→condition→misuse boundary`；operation=`precondition/permission→ordered steps→result/verification→failure/recovery/limit`；diagnosis=`symptom→check order→cause/evidence→action→escalation`；experience=`context/version→decision/tradeoff→lesson/pitfall→applicability/limit`。该 contract 对 `quality-reader` 是完整五维质量入口，对公开 source-digest/SND 是最小 publication hard gate；source-direct-audit 不参加 ReaderTaskPath 判定。stage-heading aliases 固定与 spec §10.1.3 完全相同，只用于找到可见 locator，不是质量分。runtime 从真实 route link 和 Reader 正文重放，不读取内部 JSON 代替走读；每个公开 Reader stage 必须有 semantic relation/Claim/block/hash/locator，错误顺序、主体客体互换、条件范围改变或 Reader 缺 stage 即 `path_replay=failed`。CompanyBrain 的缺口按上一段的 dimension mapping 归类，只有 QualityCase 才计算严格五维优势；分数保留为诊断字段。

质量分数严格执行 spec §11.3 的冻结公式：A/M 分母不得因缺失或 forbidden 缩小，`content_score`/`structure_score` 按 100×通过数/分母、`kd_score=0.7/0.3` 加权并 round-half-up 到两位；空集合为 `UNKNOWN`，forbidden 独立失败，Reader-Audit 等级固定为 `none=0` 至 `claim-exact=100`，两位小数相等为 `TIE`。CB 使用同一 forms/surface/分母。`KD_WIN` 仍要求 hard gate、path replay、同维 CB gap、逐 atom 完成和严格 atom advantage，`kd_score > cb_score` 不能单独产生胜出；M253-R/M253 覆盖公式、分母、空集合、TIE、forbidden、证据等级和篡改负例。

逐原子 machine oracle：每个 projection×dimension 对每个冻结 atom 输出 applicable、双方 status/evidence 和 relation；gap 必须映射同一 CB=`absent` 原子，strict improvement 至少一项 `absent→present`，且无 regression/unknown/forbidden。缺行、重复、错映射、复用或 digest 漂移为 UNKNOWN；CB=`present` 不能创造 KD_WIN。两份 schema 已冻结该合同。

`required_atom_evidence` 的 surfaces matrix 固定为：route 维度只能 `route`；taxonomy 只能 `axis`；business-answer 只能 `summary|slot:<slot>`；page-type 只能 `page_type|summary|slot:<slot>`；Reader-Audit 必须有可达 Reader surface，并可额外使用 `audit`。前四个维度的 audit-only evidence 一律 `UNKNOWN/blocked`。M202/M252 测试必须覆盖 Reader 正文缺失但 Audit 命中、错误 task-path 顺序、两侧等义改写和 CompanyBrain untyped contract。

Quality-result binding rule: `dimension_results` 的 key 集合必须等于该 projection 的 `applicable_dimensions`；每个 `KD_WIN` 都要有 `advantage_basis.projection_key == result.projection_key` 且 `advantage_basis.dimension_id == dimension_result.dimension_id`，`cb_gap_type` 只能来自同一维度的真实 observation，`kd_completion_refs` 必须落在该维度允许的 Reader surface。evaluator 在生成 verdict 前检查 basis 的唯一性、observation digest、snapshot digest、atom rows、gap atom subset、strict improvement、non-regression 和 surface；任何复用、漂移、缺行或跨维度借证据都输出 `UNKNOWN` 并阻断发布。M253 RED/GREEN 必须有对应负例，M401 packet 绑定该结果 schema hash。

CompanyBrain observation：每个适用 projection×dimension 独立绑定 dimension、snapshot/tree/target hash、可见观察、逐 atom status、gap、evidence、locator 和 digest；缺字段、缺/重 atom、跨维复用、digest 漂移或错映射均为 UNKNOWN。M253 覆盖这些 RED，M401 绑定 schema ref/SHA。

### Slice quality aggregation oracle

每个 projection 写状态/reason；聚合为 local `failed` > expected `not_evaluable` > `passed`。fatal 停止 full；两者同时出现保留证据但聚合 failed，released 阻断。

### Publication path map and replay identity

M302 对每个 Reader projection 先计算确定性 public path：`NFKC(product) / fixed_page_type / frozen_route_title`；provider 的 title 必须逐字等于 request 的 `expected_title`，不一致即 blocked。slug 只保留 Unicode 字母/数字、空格和 `-`，拒绝分隔符、`.`/`..`、保留名、空 slug 和超过 96 code points 的标题。相同目录和 slug 冲突时按 canonical `projection_key`/`source_id` 排序，首项用裸 slug，后续使用 `slug-2`、`slug-3`；path map 写入 manifest，重复、覆盖、超长、不可达或 path escape 一律 blocked，不用 hash 文件名或静默覆盖。Home 必须链接 map 中全部 Reader。

request identity 按 spec 的 `selected-source-identity.v1` 计算：`request_identity = SHA256(canonical_json({evaluation_mode, route_kind, source_id_or_projection_key, source_hash, selected_source_paths, selected_source_closure_sha256, query_sha256, config_hash, runtime_contract_id, runtime_contract_hash, semantic_contract_id, semantic_contract_hash, prompt_contract_sha256}) + LF)`。单源 `source_hash` 可非空但 closure hash 必填；多源 `source_hash` 固定 `null` 且 closure hash 同样必填；没有 query 的 source route 写 `query_sha256=null`。source/block rows 分别按 canonical path/source_id 和 raw start/end/block id 排序，以 UTF-8、递归 key 排序、无空格、禁止 NaN、末尾 LF 的 JSON 求 SHA-256；row 必须带 raw content/block hash、locator 和 byte span。closure hash 原样进入 provider/route/semantic ledger/PageProjection/RenderLedger/Audit/quality，重排或 hash drift 必须新 identity、禁止 replay；runtime 或 prompt contract hash 变化也必须新 identity。

同 identity 只复用 hash-bound response；source/config/contract/closure 变化必须新 identity。跨运行 exact replay 查找 `config/task5-replay-store-v1.json` 指定的 `/Users/Hugh/.config/knowledge-digest/replay/task5-semantic-response-ledger.jsonl`（dir `0700`/file `0600`），每条 entry 必须绑定真实 `provider_mode=real`、成功 provider receipt/ref+SHA、call ledger/ref+SHA、恰好一次 HTTP attempt、原始 run identity、当前 source snapshot/closure、runtime/semantic/prompt contract、compiler snapshot 和 parser/semantic-frame snapshot；只存 normalized typed JSON 及上述 hash，不存 key、Authorization、prompt、原始 response、raw source 或主机路径。canonical JSON+LF、append-only/create-only；当前运行先逐字段重验该真实 receipt 和全部 identity，全部精确命中才在新 output 记 `provider_calls=0`，否则 variant、漂移、fake/缺 receipt、权限或格式异常写 failure sink 并 blocked。bundle 只留 replay hash/ref，人工清理前保留；AC-014 覆盖跨运行、缺 store、权限、variant、fake receipt、compiler/parser drift、单源 closure drift、重排、Block drift 和新 output 绑定。

公开 route contract：`bundle/Home.md` 是唯一公开轴索引，必须同时提供“按问题进入”和“按场景进入”两组入口；不生成独立 `modules/`、`boundaries/`、`knowledge/` 目录。每个 Reader 恰好对应两条可回放 route row，字段顺序固定为 `entry_kind(question|scene) → question|entry_scene → product → module → object → scene → boundary → reader_path`。轴值必须来自同一 PageProjection/semantic ledger，不能由文件名猜；Home 直接平铺 Reader、缺轴、跳过问题/场景入口、route row 与 PageProjection 不相等或 route replay 断链都失败。每个实际 render unit 还必须分配 `audit/<public_projection_slug>/u-<ordinal>`，Reader 链接到 `Audit.md` 的公开 anchor，Audit entry 再绑定 source block/hash/locator；M301/M302 逐 Reader 检查 route row、链接目标、Audit replay、禁路径/禁名和内部 ID 泄漏。

### Output path safety and atomic lock boundary

M302 必须在 `output.mkdir`、staging、lock 或 candidate 写入前调用独立的 output preflight。它必须固定 `downloads_root=realpath('/Users/Hugh/Downloads')`，要求 output 是该 root 的新直接子目录且 output 本身不存在；对 raw、CompanyBrain、output 做 realpath 比较，并 fail-closed 拒绝软链接、同一路径、父子目录重叠、历史候选复用、`..` 逃逸、Downloads 外路径和任何既有 output/lock/staging。路径判断不能依赖字符串前缀。preflight receipt 必须记录三方 realpath、run/material identity、存在/软链接状态、overlap 结果和阻断原因；不安全时不创建 output/lock/staging、不发 provider call、不清理既有文件；S0/S1 失败只保留仓库 preflight/lock evidence，`failure_evidence_path=null`，不声称已创建 Downloads failure sink。

failure sink 同一 preflight 校验：目标为 `<downloads_root>/<output_basename>.failure.<run_id>.<owner_nonce>`，必须不存在、非软链、同盘且不与输入/output/lock/staging 重叠；碰撞即 blocked、calls=0，rename 前再次 lstat 且不覆盖。用户 Audit 只留 Claim/source hash/relative locator；failure-safe index 只留 reason、ledger/Audit ref/hash 和 block identity，不留 raw bytes；Audit 未落盘时 `audit_ref=null`。

生命周期固定为：S0 只做 identity/target preflight；S1 preflight 通过后才 `O_CREAT|O_EXCL` 拿 lock 并创建 staging；S2 在 staging 内先校验 M401-R 和 SND contract 的静态 schema/actual/canonical identity，不要求尚不存在的 current SND receipt；随后建立当前 raw snapshot、Block/Claim ledger、SND certificate，并在任何 SND Reader/Qwen/embedding 前运行独立 SND verifier attempt/promotion，生成本次 current receipt。只有通过的 current receipt 才能进入 SND Reader 和后续 release/manifest/run-result 消费。R4/M302 只验证 M401-R 接线能力和 schema 绑定；只有 M402 在读取 raw/CompanyBrain 或发 provider 前校验当前 `M401-R-review-receipt.json` 和静态 SND contract。S2 gate 失败就把最小 Audit 索引原子 rename 到 Downloads failure sink；S3 才读取 source/CompanyBrain 并运行 provider；S4 成功发布或失败/取消保留 sink。S0/加锁失败没有 staging，结果写 preflight/lock evidence；不能同时要求“无目录”又声称已经完成 staging rename。

锁固定为 `<output>.task5.lock`，`O_CREAT|O_EXCL`、owner_nonce 和 `task5-output-lock.v1`；只有 owner 写 staging、更新锁和做一次 atomic rename，竞争/owner 不符/held 都 blocked，不抢锁、不删除、不复用、不发 provider。状态机固定为 `held→rename_committed→finalizing→published`，失败分支为 `held→failed|cancelled`、`rename_committed→failed|publication_ambiguous`、`finalizing→failed|publication_ambiguous`；只有 quality-result finalize 成功并 promotion 后才能写 `published`。candidate QA 不消费 promoted quality result；finalize 重新读取最终目录 manifest/tree，写不可变 finalize receipt 后再 promotion，避免 producer/consumer cycle。rename/finalize/manifest drift 失败时，若能证明 output 是本 owner 本次 tree，则原子移入 `<output>.failure.<run_id>.<owner_nonce>`；无法证明 owner/tree 或 sink rename 失败则状态为 `publication_ambiguous`，保留 output/staging/lock 和证据，禁止 released。逐文件 fsync；崩溃发生在 rename、lock update 或 promotion 之间时，recovery 依据 rename/finalize receipts 和 tree digest 只允许收敛到上述失败态或 published，不得猜测成功。残留 held lock fail-closed，人工检查前不接管。M301/M302 覆盖竞争、SIGKILL、取消、崩溃、sink 失败、owner/tree 不匹配、finalize 失败和锁篡改，并核对单 owner、输入/旧输出不变及可回查证据。

M302 的 output preflight 可在 host-only receipt 记录 realpath；它不得把这些字段复制到 public bundle。发布前扫描 `bundle/` 的 Markdown/JSON，命中绝对路径、用户名、staging、WorkflowHub 路径或 host receipt 即失败。

### Repair sub-gates within the single authorized mini-task

这不是拆新任务，而是把用户要求的同一 Task5 变成可独立停下、可独立回滚的四个证据闸门：

| gate | 覆盖范围 | 必须留下 | 失败处理 |
| --- | --- | --- | --- |
| R1 | provider config/identity/calibration/budget | `quality/evidence/task5/repair-gates/R1.json` | 只回滚 R1 config loader/test patch，保留设计和失败证据 |
| R2 | typed KnowledgeUnit/Qwen/no-fallback | `quality/evidence/task5/repair-gates/R2.json` | 只回滚 R2 adapter/test patch，保留 R1 和 Audit |
| R3 | embedding selected-path consumption/五维 oracle | `quality/evidence/task5/repair-gates/R3.json` | 只回滚 R3 route/evaluator patch，保留 R1/R2 |
| R4 | slice/full runtime/Downloads/89 closure | `quality/evidence/task5/repair-gates/R4.json` | 只丢弃 candidate/staging，保留前三闸门和所有 raw/CompanyBrain |

每个闸门先跑自己的 focused gate，再允许进入下一个；M401 汇总四闸门，M401-R 审查汇总快照，M402 才执行真实 89 条。回滚具体文件、baseline hash、当前 hash 和安全恢复动作以 `task5-repair-baseline-v2.json` 的 `rollback_matrix` 为准。

### Frozen provider budget formula

真实 provider budget 固定为 `max_provider_calls=132`、`retry=0`、`planned=132`：LLM=`87 full source + 12 slice source + 8 full quality + 8 slice quality =115`；Embedding=`2 probe + ceil((88+8)/8) full + ceil((13+8)/8) slice =17`。`G-SOURCE-ND` 是确定性替换，不发 Qwen；不保留额外调用余量；`G-EMPTY-89` 不发请求，source-direct-audit 和 related route 不计入本 revision。

每个 `evaluation_mode` 的每个非空 source/projection 只允许一次逻辑 request；full/slice receipt、vector、closure 不互用。request identity 使用上面完整 canonical key；2xx contract/lineage/relation/raw-copy 按当前 mode-local 失败继续清单，transport/auth、预算、身份、配置、锁和取消为 global fatal。`planned/observed/http_attempt_count` 必须可回查，`observed>132` 或无法证明一次 HTTP attempt 立即 overrun/blocked，不能重试。

R1 重算 `115+17`，覆盖 retry/probe/replay/drift，并校验 slice hash/11/14/13。

### Typed page evidence binding

`required_atom_evidence` 由编译器按 `unit→Claim→Block/hash/locator` 派生，形状和 surface matrix 以 spec 为准；Qwen 不自报事实。字段/集合/surface 不一致为 `UNKNOWN`，不得进入 Reader/KD_WIN，hash 写入 receipt/RenderLedger。实现只读取并 hash 校验完整 v2 QualityCase，不复制 fixture。

## Canonical oracle appendix（implementation preflight input；design review 只检查声明）

2026-08-25 contract revision: answer-critical Claim refs are `Reader.body+Audit`; source-detail/archive refs are `Audit`, while Audit retains complete source closure. Q-POS core-entry detail is Audit-only. Raw heading/image-only refs in Q-POS/Q-OPR/Q-DIA/Q-BND were corrected, including Q-CON-01 VPN/global-proxy blocks. The current runtime-bound actual SHA-256 is `8d2a5024bce31bd48709d363bbf8cf578b18b46be732f58e4bd133f881c32f67`. The same fixture now freezes semantic contracts for question routing, five-axis taxonomy, business-answer stages, visible page type, and Reader/Audit traceability. Earlier hash mentions in historical review prose are superseded and are not runtime authority.

以下只声明实现 preflight 的冻结夹具、schema、hash 和 rehash 责任；完整 JSON 是唯一 authority，runtime 必须读取实际字节，缺失/漂移即 blocked，不能从 prose 重建：quality cases=`config/task5-quality-cases-v2.json`（actual `8d2a5024bce31bd48709d363bbf8cf578b18b46be732f58e4bd133f881c32f67`、canonical `281ced2464a2d7dfd035aecf084cc21ef87ed8f8c6485993a6287375e8af1654`）；CompanyBrain baseline=`config/task5-companybrain-baseline-v2.json`（actual `ba69f3ce…`，显式 projection_keys）；source manifest=`config/task5-source-page-manifest-v2.json`（89 条）；slice fixture=`config/task5-slice-cases-v1.json`（actual `4ebccc3d…`、canonical `f3337ac1…`、11 cases/14 descriptors/13 risks）；rollback baseline=`quality/evidence/task5-repair-baseline-v2.json`（actual `6d9098d4…`、canonical `410182a9…`）。M251/M252 仍逐 projection 读取 CompanyBrain baseline 并生成 host-only/public route snapshot：host 可含 root_realpath，Downloads 只含脱敏 public projection；每个 observation 绑定目标/入口文件 hash、snapshot/tree digest、维度、locator、scanner version 和允许 gap mapping。`root_realpath` 不得泄露。slice/full 使用精确 source paths，`missing_full_source_paths` 只产生 `source_not_in_slice/not_evaluable`；Q-DIA full=7、slice=2；不得改 fixture 或跨 mode 复用 evidence。M401 pre-M402 readiness 只证明快照存在，不产生质量 verdict；M402 必须重新生成 actual_run snapshot。rollback 只消费 baseline 的 before hashes，after/patch/inverse 只能由 gate receipt 产生。

### WorkflowHub identity handoff execution rule

`mini_task.design` 的 replay code 必须先读取 WorkflowHub adapter 通过 TaskKernel/Workspace 认证生成的 `design_preflight` handoff，确认 parent canonical make-decision stage-outcome 的 result/attempt ref+SHA、attempt_id、原始需求与三轮 Talk attestation、当前 worktree snapshot/material revision/material_id、design-review contract/semantic identity 和 writer attestation；另确认 Task5 runtime/semantic contract identity。缺失或漂移在设计 provider 前 STOP。M101/M401 接受该不可变 `design_preflight` handoff；design terminal clean、M401 和 M401-R 都通过后，才由 adapter 生成包含 design/implementation refs 的 successor `implementation` handoff，只有 M402 接受 successor。任何 caller 传入的 `snapshot_tree`/`material_id` scalar 旁路、handoff 缺失、循环引用或 task/worktree/hash 不匹配都必须在 receipt、RED 或 provider 前 STOP，后续 gate 只继承该不可变 identity。

### 2026-08-25 execution checkpoint

已实现并通过 focused regression：CompanyBrain 完整快照判定、自然语义与可见分类面分离、Q-POS/Q-CON direct-answer 检查、source-bound stage 的行级非泛词匹配、live embedding transport 计数。r31 仅做离线重算验证，结果五维全 `KD_WIN` 但不能作为新运行证据；下一步必须用新 Downloads 目录重新执行 slice→full，并检查真实 embedding ledger、89 条闭包和全部发布门。

## 2026-08-31 极简架构实施修订（以本节替代并行 Task5 runtime 继续扩展）

上一版 plan 虽然覆盖了很多门禁，但仍允许实现者继续在 `task5_runtime.py/task5_provider.py` 上打补丁，和用户要求的“简洁好维护”冲突。自本节起，实施只认下面这条链：

```text
digest CLI → compiler.digest → providers(Qwen/Jina) → publisher.commit
```

### 实施硬边界

- `task5_runtime.py`、`task5_provider.py`、旧 evaluator 不得被生产入口 import；完成切换后移入历史目录或删除。CI 必须有“旧模块零 import、旧脚本零写入”的反例测试。
- `Evidence` 和 `ReaderPage` 是仅有的语义对象；`RunManifest` 是机器闭包索引，必须逐条列出 89 个 source、每个页面、每个 route 和最终 surface hash，但不能写业务正文。
- Qwen typed JSON 是唯一业务正文输入；renderer 不重写、不添加、不修补业务句子。非法/缺证据/原文复制直接 Audit-only。
- Jina 每个 route 产生 selected closure，并且 selected source/page IDs 必须与实际 Qwen 输入和 Home route 完全相等；只有收据没有消费算失败。
- `page_key` 固定为 `source:<source_id>` 或 `answer:<question_id>:<page_type>`；来源终态和缺页状态固定，不能用空模板或另一个 page type 顶替。
- `_digest` 机器输出固定为 `run.json`、`evidence.jsonl`、`sources.jsonl`；公开只保留 `Home.md`、`Audit.md`、`products/`，不生成 `modules/`、`boundaries/`、`knowledge/`、hash-only 文件名和 staging/attempt 路径。

### 实施顺序与停止条件

1. **入口切换**：让 `digest` 直接调用新 `compiler.digest`；固定 Adapter 测试能观察 Qwen/Jina 请求，且旧 Task5 模块未 import。
2. **最小垂直切片**：完成一个 source page、一个 cross-source answer page、Home route、Audit exact block 回查和原子发布；先跑 golden test。
3. **全量编译闭包**：同一入口完成 89 条来源终态；空源/失败源不进 Reader 但必须进 RunManifest/Audit；所有非空来源都尝试 Qwen，失败不回退 raw-copy。
4. **真实 provider 消费**：Qwen typed schema 与 Jina selected closure 均有 request/response/receipt；改变固定 embedding 结果会改变 route，证明 Jina 是消费者。
5. **真实 Downloads 运行**：写新的 Downloads 目录，先检查 source/Reader/Audit 闭包与页面可读性，再运行五维逐 projection 对照和独立 review。任一维不是 `KD_WIN`，终态 `not_released`。

每一步失败都保留证据并停止发布；不新增“补丁阶段”、不把失败交给下一任务、不用静态 fixture 或 CompanyBrain 事实补正文。

## 2026-08-31 3rd-review 可执行补充

以下条目是本计划的硬验收，不是额外需求：

1. **先完成迁移终态**：删除 `task5_runtime.py`、`task5_provider.py` 和旧 Task5 写入脚本在工作树中的生产可导入路径；保留历史结果只放 `quality/evidence/`。增加生产入口 import 反例测试。
2. **固定机器合同**：实现 `RunManifest` 严格 schema；source/page/route 数量、重复项、状态与列表必须一致。哈希使用规范化 UTF-8 JSON；`question_id`、`page_key`、`payload_sha256`、`surface_sha256`、`tree_sha256` 按设计文档公式测试。
3. **固定 89 条闭包**：从冻结 source manifest 逐条核对 raw path/hash/status。`blank_source`、`duplicate_alias`、`provider_failed`、`unsupported_format` 都必须可回查；任何缺行、增行、状态漂移停止。
4. **证明 Jina 被消费**：descriptor 只来自 raw/Evidence；route ledger 写候选、selected、rank、score、request/response hash、Qwen payload hash；固定向量变更必须改变 selected closure 和 payload hash。
5. **移除语义暗门**：质量页只允许一次 Qwen typed compile；renderer 不得修补正文；非法结果只进 Audit。新增非法 JSON、closure 外引用、原文复制、缺 Evidence 和不完整页面的失败测试。
6. **调整质量分支覆盖**：quality-config 运行同时生成可回查的 canonical source pages 和 12 个 frozen answer pages；不能再用“只生成 12 页”冒充 89 条全量。预算按实际最大请求数预检。
7. **最终证据**：新 Downloads 目录只产生 `Home.md`、`Audit.md`、`products/`、`_digest/run.json`、`_digest/evidence.jsonl`、`_digest/sources.jsonl`；不得出现 `modules/`、`boundaries/`、`knowledge/`、hash-only 文件名或 staging/attempt 路径。五项比较必须逐 projection×dimension 读取真实 Markdown；非全 `KD_WIN` 保持 `not_released`。
8. **失败也要落盘**：单个 source/route/provider 失败必须在 RunManifest 写明确终态和 reason，候选可以原子提交为 `not_released`；只有输入闭包、输出 schema 或发布安全性无法判断时才 `blocked` 且不写半套目录。
