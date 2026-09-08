# Task5 当前生效任务卡 v4.7（2026-09-04）

> 只有本节生效：从文件开头到本文件末尾的唯一归档分隔线之前全部属于当前任务卡；归档分隔线及其后全部内容是历史资料，旧命令、旧 hash 和旧输出树均不再授权执行。

## 当前修订 v4.7（2026-09-04）：进入实现前的页面、状态和 fixture 硬核对

M402 的最终 public `_audit` 只允许 runtime 固定的十一项文件；`bundle/_audit/run-result.json` 是 public receipt。`quality-result`、CompanyBrain observation 和 host-run receipt 都由同一 M402 attempt 写入 `quality/evidence/task5/actual-run/` 的不可变证据，run-result 只保存 quality artifact 的 ref+SHA，不复制第二份质量结果。

LINEAGE-001 的唯一缺口例外是精确 `原始资料未明确` 且无 evidence 的 section：保留 `Reader.section` 与 `Reader.answer_body` 两行 ledger，分别计入 `unknown_units`，不伪造绑定，也不进入事实 lineage 分母；其余事实 unit 必须 100% raw-bound。

`AC-v4-01…AC-v4-13` 的唯一完整定义在 active `spec.md`；本任务卡只记录执行入口和证据归属，不复制第二套验收定义。

这四项是同一 Task5 的实现验收子项，不是新增任务或后续任务；未全部有当前 receipt 前，M401 不得通过。设计审查不属于这些硬门：`mini_task.design` 没有可认证的 `terminal-clean` 结果时，只记录 DESIGN-ADVISORY 的缺失/风险，不阻断 M401、M401-R 或 M402。

- **ENTRY-001**：检查 `pyproject.toml` 的 `digest` 入口和 `simple_cli.main` 的调用图；允许它作为薄适配层，但必须证明业务编排唯一进入 `compiler.digest`，CLI 不生成业务文本/分类/质量 verdict，旧 runtime/provider/evaluator 零生产 import。
- **OUTPUT-001**：用 fake/no-network 运行真实 public entry，验证正式结果只在隔离测试 run root 的 `bundle/` 产生；Reader 只从 `bundle/Home.md` 进入 `products/<product>/<page-type>/...`，机器闭包只能精确包含 active spec 开头列出的十一项 `_audit` 文件，且不得产生 `_digest/modules/boundaries/knowledge/staging/attempt` 公共路径。真实 Downloads 只由 M402 写入。
- **BASELINE-001**：构造 CompanyBrain 文件 hash/tree、raw source manifest、observation 的漂移和跨 run 负例；验证 `quality.py` 只接受同一 M402 的 `companybrain_snapshot_id/companybrain_tree_sha256/observation_sha256/source_manifest_sha256`，缺失或漂移只能 `CB_MISSING/UNKNOWN`。
- **LINEAGE-001**：构造 Reader 标题、问题、正文句、五轴、页面类型、section 和 Home route 的无 evidence、错 source、错 raw hash、错 locator、重复 unit 负例；验证 compiler 中间 evidence ledger 每个可见 unit 恰好一行且 `lineage_coverage=100%`，再验证 formalizer 移除中间 ledger 后 public bundle 仍由 active 十一项机器闭包回查，失败时不发布。

每项都要记录：当前命令、输入 snapshot/material、stdout/stderr/result hash、实际结果、失败反例和 `attempt_id`。凡是 gate 写隔离 run-root，`attempt.json` 必须写 `run_root_ref`；M401-R 不写 run-root 时不得生成伪造引用。不能用旧测试、旧候选、静态质量 JSON 或“文件存在”替代；这四项通过后仍必须经过 M401、authenticated M401-R 和真实 M402。

Provider 配置的执行边界也属于当前任务卡：默认读取 `~/.config/knowledge-digest/config.json`，M402 的 authenticated runner 可用显式 `--provider-config` 覆盖；LLM 只准 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`，embedding 只准 `https://llm.paxszapp.com/v1` 的 `jina-embeddings`，receipt 必须写实际模型。每个 provider section 先取直接 `api_key`，缺失时才按 `api_key_env` 回退；根级 `api_key` 仅作迁移兼容补入缺失 section。配置、key、endpoint、model 或 calibration 的 preflight 失败必须在首个请求前记录 `blocked|unavailable` 与 `provider_calls=0`；密钥不得进入任何 public/host receipt、payload、cache 或报告，绝对配置路径仅 host-only 可见。

补充反例必须落到对应卡片：C2 校验 `qwen_payload_sha256` 绑定实际 `model.generate` payload 字节；LINEAGE-001 校验同一 `route_name` 重复命中同一 `home_target_page_identity` 时渲染前失败；C0/BASELINE-001 校验 CompanyBrain observation row 的 `status` 只接受 `present|absent|unknown|forbidden`，并按 spec 映射 `CB_MISSING/UNKNOWN/N/A`，不得由实现自行扩展。

四组行为测试的 gate owner 固定为：`ENTRY-001` 与 `OUTPUT-001` 在 `tests/acceptance/test_task5_publication_contract.py`；`BASELINE-001` 在 `tests/acceptance/test_task5_quality_gate.py`；`LINEAGE-001` 在 `tests/acceptance/test_task5_projection.py`。M401 focused/full 命令必须覆盖这三个 owner 文件，其他测试只作相邻回归，不替代四组 owner。逐 AC trace 的 implementation anchor 必须落在真正覆盖该 AC 的具体测试函数；当 gate owner 只覆盖通用入口、而具体 Reader/Home/lineage 行为由 `tests/test_simple_digest.py` 覆盖时，允许 AC trace 引用该相邻回归，但不能因此取消 gate owner 的覆盖要求。`tests/acceptance/test_task5_full_run.py` 是 M401 full 的 slice→full/run-result 回归 owner，负责验证运行级闭包和非网络完整编排；它不替代上述四组行为 owner。

C0 的 authority/schema/hash/slice 派生测试唯一承载文件为 `tests/acceptance/test_task5_contract.py`；该文件与四组行为测试同属当前 Task5 测试面，C0/M401 命令必须显式包含它。

M402 表格中的通过条件与 spec 同义且更具体：所有 `applicable=true` 的 projection×dimension row 必须为 `KD_WIN`，所有 `applicable=false` 的 row 必须恰为 `N/A`，矩阵不得缺行、重复或多出其它 verdict；“五维全 KD_WIN”不能单独作为通过依据。

slot 的 `route_name:page_identity` 和 `route_name:home_target_page_identity` 只表示 `route_name + ":" + home_target_page_identity` 实际值，字段名不进入 bytes。M401-R receipt 采用 `task5-m401-r-review-receipt.v1`，除现有字段外必须含 `source_receipt_ref`、`source_receipt_sha256`，顶层 promotion 只原样提升 attempt-local source receipt。纯 lineage/quality 失败按 `not_released`/exit 1，global identity/authority/provider 失败才按 `blocked|unavailable`/exit 2。

M401 packet 同样由 authenticated adapter 将通过 attempt source 原样 promotion 到 `quality/evidence/task5/M401-evidence-packet.json`；source ref/SHA 只记录在同一 M401 attempt 的 `attempt-receipt.json`，promotion view 与 source bytes 完全一致。M402 host-only `quality-result.json` 顶层必须写 `companybrain_snapshot_id`、`companybrain_tree_sha256`、`observation_sha256`，逐 row 的 CompanyBrain digest 必须与其一致；public bundle 只保存该 artifact 的 ref+SHA。

C0、M401 和 verifier 共同执行同一组边界：受控 fixture 行数统一写作 `fixture_source_count`，只有 M402 的真实 RunManifest 要求 89 行；隔离 bundle 的 `run_root_sha256` 只覆盖除两个 run-result 文件外的 regular files；title slug 使用 Unicode `Letter`/`Nd`，非空 title 的空 slug 为 `untitled`，空 title 失败；失败索引 basename 固定为 `bundle`；空 body section 不渲染且不生成 `section`/`answer_body` unit；每个 manifest route row 都是唯一非空目标的 `Home.route` row。M401 packet 的 `attempt-receipt.json.packet_sha256` 是 packet 完整 UTF-8 文件 SHA，并与 M401-R 的 `m401_packet_sha256` 相等。每个 `(product_key,page_type)` 目录维护全局最终文件名占用集合，按 `(product_key,title,page_id)` UTF-8 bytes 升序从 `base_slug`、`base_slug-2`、`base_slug-3`……选择首个未占用名，追加前将 base 截断到 `100-len("-N")` 个 Unicode code point，且其它 base slug 组的基名和后缀名也算已占用。上述规则必须在 C0/M401 的跨组碰撞和边界反例中留证。

### v4.4 当前纠偏：历史 V50 只留证，不挡当前 raw-only 门

`ROOT-CAUSE/D0-H` 对精确 V50 的回放仍要执行，缺失时固定留下 `blocked/calls=0` attempt；但该历史 attempt 不再是当前 M401/M402 的硬前置，不得要求 promotion，也不得拿另一个候选补洞。当前 M401/M402 的真实依据是 D0-R 的 raw 89 条、当次 CompanyBrain snapshot、真实 Qwen/Jina、五项逐格结果以及 Reader/Audit 闭包。当前 CompanyBrain baseline 由当次 authenticated M402 snapshot 绑定，不再依赖历史 `RC-CURRENT-BASELINE` 成功回放。

SND 使用 `SND-RULE-002`：明确的否定/描述性语境（如“不会”“没有”“避免”“不可预知”“优点”“缺点”）中的触发词归为 `no_rule`；触发词加动作词仍为 `rule`；没有动作词也没有明确描述性语境才是 `ambiguous`。这条只修复误判，不放宽真实异常规则的证据要求。

Provider adapter 每个 `(provider, request_identity)` 只允许一次 HTTP attempt（`retry=0`）；编译器恢复是有界逻辑：source 全局最多 12 次 recovery call、单 source 最多追加 3 次，quality projection 校验失败最多再发 1 次完整 Qwen 页面。质量事实校验固定一页一请求，避免多页响应的 page identity/结果数漂移。每次 recovery 必须写入 trace、hash 和 call plan，不能拼接或由 Python 改写正文；耗尽预算后保留 Audit-only/not_released。

## 0. 总 STOP 规则

合同 identity、当前 snapshot/material、provider 配置、测试 receipt、source closure 或 output manifest 无法从真实字节验证，就停止并记录 `blocked`；可选 DESIGN-ADVISORY 没有 terminal-clean 结果不属于阻断条件。不得填静态 JSON、复用旧 receipt、拿 pytest 绿冒充 released。

## DESIGN-ADVISORY：可选设计审查记录

如能取得 authenticated `make-decision` `design_preflight` handoff，就使用当前四份材料记录 WorkflowHub `mini_task.design` 的审查事实、风险和 finding disposition；没有 canonical result、review unavailable、partial、漂移或未处置 finding 时只记录 advisory 状态，不伪造通过，也不阻断 M401/M402。`parent_design_review=null` 是合法的“未等待设计审查”标记。

## ROOT-CAUSE：旧结果根因记录（不阻断当前 raw-only）

执行 provider-free `replay_root_cause()`，只用冻结 root-cause input manifest、精确旧候选和 CompanyBrain/raw 元数据。旧 V50 不可回查时必须生成 `blocked/calls=0` 证据，保留待验证假设；不得用其他候选补洞。该证据只作为 M401 的 AC-v4-13 历史限制记录，不进入当前 raw-only release predicate。

## C0：合同一致性

读取 `spec.md`、`plan.md`、`tasks.md`、`decision-log.md` 的 active sections 和 active authority 闭包；重算 schema/hash/枚举、size 和交叉引用；从 slice JSON 派生 11 case/27 source paths。只在当前生效字段把旧常量写成旧口径（例如旧 slice 的 14 case/12 path）时停在 design repair；当前合法的 `P=12` projection、11 case、27 unique path 不触发该规则。两套架构、两套输出树或两套 schema 仍直接阻断。C0 的 authority inventory 必须作为 M401 的输入，不以 prose 或旧 receipt 替代。

`RunManifest.pages` 必须使用 spec/plan 同一 `knowledge-digest-page-row.v1`：字段恰好为 `page_id/page_key/page_type/axes/source_ids/path/surface_sha256`；`page_type` 只能是 `positioning|concept|operation|diagnosis|experience`，分别对应定位/概念/操作/诊断/经验。Reader path 只按 `products/<product_key>/<page_type>/<filename>.md` 的已映射产品键、title slug、截断和同名后缀公式生成；未知一级产品固定 `unclassified/unsupported`、不生成 Reader/page row；`pages` 按 `page_id` UTF-8 bytes 排序，不能按输入或模型顺序命名。M402 的真实 RunManifest 才要求 89 行；C3/M401 fixture 使用自身受控行数但需同一 schema/闭包。M401-R receipt 的字段还必须包含 `status`、`reason_code`，并按 spec 映射：`available → NONE/passed/semantic`，`needs_human|partial → QUALITY_GATE_FAILED/blocked`，`unavailable → REVIEW_UNAVAILABLE/unavailable/transport|cancelled`；非 available 均不得进入 M402。M401 的 `fixture_bundle_sha256` 等于 C3 fixture tree hash，`fixture_manifest_sha256` 等于 fixture 内嵌 RunManifest 的 canonical hash，二者不可混用。

## 当前卡片的执行与留证合同

每张卡都必须由当前 WorkflowHub attempt 执行；失败 attempt 只写 attempts 目录，不能覆盖 promotion view。表中的命令/入口、receipt schema、exit 和 promotion 是生效合同，历史归档中的旧命令不再授权。

| 卡片 | 当前入口 | receipt 路径 | 通过条件 | 失败结果 |
| --- | --- | --- | --- | --- |
| DESIGN-ADVISORY | authenticated `mini_task.design` adapter（可选） | 可回查的 review fact；没有结果也记录 unavailable | advisory 已记录或明确未取得 | 不阻断 M401/M402 |
| ROOT-CAUSE | `replay_root_cause()` provider-free | `quality/evidence/task5/root-cause/attempts/<id>/root-cause-evidence.json`（schema=`task5-root-cause-evidence.v2`） | V50 可回查且映射完整 | unavailable/blocked、calls=0；不使用 repair-gate inverse |
| C0 | `uv run --frozen pytest -q tests/acceptance/test_task5_contract.py` | `quality/evidence/task5/repair-gates/attempts/<id>/C0/attempt.json` | authority/schema/hash/slice 派生和入口反例通过；无 run-root | `status=failed|blocked|unavailable`；run-level `not_released` 归一为 `failed` |
| C1 | `uv run --frozen pytest -q tests/acceptance/test_task5_source_semantic.py` | `quality/evidence/task5/repair-gates/attempts/<id>/C1/attempt.json` | 89-source/locator 反例通过；无 run-root | `status=failed|blocked|unavailable`；run-level `not_released` 归一为 `failed` |
| C2 | `uv run --frozen pytest -q tests/acceptance/test_task5_provider.py tests/test_simple_providers.py` | `quality/evidence/task5/repair-gates/attempts/<id>/C2/attempt.json` | fake Qwen/Jina/失败语义通过；无 run-root | `status=failed|blocked|unavailable`；run-level `not_released` 归一为 `failed` |
| C3 | `uv run --frozen pytest -q tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_quality_gate.py tests/acceptance/test_task5_projection.py tests/test_simple_digest.py` | `.../attempts/<id>/C3/attempt.json` + `.../attempts/<id>/C3/inverse.patch` + `C3/run-root/bundle/` | fake/no-network Reader/Audit/quality 独立通过；有 `run_root_ref`、before/after hash 和 reverse-apply 证据 | `status=failed|blocked|unavailable`；run-level `not_released` 归一为 `failed` |
| IMPLEMENT-CURRENT | `uv run --frozen pytest -q tests/acceptance/test_task5_contract.py tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_provider.py tests/acceptance/test_task5_source_semantic.py tests/acceptance/test_task5_quality_gate.py tests/acceptance/test_task5_projection.py tests/test_simple_digest.py tests/test_simple_providers.py` | `quality/evidence/task5/repair-gates/attempts/<id>/IMPLEMENT/attempt.json` + `inverse.patch` | 生产链真实连通、quality.py 唯一裁决、旧 runtime/provider/evaluator 零生产 import；不写 run-root；receipt 记录 before/after/path hashes 和 `git apply --check --reverse` 结果 | failed/不进入 M401 |
| M401 | focused=`uv run --frozen pytest -q tests/acceptance/test_task5_contract.py tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_provider.py tests/acceptance/test_task5_quality_gate.py tests/acceptance/test_task5_projection.py tests/acceptance/test_task5_source_semantic.py tests/test_simple_digest.py tests/test_simple_providers.py`；full=`uv run --frozen pytest -q tests/acceptance/test_task5_contract.py tests/acceptance/test_task5_full_run.py tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_provider.py tests/acceptance/test_task5_quality_gate.py tests/acceptance/test_task5_projection.py tests/acceptance/test_task5_source_semantic.py tests/test_simple_digest.py tests/test_simple_providers.py`；packet writer=`uv run --frozen digest --gate M401 --fixture-bundle quality/evidence/task5/repair-gates/attempts/<c3-attempt-id>/C3/run-root/bundle --m401-attempt quality/evidence/task5/repair-gates/attempts/<id>/M401 --m401-run-root quality/evidence/task5/repair-gates/attempts/<id>/M401/run-root`；两个 pytest 命令只写 AC trace/test receipt，`attempt.json` 与 `attempt-receipt.json` 的单值 `command` 只记录上述 packet-writer 命令及完整 argv 字节；fixture-bundle 必须是通过 C3 的不可变 bundle，runner 复核其 manifest/tree/material identity；不得读取 raw、CompanyBrain 或 provider。 | attempt=`quality/evidence/task5/repair-gates/attempts/<id>/M401/attempt.json`；attempt receipt=`.../M401/attempt-receipt.json`；packet=`.../M401/M401-evidence-packet.json`；inverse=`.../M401/inverse.patch`；run-root=`.../M401/run-root/bundle/`；promotion=`quality/evidence/task5/M401-evidence-packet.json` | AC-v4-01…13 每项均有七字段 trace；attempt 有 before/after/inverse hash；隔离 run-root 只有唯一 bundle | 不 promotion |
| M401-R | authenticated WorkflowHub `mini_task.implementation` adapter | source=`quality/evidence/task5/repair-gates/attempts/<review_attempt_id>/M401-R/M401-R-review-receipt.json`；review-result=`quality/evidence/task5/repair-gates/attempts/<review_attempt_id>/M401-R/review-result.json`；promotion=`quality/evidence/task5/M401-R-review-receipt.json`（只允许原样提升 source bytes/hash）；两份 receipt 字段全集含 `schema_version/review_kind/m401_packet_ref/m401_packet_sha256/review_result_ref/review_result_sha256/source_receipt_ref/source_receipt_sha256/snapshot_tree/material_id/terminal_status/terminal_clean/all_findings_disposed/finding_dispositions/outcome/status/reason_code`；review-result 按 canonical UTF-8 JSON+LF 计算完整文件 SHA-256 | 审查同一 M401 packet/current snapshot；terminal semantic clean；所有 finding 有 disposition；attempt 有 inverse hash | blocked，不进入 M402 |
| M402 | `uv run --frozen digest <raw_input> <downloads_run_root> --companybrain-root <companybrain_root> --config config/task5-reader-quality-provider-v2.json --provider-config <provider_config> --gate M402 --m401-packet quality/evidence/task5/M401-evidence-packet.json --m401-r-receipt quality/evidence/task5/M401-R-review-receipt.json --workflowhub-successor quality/evidence/task5/workflowhub-implementation-handoff.json`（`raw_input`、`companybrain_root`、`provider_config` 和 Downloads 输出根由 authenticated runner 注入；实际路径/身份只进 host-only receipt 的 `provider_config_ref` 等字段） | `<authenticated Downloads run_root>/bundle/_audit/run-result.json`；host-only=`quality/evidence/task5/actual-run/attempts/<id>/host-run-receipt.json` + `companybrain-observation.json` + `quality-result.json`（均由同一 M402 attempt 写入，不进入 public bundle） | 真实 89 条、四产品、Jina/Qwen、Reader/Audit 闭包；所有 `applicable=true` 行为 `KD_WIN`、所有 `applicable=false` 行恰为 `N/A`，且 projection×dimension 矩阵无缺行、重复或其它 verdict；host receipt、observation、quality artifact、public run-result 和最终 tree/hash 互相闭合 | `not_released/blocked` |

C0–C2 只验证合同、输入/反例和 fake provider seam；C3 是独立的 fake/no-network Reader/Audit/quality contract attempt，必须使用自己的隔离 `run_root_ref`，不能和 M401 的实现审查或 M402 的真实 Downloads 运行合并为同一张卡。C3 的 attempt、bundle 和 receipt 都必须留在 `repair-gates/attempts/<id>/C3/`；M401 只消费这些不可变字节和反例结果，不把 C0–C3 的合并 pytest 退出码当作 C3 已执行。

`M401-R-review-receipt.json` 固定包含 `schema_version`、`review_kind`、`m401_packet_ref`、`m401_packet_sha256`、`review_result_ref`、`review_result_sha256`、`source_receipt_ref`、`source_receipt_sha256`、`snapshot_tree`、`material_id`、`terminal_status`、`terminal_clean`、`all_findings_disposed`、`finding_dispositions`、`outcome`、`status` 和 `reason_code`，不得省略或增加未声明字段。M401-R 先在自己的 attempt 目录写不可变 source receipt，再由同一 authenticated adapter 原样提升到顶层 promotion view；promotion view 不追加 source ref/SHA，也不能另写或编辑内容，来源 ref/SHA 只保留在 receipt 自身的固定字段中。M401-R 只读 `.../M401/M401-evidence-packet.json`、同目录 `attempt.json`、`attempt-receipt.json` 和 `inverse.patch`，并复算 packet/attempt receipt SHA 后完成 inverse 校验；通过后才更新 promotion view，不判断真实五维胜负；M402 才负责真实运行和五维结论。BASELINE-001 只使用 fixture 构造的 CompanyBrain 树/hash，真实 CompanyBrain 仅在 M402 读取。

## C1：89 条 Evidence 闭包

C1 是离线只读合同门，不读取用户 raw、CompanyBrain 或 provider，也不写 host-run-receipt。它使用冻结的 `task5-source-page-manifest-v2.json`、受控 fixture 和 source semantic 测试，验证 89 行 source manifest 的字段、产品归属、Block/Claim locator、content hash、空源/重复别名/失败状态和 compiler 中间 `_audit/sources.jsonl` 映射。真实 89 条 raw 的快照、Block/Claim 生成和 `source_manifest_sha256` 只由 M402 的 `compiler.digest` 在 authenticated runner 中完成；M402 再按 89 个 RunManifest source rows 的 canonical JSON 规则重算，并与中间 projection 相等；该文件在 formal audit 前移出 public bundle。

## C2：Qwen/Jina

先用 fake adapter 和 network deny 覆盖成功、坏 JSON、未知字段、越界引用、原文复制、provider failure、Jina closure drift；Qwen 单源 schema/引用/原文复制失败按 local failure 留证并继续，鉴权、配置、contract hash、预算和全局身份失败按 global failure 立即 blocked/unavailable；再做只改变 fake vector/rank 的因果反例，确认 selected paths、route ledger hash 和 Qwen payload hash 会变化，route-only path 不进入 payload。C2 是 fake/no-network gate，不读取真实 `provider_config`，不写 host-only receipt；真实配置读取、路径留证和 provider 调用只在 authenticated M402 runner 发生。Qwen 必须是 `task5-semantic-output.v2`；Jina selected closure 必须逐字进入 Qwen payload、ReaderPage 和 Home route；renderer 零语义 overlay。

## C3：Reader、Audit、质量

用 fake/no-network fixture 生成唯一隔离路径 `quality/evidence/task5/repair-gates/attempts/<attempt_id>/C3/run-root/bundle/`；M401 使用同样规则但路径为 `.../<attempt_id>/M401/run-root/bundle/`，M401-R 不生成 bundle。bundle 包含 `README.md`、`Home.md`、`Audit.md`、四个产品目录和 active spec 的十一项 `_audit` 机器文件。README/Audit/Home 固定壳只能由 fixture machine evidence 确定性重建，出现动态业务句直接失败；Home 同时有问题/场景入口，Reader 可见五轴和页面类型，Audit 必须实际包含 `#evidence-<evidence_id>` 锚点并可回查 block/claim/hash/locator；质量从 fixture 页面重算只验证算法，不产生真实优胜结论。真实 Downloads、raw/CompanyBrain 页面和真实五维结论只能由 M402 生成。

## IMPLEMENT-CURRENT：生产链实现与可回滚证据

只修改 `plan.md` 允许的生产文件；唯一运行入口必须是 `digest CLI → compiler.digest → providers → quality.py → publisher.commit`。实现卡必须逐项证明：`simple_cli.py` 调到 `compiler.digest`；`compiler.py` 实际调用 `providers.py` 的 Qwen/Jina；Qwen typed semantic output 进入 ReaderPage，Jina selected closure 进入 Qwen payload 和 route ledger；`quality.py` 是唯一质量裁决器；`publisher.py` 完成锁、staging、manifest/tree 校验和原子提交；`task5_runtime.py`、`task5_provider.py`、旧 evaluator 在生产 import graph 中不存在。上表命令是实现卡唯一测试入口；通过后由当前 build-code owner 在 `quality/evidence/task5/repair-gates/attempts/<id>/IMPLEMENT/` 写 `attempt.json` 与 `inverse.patch`，IMPLEMENT 不生成或保留 run-root，按 plan §2.1 的临时副本 reverse-apply check 验证后才允许 M401。测试通过但实现卡、receipt 或逆补丁缺失，仍视为未完成。

## M401：实现就绪

前置为 D0-R、C0–C3、独立的 IMPLEMENT-CURRENT attempt/inverse 证据和当前实现代码/测试证据，不再要求 DESIGN-ADVISORY 的 terminal-clean 结果。D0-H 的 V50 blocked attempt 只作为 AC-v4-13 历史限制被记录，不要求 promotion，也不阻断 M401。执行声明的 Task5 focused/full fake no-network tests，按 `spec.md` 的 AC-v4-01…AC-v4-13 生成当前 AC trace、authority inventory、test receipt、implementation material 和 M401 packet；不调用真实 provider，不写真实质量通过结论。失败只保留 attempt evidence。

## M401-R：实现审查

由 authenticated WorkflowHub adapter 执行 `mini_task.implementation`。必须 available、terminal semantic clean、所有 finding 有真实 disposition，并生成 implementation successor；unavailable/partial/non-terminal/未处置 finding 一律 STOP。

## M402：真实 slice→full

执行表中的 C3、M401 若写隔离 run-root，必须在各自 attempt 的 `attempt.json` 写真实非空 `run_root_ref`；IMPLEMENT/M401-R 不写 run-root 时按 `task5-repair-gate-attempt.v1` 固定写出 `run_root_ref=null`；C0–C2 使用 `task5-readonly-gate-attempt.v1`，固定写出 `run_root_ref=null`。这里的 null 是字段值，不是省略字段。C3 不再靠共享路径约定补充这一字段。

前置为当前 M401 packet、M401-R promoted receipt、符合 active `spec.md` 的 `workflowhub-implementation-successor.v1` handoff 三方 identity 完全相等。只读取 raw 和 CompanyBrain，在 Downloads 新目录用一个共享 run context 先运行 slice、再运行 89 条 full；记录真实 Qwen/Jina、Reader/Audit、RunManifest、五项比较和发布状态。slice 成功的 source-digest 只可通过 receipt-bound exact identity 被 full 重用；禁止两个孤立 CLI 结果拼接。所有 `applicable=true` 的 projection×dimension row 必须为 `KD_WIN`，所有 `applicable=false` 的 row 必须恰为 `N/A`，且矩阵无缺行、重复或其它 verdict，全部闭包通过后才可 released/close，否则保留真实 `not_released` 或 `blocked`。

## 禁止事项

不修改 raw、CompanyBrain、旧产物、main；不创建 successor task；不让旧 Task5 runtime 成为生产入口；不使用 `/tmp` 候选、旧 review、静态质量文件或平均分；不在五项全胜前宣布 released。


## ARCHIVE-NON-ACTIVE: 历史任务卡（非生效）

> 以下全部内容是历史执行记录，不再授权执行；尤其是其中的旧 `scripts/task5_reader_quality.py`、`_digest` 路径和旧 R1–R4 命令，不能覆盖当前 v4.2 的唯一 `digest → compiler → providers → publisher` 链。

- **Input**：`decision-log.md`、`spec.md`、`plan.md`；不再维护容易过期的头部文件 hash，设计材料身份以 WorkflowHub 当前 snapshot tree/material_id 和 mini-task review receipt 为准。
- **Template version**：`plan-task.v3`

> **合同归属**：`spec.md` 管产品行为和验收，`plan.md` 管 schema/bytes/file-boundary/gate 机器合同，本文件只执行任务卡和 STOP；重复字段是索引，不是第二套合同。发现冲突立即停卡，以 spec/plan 的当前 WorkflowHub snapshot/material 为准。

> **历史说明**：旧 P1–P4 和 `Repair mini-task execution cards v2` 只保留离线事实；它们不能授权本轮真实运行，也不能覆盖顶部 v4.2。当前真实运行前置只认顶部任务卡、当前 WorkflowHub binding、M401、M401-R 和 M402。

## 用户复核后的当前合同修正（2026-08-21）

本节优先于历史卡片中仍写 `source-direct-audit`、`full-source`、逐页 Audit 文件或 hash 路径的旧描述，不新增任务，只修正同一 Task5 的执行合同：

- 89 条 coverage 中 87 条普通非空来源各走一次 `source-digest` 尝试；只有逐源 route-support、Qwen typed compile 和 lineage 全部通过才生成 Reader。SND entry 由确定性 diagnosis projection 替换且必须有逐 Block `semantic_zero_match_certificate.v1` 才能成为 Reader，否则 Audit-only/not_released；known_empty 和显式 source-direct-audit 只进 Audit，失败不回退原文。
- Provider schema 使用 `config/task5-provider-semantic-output-v2.json`；`expected_title` 必须逐字回显，路径只用冻结 route title，title mismatch 不生成 Reader。source-digest、`task5-source-not-documented-contract-v2`、external-processing-policy 和 publication-layout authority 已冻结；漂移必须新版本并重跑 design review。
- 当前 publication layout authority=`config/task5-publication-layout-v2.json`，SHA=`26764a5892584bfedfb58c088d65d769f7dd555f836da53aa183b05257d0d986`；旧 v1 仅历史，不可被 implementation 或 M402 接受。
- 用户只看 Downloads 运行目录下的 `bundle/`；Reader 只有 `Home.md → products/<product>/<page-type>/<readable-title>.md`，Audit 集中为 `Audit.md` + `_audit/`。Home route table 是唯一公开轴索引，不再把 `staging/attempt/candidate-bundle` 当公开入口，也不生成 `modules/boundaries/knowledge` 或 hash 文件名；每个 Reader render unit 必须有公开 `audit/<public_projection_slug>/u-<ordinal>` 回查锚点。
- 上述合同 hash/实现 identity 未重新绑定前，任何真实 provider 调用都 STOP；五个维度没有全部严格 `KD_WIN` 时，最终状态只能 `not_released`。

## Repair file boundary v2

实现阶段的 ADD/OWN、MODIFY、READ-ONLY authority 和禁止新增路径，唯一以 `plan.md` 的「Repair file boundary v2」为准；tasks 不复制第二份 allowlist。实现前必须重算 plan appendix 中的 actual/canonical SHA，旧 v1 semantic-output 只作历史审计。M101 额外允许写 `repair-gates/attempts/<attempt_id>/baseline-preflight.json`；R1–R4/M401 证据只写不可变 attempts，promotion view 只引用 passed attempt，失败/取消/超预算不覆盖。四份设计材料在 design review terminal clean 后冻结，若需改动先重跑 design review。

### Gate receipt ownership and handoff

`mini_task.design` dispatch 前必须验证 authenticated `workflowhub-identity.v1`、parent refs/SHA、原始需求、三轮 Talk、snapshot/material、contract/semantic 和 writer。canonical evidence 必须符合 `workflowhub-authenticated-parent-projection.v1`，显式保存 parent result/attempt/receipt ref+SHA、make-decision snapshot/material/attestation、raw requirement ref+SHA、每轮 Talk `choices` 与 `selection_sha256`、`accepted_risk`/basis 和 writer attestation；同时绑定 parent full decision log、provider compact projection、raw requirement 和 Talk selection 的路径+SHA，不得把 compact SHA 冒充 full SHA。该 schema、禁止字段和绑定以 `config/task5-machine-evidence-contract-v1.json` 为唯一 authority。provider material_id 必须匹配 handoff；design clean 后才生成 implementation successor。

Implementation successor 只能由 authenticated WorkflowHub adapter 写入，不能由 Task5 CLI、caller 或测试自报。`quality/evidence/task5/workflowhub-implementation-handoff.json` 必须符合 `workflowhub-implementation-successor.v1`，并逐项绑定 design review 的 result/attempt/report ref+SHA、implementation review 的 result/attempt/report ref+SHA、M401 packet 和 M401-R receipt ref+SHA、当前 snapshot/material/worktree、WorkflowHub contract/semantic identity、Task5 runtime/semantic identity、writer attestation 及完整 finding dispositions；固定 `review_kind=mini_task.implementation`、`terminal_status=semantic`、`terminal_clean=true`、`all_findings_disposed=true`。该文件及其 parent refs、canonical `handoff_sha256` 属于 host-owned 文件边界，M402 只读复核，缺失、漂移、路径越界或任何 finding 未处置都在 raw/CompanyBrain/provider 前 `blocked/calls=0`。

M101 的 baseline preflight receipt `quality/evidence/task5/repair-gates/attempts/<attempt_id>/baseline-preflight.json` 是 ADD/OWN 的 attempt evidence；它只记录 frozen baseline ref/SHA、path-hash digest、patch scope、parent snapshot/material 和校验结果，不是新的产品输出，也不能覆盖固定 promotion view。

Authority rehash 顺序固定：M102/R1 先读取 `config/task5-runtime-authority-map-v1.json`，逐项重算其完整、排序后的 17 个 key（`external_processing_policy`、`machine_evidence`、`publication_layout`、`provider_handshake`、`provider_prompt`、`provider_semantic`、`reader_path_relation`、`reader_quality_provider`、`replay_store`、`root_cause_evidence`、`root_cause_inputs`、`semantic_frame`、`semantic_frame_field_closure`、`source_block_claim`、`source_digest`、`source_not_documented`、`source_sensitive_content_scan`）和 5 项排除项；同时校验 provider-config、handshake、prompt、machine-evidence、root-cause input/evidence、source-block-claim、source-not-documented、external-policy、publication-layout、calibration manifest/artifact。receipt 必须写 map 实际/规范 hash、逐项 path/schema/actual/canonical hash、`included_keys` 与 map key 集合的 exact equality、`excluded_paths` 与 map 集合的 exact equality、derived runtime contract hash；缺失、额外、重复、顺序重排、交叉引用或任何 hash mismatch 都在 provider 前 blocked。M252/R3 校验 quality/baseline/observation/source/slice authority；M301/R4 再校验 source/slice/layout/machine-evidence/policy；M401 finalize 重算全部 authority（含 run-result schema）并写 path/SHA、canonical SHA、纳入/排除和缺失/漂移原因。失败证据保留。

| receipt | 生成卡 | 生成时机 | 下一卡校验 |
| --- | --- | --- | --- |
| `R1.json` | M102 | 每次调用先写 `attempts/<attempt_id>/`；通过 attempt 后才更新 promotion view，并校验 `inverse/R1.patch` | M202 首个测试前 |
| `R2.json` | M202 | typed compiler、lineage 和 raw-fallback gate 的 attempt 完成后，只有通过 attempt 才 promotion | M252 首个测试前 |
| `R3.json` | M252→M253 | preflight/final event 均保留在 append-only attempt/event history；通过 attempt 后才 promotion | M301 首个测试前 |
| `R4.json` | M302 | runtime slice/full、Downloads、source closure 和 status/exit gate 的通过 attempt 才 promotion | M401 打包前 |

RED 只产生独立的 test receipt，不产生 gate attempt：路径为 `quality/evidence/task5/repair-gates/red-tests/attempts/<attempt_id>/<gate>.json`，schema=`task5-red-test-receipt.v1`，状态为 `expected_failed`，绑定命令、预期/实际退出码、测试结果 hash、当前 snapshot/material 和 `observed_provider_calls=0`。`expected_failed` 不是 `failed`，不写 `R*.json` promotion view，也不阻断 GREEN；对应 GREEN 卡必须显式消费并校验 `red_test_ref+sha256`，证明 RED 负例确实先失败。M101 的 `baseline-preflight.json` 是独立的无 provider bootstrap receipt，不能由 M101 RED receipt 代替。只有 GREEN 的 `task5-repair-gate-attempt.v1` 才使用 `status=passed|failed`、才进入 R1–R4 promotion；GREEN 的 failed attempt 保留并阻断下一卡。固定 `R*.json` 只作 append-only promotion/index view，记录 latest/promoted/attempt refs；下一卡检查 latest=promoted、status、snapshot chain、path hashes、patch、inverse 和 test receipt。R3 `R3-events.jsonl` 按 `task5-repair-gate-event.v1` append-only：记录 attempt/event index、全局 sequence、input snapshot/material/hashes、8 个固定 projection keys、previous/event digest；event hash 排除自身，按 plan canonical JSON+LF，exclusive lock+fsync 分配 sequence，失败事件不删改，receipt 记录 event_count/last digest/log hash。

### Test receipt and inverse patch contracts

R3 event、gate attempt、test receipt 和 inverse patch 都按 `plan.md` 的 canonical JSON、append-only、锁、snapshot/material、promotion 与 `after → before` 回滚合同执行；失败 attempt 只能保留，不能 promotion。M401 必须复 hash R1–R4 的通过 attempt、测试和 inverse；M401 packet 缺任一前置绑定即 STOP。M401-R 是下游消费者，不是 M401 packet 的输入。

`task5-m401-evidence-packet.v1` 与 plan 使用同一 canonical bytes；顶层 `canonical_sha256` 排除自身。packet 必须绑定 provider semantic schema、CompanyBrain host snapshot ref/tree digest/`pre_m402_readiness`、R1–R4 promotion refs、当前 snapshot/material、AC trace、receipt hash 和 finding dispositions；它不得包含尚未生成的 M401-R receipt/ref/hash。M401 snapshot 只证明前置，M402 必须重新生成 actual-run snapshot。缺字段、hash/snapshot 漂移或外部改写即 STOP。
- M401 的 focused/full receipt 使用独立 `task5-m401-test-receipt.v1`：`receipt_kind` 只能是 `focused|full-regression`，attempt 文件必须有 `commands[]`、`exit_code`、`status`、`test_count`、stdout/stderr/canonical result SHA、`snapshot_tree` 和 `material_id`；canonical bytes 仍为 UTF-8、递归排序、无空格 JSON + LF，整文件 SHA 由 M401 packet 引用。固定 `m401-receipts/M401-focused-test-receipt.json` 与 `M401-full-regression-receipt.json` 使用 `task5-m401-test-promotion.v1`，只记录 promoted attempt/ref/hash、attempt history 和 gate-local snapshot/material，不得冒充完整 receipt。focused/full 任一 latest 不等于 promoted、receipt hash/snapshot/material 漂移或命令/计数缺失，M401 立即 STOP。
- 每个 `inverse/R*.patch` 都是对应 gate 的完整 unified diff，只能触及该 gate 的 `changed_paths`，由该 gate 生成卡在写 gate receipt 前生成；gate receipt 记录 `inverse_patch_ref`、`inverse_patch_sha256`、`patch_format=unified-diff` 和 `inverse_base_after_snapshot`。下一 gate 和 M401 用 `sha256`、路径集合和 `git apply --check`（针对 after snapshot 的临时副本）验证，缺文件、hash 漂移、跨 gate 路径或无法反向应用立即 STOP；不能用文字里的“可回滚”代替 patch 文件。

上述固定 test/inverse 路径是通过 attempt 的 promotion view；每次 attempt 的原始 test receipt 与 inverse patch 必须先写入 `repair-gates/attempts/<attempt_id>/tests/` 和 `repair-gates/attempts/<attempt_id>/inverse/`。失败 attempt 不得写入或覆盖固定 promotion view，重跑只能创建新的 `attempt_id`；通过后固定 view 可以原子更新，但必须保留 `attempt_refs`、旧 attempt 文件和旧失败摘要，且 `test_receipt_ref`/`inverse_patch_ref` 指向本次被 promotion 的通过 attempt。

## Historical P1–P4 implementation record (compressed)

P1–P4 只作为同一 Task5 的离线历史事实：已有 89-path inventory、Block/Claim、路由/五类投影、CompanyBrain 对照、五维 evaluator、slice→full 和原子发布证据，分别保留在 `quality/evidence/task5/P1–P4/`。它们不授权本轮 Qwen/Jina 运行；本轮只复用代码边界，仍由 decision-log/spec/plan 与下方 repair cards 重新证明 provider identity、semantic lineage、source closure、评分和真实 89 条 gate。raw、CompanyBrain、正式 digest、Task4 和旧产物不改、不覆盖。

## Repair mini-task execution cards v2

以下是本轮 provider-backed 修复的新增任务卡。旧 T101–T999 的完成记录是历史快照，不覆盖本节的执行状态；本节没有任务在实现前预填完成。

### D0-H / D0-R — 历史根因回放与当前 raw-only 候选预检分离

- **owner/status**：R1/M101；D0-H=`blocked_until_inputs_restored`，D0-R=`ready_after_current_raw_preflight`。两张门发生在 `mini_task.design`/provider 前，但不是同一输入，也不能互相替代。
- **command**：`uv run --frozen python scripts/task5_reader_quality.py root-cause-preflight --root-cause-input-manifest config/task5-root-cause-input-manifest-v1.json --root-cause-contract config/task5-root-cause-evidence-v2.json --raw-input '/Users/Hugh/Downloads/confluence 原始数据' --companybrain '/Users/Hugh/Hugh/Knowledge/CompanyBrain' --evidence-root quality/evidence/task5 --network-policy deny`。
- **D0-H order/oracle**：认证当前 snapshot/material；校验五个 `RC-*` 输入；写不可变 `root-cause-evidence` attempt。全程 `provider_calls=embedding_calls=0`。每条 blocking/major observation 必须绑定输入 ref/SHA、相对 locator、CompanyBrain `case × projection × dimension`、合同缺口和 repair mapping。V50 或 baseline 漂移只阻断历史 promotion，不得换用其他候选。
- **D0-R order/oracle**：只读取当前 raw 89 条、CompanyBrain 只读快照和当前实现/运行合同，生成新的 source-scope ledger（source identity、Block/Claim closure、空源/重复源状态、输入 digest、raw-only candidate id）；全程 `provider_calls=embedding_calls=0`。它不要求原文先显式写出五轴语义，五轴和 page type 由 Qwen typed output 生成，再由 post-provider verifier 逐字段回绑。D0-R 通过后才允许普通 present source 逐条尝试 Qwen；route support 少于 87/87 时保留失败证据，最终只能 `not_released`。
- **current blocker**：D0-H 当前只能写 `blocked` attempt；D0-R 不得读取或替换 V50，也不得把 D0-R 结果写进历史 root-cause promotion。两者都不能靠文件名、目录、整篇原文或模型猜测补齐 Reader。

### Fixed gate command contract v2

所有 gate 从仓库根目录执行。以下 `GATE_BASE`、`BASELINE_BOOTSTRAP` 和 `PROMOTE(gate,dir)` 是先展开的固定命令宏，不是 caller 可改写的环境变量；attempt id 由 authenticated runner 生成。缺子命令、参数或 receipt 字段即 blocked。所有 gate 使用 `--provider-mode fake --network-policy deny`，不得联网；RED 命令写入 `repair-gates/red-tests/attempts/<attempt_id>/<gate>.json`，GREEN 命令才写入 `repair-gates/attempts/<attempt_id>/`。固定退出码：`0=可 promotion`、`1=本地测试/质量失败`、`2=identity/config/provider blocked/unavailable`、`3=runner failure`、`4=cancelled`；RED 的预期失败另记录 `expected_failed`，不按 gate failed 处理。

`GATE_BASE = uv run --frozen python scripts/task5_reader_quality.py gate --workflowhub-handoff quality/evidence/task5/workflowhub-design-preflight-handoff.json --evidence-root quality/evidence/task5 --provider-mode fake --network-policy deny`。
`AUTHORITY_ARGS = GENERATED_RUNTIME_AUTHORITY_ARGS(config/task5-runtime-authority-map-v1.json)`：这是 runner 内部的不可改写命令宏，不是 caller 环境变量；它按 map 的当前字节生成 17 项 included authority 的 `--authority <key> --path <path> --schema <schema> --actual-sha <actual_sha256> --canonical-sha <canonical_sha256>` 参数和 5 项 `--excluded-path` 参数，并同时带 map actual=`78bea9d08cb1b4e181770d7b8a182ff424512f2fbddd7e40d37f6e9ed1cd2f5b`、map canonical=`0c3f2f0e802479374b4db65b748b6d5034e9a19ade80d60f98423cbbddafc4de`、derived runtime=`ffab8d33b10a766d4c602bcb1cacd5f444f74d34992653df767e495c6dee260b`。任何手写 `--provider-contract/--machine-evidence/...` authority argv、缺项、额外项或与该生成结果不等价都立即 blocked；只有不在 map 的 gate-specific inputs（baseline identity、quality/baseline/observation/slice/source manifest、quality-result/source-direct、calibration）才能单独列出，并同样传 path/schema/actual/canonical SHA。
固定执行和 promotion：

`D0_HISTORICAL = GATE_BASE root-cause-preflight --root-cause-input-manifest config/task5-root-cause-input-manifest-v1.json --root-cause-contract config/task5-root-cause-evidence-v2.json --raw-input '/Users/Hugh/Downloads/confluence 原始数据' --companybrain '/Users/Hugh/Hugh/Knowledge/CompanyBrain' --evidence-root quality/evidence/task5 --network-policy deny`。它必须先于历史 root-cause promotion；失败写不可变 blocked attempt，calls=`0`，不写 promotion。`D0_RAW_ONLY = GATE_BASE raw-preflight --raw-input '/Users/Hugh/Downloads/confluence 原始数据' --companybrain '/Users/Hugh/Hugh/Knowledge/CompanyBrain' --evidence-root quality/evidence/task5 --network-policy deny`；它只生成当前 raw source-scope/input identity，成功后才允许当前候选进入 provider gate，不生成历史 root-cause 结论。
- `BASELINE_BOOTSTRAP = GATE_BASE bootstrap-baseline --baseline quality/evidence/task5-repair-baseline-v2.json --root-cause-input-manifest config/task5-root-cause-input-manifest-v1.json --root-cause-contract config/task5-root-cause-evidence-v2.json --root-cause-ref quality/evidence/task5/root-cause/root-cause-evidence.json --root-cause-sha <promoted-root-cause-sha256> --baseline-preflight-out quality/evidence/task5/repair-gates/attempts/<m101-bootstrap-attempt-id>/baseline-preflight.json`。它只消费 D0 已 promotion 的 root-cause evidence；该 evidence 必须含 89 条 source-scope ledger 和其 digest。历史根因输入完整性若仍是 release 前置则继续校验，但 post-provider 的 87/87 route closure 不在 D0 预先伪造；不得在 M101 内第一次 replay 根因。
- M101 RED：`GATE_BASE --gate M101 --test-kind red --baseline quality/evidence/task5-repair-baseline-v2.json --baseline-preflight quality/evidence/task5/repair-gates/attempts/<m101-bootstrap-attempt-id>/baseline-preflight.json --root-cause-ref quality/evidence/task5/root-cause/root-cause-evidence.json --root-cause-sha <promoted-root-cause-sha256>`；runner 必须校验 D0/baseline-preflight 与 root-cause evidence 的 ref/SHA、同一 snapshot/material、`status=passed` 和 89 条 source-scope closure；缺失、漂移或不匹配时 calls=`0` 且不得写 RED receipt。RED=`1`，identity/preflight=`2`，calls=`0`；它只写 `red-tests/.../M101.json`。
- M102 GREEN：`GATE_BASE --gate M102 --red-test-ref quality/evidence/task5/repair-gates/red-tests/attempts/<m101-red-attempt-id>/M101.json --baseline-receipt quality/evidence/task5/repair-gates/attempts/<m101-bootstrap-attempt-id>/baseline-preflight.json --baseline-identity-from-root-cause-input RC-CURRENT-BASELINE --root-cause-ref quality/evidence/task5/root-cause/root-cause-evidence.json --root-cause-sha <promoted-root-cause-sha256> AUTHORITY_ARGS --calibration-manifest config/task5-calibration-manifest-v1.json --calibration-manifest-sha256 b18610b2a3ffe0dccb854509cd9b826aace0fe18b18af836f6679aebefa8f510 --calibration-artifact evidence/phase4/calibration-artifact.json --calibration-artifact-sha256 c31b1f8c78a889dff4cdbbab0fb695871c513844b5c8392d52dbbd8ad33e4c06`；exit `0` 后执行 `PROMOTE(M102,<m102-attempt-id>)`。`AUTHORITY_ARGS` 展开后 R1 fake receipt 必须覆盖 handshake v3 的三类 LLM route，并记录 17-key exact set、每项 path/schema/actual/canonical SHA、calibration endpoint/model/dimension；缺任一 route、把 source-direct-audit 当 Reader route 或 baseline identity 与 RC-CURRENT-BASELINE 不等都是 blocked/calls=0。
- M201 RED：`GATE_BASE --gate M201 --test-kind red --semantic-contract config/task5-provider-semantic-output-v2.json --source-contract config/task5-source-digest-contract-v2.json --semantic-frame config/task5-semantic-frame-v1.json`；typed/raw-fallback=`1`，identity drift=`2`；只写 `red-tests/.../M201.json`。
- M202 GREEN：`GATE_BASE --gate M202 --red-test-ref quality/evidence/task5/repair-gates/red-tests/attempts/<m201-red-attempt-id>/M201.json --r1-attempt quality/evidence/task5/repair-gates/R1.json --baseline-receipt quality/evidence/task5/repair-gates/attempts/<m101-bootstrap-attempt-id>/baseline-preflight.json --baseline-identity-from-root-cause-input RC-CURRENT-BASELINE AUTHORITY_ARGS`；exit `0` 后 `PROMOTE(M202,<m202-attempt-id>)`。R2 attempt/test receipt 必须写 map-generated authority argv、baseline identity、parser/path/semantic-closure contract ref、actual SHA、canonical SHA 和派生 identity，并让 request/response/replay identity 三方相等；任一 authority、baseline 或逐字段 closure 缺失/漂移时 calls=`0`。
- M251 RED：`GATE_BASE --gate M251 --test-kind red --quality-config config/task5-quality-cases-v2.json --baseline-config config/task5-companybrain-baseline-v2.json --observation-config config/task5-companybrain-observation-v2.json`；静态答案/verdict=`1`，authority drift=`2`；只写 `red-tests/.../M251.json`。
- M252 GREEN：命令参数由 `AUTHORITY_ARGS = GENERATED_RUNTIME_AUTHORITY_ARGS(...)` 展开；必须传入当前 R2、baseline、quality-result、source-direct、slice、manifest、embedding-handshake、calibration 的 path/SHA，完成后 `PROMOTE(M252,<m252-attempt-id>)`。详细参数见本卡的 M252 authority receipt contract。
  ```text
  GATE_BASE --gate M252 \
    --red-test-ref quality/evidence/task5/repair-gates/red-tests/attempts/<m251-red-attempt-id>/M251.json \
    --r2-attempt quality/evidence/task5/repair-gates/R2.json \
    --baseline-receipt quality/evidence/task5/repair-gates/attempts/<m101-bootstrap-attempt-id>/baseline-preflight.json \
    --baseline-identity-from-root-cause-input RC-CURRENT-BASELINE \
    --quality-config config/task5-quality-cases-v2.json \
    --quality-result-config config/task5-quality-result-v3.json \
    --baseline-config config/task5-companybrain-baseline-v2.json \
    --observation-config config/task5-companybrain-observation-v2.json \
    --source-direct-contract config/task5-source-direct-contract-v1.json \
    --slice-config config/task5-slice-cases-v1.json \
    --source-manifest config/task5-source-page-manifest-v2.json \
    --embedding-contract-handshake config/task5-provider-contract-handshake-v3.json \
    --calibration-manifest config/task5-calibration-manifest-v1.json \
    --calibration-artifact evidence/phase4/calibration-artifact.json \
    AUTHORITY_ARGS
  ```
  所有 gate-specific 文件也必须在 receipt 中记录 actual/canonical SHA；缺项、漂移或手写 authority argv 都是 `blocked/calls=0`。
- M253-R RED：`GATE_BASE --gate M253-R --test-kind red --r2-attempt quality/evidence/task5/repair-gates/R2.json --quality-config config/task5-quality-cases-v2.json --baseline-config config/task5-companybrain-baseline-v2.json --observation-config config/task5-companybrain-observation-v2.json --slice-config config/task5-slice-cases-v1.json --source-manifest config/task5-source-page-manifest-v2.json`；新增关系负例=`1`；只写 `red-tests/.../M253-R.json`。
- M253 GREEN：`GATE_BASE --gate M253 --red-test-ref quality/evidence/task5/repair-gates/red-tests/attempts/<m253r-red-attempt-id>/M253-R.json --r2-attempt quality/evidence/task5/repair-gates/R2.json --r3-red-attempt quality/evidence/task5/repair-gates/red-tests/attempts/<m253r-red-attempt-id>/M253-R.json --quality-config config/task5-quality-cases-v2.json --baseline-config config/task5-companybrain-baseline-v2.json --observation-config config/task5-companybrain-observation-v2.json --slice-config config/task5-slice-cases-v1.json --source-manifest config/task5-source-page-manifest-v2.json`；exit `0` 后 `PROMOTE(M253,<m253-attempt-id>)`。
- M301 RED：`GATE_BASE --gate M301 --test-kind red --r2-attempt quality/evidence/task5/repair-gates/R2.json --r3-attempt quality/evidence/task5/repair-gates/R3.json --slice-config config/task5-slice-cases-v1.json --source-manifest config/task5-source-page-manifest-v2.json --publication-layout config/task5-publication-layout-v2.json`；缺 Downloads/89/route-Audit=`1|2`；只写 `red-tests/.../M301.json`。
- M302 GREEN：`GATE_BASE --gate M302 --red-test-ref quality/evidence/task5/repair-gates/red-tests/attempts/<m301-red-attempt-id>/M301.json --r2-attempt quality/evidence/task5/repair-gates/R2.json --r3-attempt quality/evidence/task5/repair-gates/R3.json --slice-config config/task5-slice-cases-v1.json --source-manifest config/task5-source-page-manifest-v2.json --publication-layout config/task5-publication-layout-v2.json`；exit `0` 后 `PROMOTE(M302,<m302-attempt-id>)`。

`PROMOTE(gate,id) = uv run --frozen python scripts/task5_reader_quality.py promote --gate gate --attempt-ref quality/evidence/task5/repair-gates/attempts/id/R*.json --tests-ref quality/evidence/task5/repair-gates/attempts/id/tests/R*.json --inverse-ref quality/evidence/task5/repair-gates/attempts/id/inverse/R*.patch`；`R*` 按 gate 映射为 R1/R2/R3/R4。只接受本命令生成且匹配当前 after snapshot/material/authority hashes 的 receipt；旧 receipt、手填摘要、transport 完成或绿色 pytest 不得 promotion。

### M101 — RED: provider config, identity and budget

- **Phase**：R1 provider identity/config and preflight
- **status**：blocked until D0 and design terminal clean
- **depends_on**：D0 root-cause/route-support promotion; design terminal clean
- **goal**：证明当前代码不能满足用户配置优先级、批准 endpoint/model、secret redaction、calibration 和调用预算；先写会失败的验收。
- **inputs**：D-004/D-007/D-008、ADR-0012、`llm.py`、`embedding.py`、用户 config boundary。
- **files**：`tests/acceptance/test_task5_provider.py`、`src/knowledge_digest/task5_provider_config.py`、`scripts/task5_reader_quality.py`（测试先于实现；R1 同时 owns baseline-preflight/gate CLI，R4 只调用既定接口）。
- **first action**：只消费 D0 已 promotion 的 root-cause evidence；验证其五项输入 ref/SHA、89 行 source-scope ledger 和当前 snapshot/material。然后无网络 `validate_baseline_contract()` 读取 `RC-CURRENT-BASELINE`，校验 baseline actual/canonical SHA、ADD/MODIFY before hash、R1–R4 owner；最后 `write_baseline_preflight()` 绑定 D0 refs 和 baseline。M101 不再第一次调用 `replay_root_cause()`，不替换漂移输入，不使用研究文档或其他候选产物。post-provider route support 不在 M101 预先伪造，改由 R2/R4 对实际 Qwen 输出逐源闭合；任一 D0/baseline 缺失、漂移或比较不可建立立即 STOP，calls=0；receipt 为 `task5-baseline-preflight.v1` canonical JSON，并由 M102/R1–R4 复核同一 ref/SHA、snapshot/material。任何 DNS、TLS、socket/connect 或 read-timeout 失败都必须由 `Task5ProviderTransport.v1` 先写 create-only 无响应 attempt receipt；缺该 receipt 仍是 blocked/calls=0。
- **authenticated identity**：M101 只能接收 WorkflowHub adapter 通过 TaskKernel/Workspace 认证生成的 `workflowhub-identity.v1` handoff；不得信任 caller 自报的 `snapshot_tree`/`material_id` argv/env。handoff 必须带 parent canonical make-decision result/attempt ref+SHA、attempt_id、原始需求与三轮 Talk attestation，以及当前 snapshot/material revision/material_id；handoff 缺失、attestation/hash/task/worktree 不匹配，或当前重算 snapshot/material revision/material_id 不一致，都在 receipt/RED/provider 前 blocked；baseline-preflight 和后续 R1–R4/M401/M402 必须继承同一 identity ref/SHA。
- **tests**：缺 config/key、明文 key、未知字段、endpoint/model 漂移、calibration mismatch、budget overflow、explicit CLI precedence、config hash/redaction/idempotency；`llm.retry_attempts`/`embedding.retry_attempts` 非零拒绝，DNS/TLS/connect/read-timeout/429/5xx/坏 JSON/部分向量都只能有一次 attempt，网络无响应必须有失败 receipt 且不能伪造 HTTP response。预算测试必须从冻结 fixture 重算 `115` 次 LLM、`17` 次 embedding、`132` 次 planned calls，并覆盖 SND replacement、额外 probe、隐式 retry、跨 mode 复用 receipt 三个 overrun/identity 负例；根因 evidence 缺输入、错误旧产物 hash、只写结论无 locator、缺 CompanyBrain case/projection/dimension 配对差异、缺合同缺口/修复映射或 promotion 漂移必须在首个 network call 前阻断；还必须覆盖缺失/过期/错 hash 的 baseline-preflight 或 root-cause ref，断言 calls=`0`、不写 gate receipt；不能只断言一个写死的总数。
- **oracle**：每个失败在首个 network call 前暴露；测试不得真的发送 provider 请求。
- **STOP**：若测试无法观察“首个请求前阻断”，不能进入 M102。

### M102 — GREEN: provider config and preflight

- **Phase**：R1
- **status**：pending
- **depends_on**：M101；design terminal clean
- **goal**：实现显式 CLI > `~/.config/knowledge-digest/config.json` 的配置加载和 provider preflight；v2 直接读取 `api_key`，`api_key_env` 仅作兼容回退。
- **files**：`src/knowledge_digest/task5_provider_config.py`、`config/task5-provider.example.json`、`tests/acceptance/test_task5_provider.py`、`scripts/task5_reader_quality.py`。
**read_only_inputs**：`config/task5-runtime-authority-map-v1.json`（actual=`78bea9d08cb1b4e181770d7b8a182ff424512f2fbddd7e40d37f6e9ed1cd2f5b`、canonical=`0c3f2f0e802479374b4db65b748b6d5034e9a19ade80d60f98423cbbddafc4de`）、`config/task5-machine-evidence-contract-v1.json`（actual=`df96f45ab66aa58c02867834ea1d3f01051fb750a401ce2c71c46d52d0eb01ae`、canonical=`2afc28ccabd930d77ddf9278f546b1a81b3d72e6df66b129d00b70406685f882`）、`config/task5-source-block-claim-contract-v1.json`（actual=`02898de03f72ad2ccfe7998cff9b4c4362cde95e71ed3aa0cdd35a5a00ce9b71`、canonical=`4baa67603f01aa1e1f114b08cf352a03d51d67035071feb3894f499af6983639`）、`config/task5-publication-layout-v2.json`（actual=`26764a5892584bfedfb58c088d65d769f7dd555f836da53aa183b05257d0d986`、canonical=`f8d75e9069d4dee610f2cbc61e1172eabd1188a37fe4b52d8e67ff1394614e72`）、`config/task5-root-cause-input-manifest-v1.json`（actual=`2909de6d…`、canonical=`52e86dd5…`）、`config/task5-root-cause-evidence-v2.json`（actual=`6b75d70ed2db0820aeea99e82a86ae241212d6e51246e3b8f449523faa580985`、canonical=`cd4751b98da5f743faf4a8a81624ac335c219e6df803c3a44dd7e962b3d5e971`）、`config/task5-provider-config-v2.json`（SHA-256=`c6923528c565b9cbfebca28cecd58cf84be218ecac6d45f625307cd5572ee5b3`，canonical=`e28334be53c1e2c85a720057b167bfa3f3ee9c37ae19ae94e527a1a8b5430a33`）、`config/task5-reader-quality-provider-v2.json`（actual=`8617fe9aa4070ff548ca168c4f86a044b36ad0c6f3c4bc7248b18f315d840923`、canonical=`f239ad0b24a15cae22e7f61172e1e2b537324ec88e902efe7d5e727e1e4c1ead`）、`config/task5-semantic-frame-field-closure-v1.json`（actual=`d2a560e7b06d9c5edaf031de0565abd4d86a9fc77613e26bc1b954212c6acc20`、canonical=`a3c7bd6b7c4757f9a4d38599768889b85fc66dbab4d8f5ed574dd9ba74d24262`）、`config/task5-provider-contract-handshake-v3.json`（actual=`c15c0612…`、canonical=`fc821c35…`）、`config/task5-reader-path-relation-contract-v1.json`（actual=`c3f12166…`、canonical=`16de1b3c…`）、`config/task5-calibration-manifest-v1.json`、`evidence/phase4/calibration-artifact.json`、`config/task5-source-sensitive-content-scan-v1.json`（actual=`1253ab1e1e31ae7d737183d8ac8ffb85d9e5f83a2bc76b534195bbc4339d53d5`、canonical=`5836aa4631c29d5d6117eed42c47f886e1edfe36df3c03ee97bbfcc2743dff2e`）和 `config/task5-replay-store-v1.json`（SHA-256=`56e2198d5bb1d16c0c99d61fb3abd0e5a728619622d1d2fe8ac0409a25bd6457`）；M102 只读取并 hash 校验它们，不能修改 provider-required authority。
- **contract**：批准的 LLM model 为 `qwen3.6|qwen3.8` + `https://dashscope.in.whatspos.cn/v1`，实际 model 必须通过 live capability check 且原样进入 receipt；当前用户 endpoint 只提供 `qwen3.8`；jina-embeddings + `https://llm.paxszapp.com/v1`；本地 `config.json.api_key` 优先，`api_key_env` 仅兼容回退，receipt 不记录 key；config/prompt/schema/input identity；prompt contract=`config/task5-provider-prompt-contract-v1.json`（actual=`1e8888cb…`、canonical=`791ac7e1…`，三类 route），semantic-frame=`config/task5-semantic-frame-v1.json`（SHA-256=`e864fd5f976a5641ffda5db662eceb2ce85687f5fabf250dc7e337b73f264ae6`）；approved calibration SHA-256=`c31b1f8c78a889dff4cdbbab0fb695871c513844b5c8392d52dbbd8ad33e4c06`；`llm.retry_attempts=0`、`embedding.retry_attempts=0`、每个逻辑 call 只能有一个 HTTP attempt；receipt 记录 `http_attempt_count`，按实际 attempt 计 `observed_calls`；客户端无法证明无 retry 或发生第二次 attempt 时在下一次请求前 blocked/overrun；预算超限立即停止并写 `overrun` blocked/not_released receipt，不重试、不伪装通过；状态到退出码固定为 `released=0`、`not_released=1`、`blocked=2`、`unavailable=2`、`failed=3`、`cancelled=4`。
- **oracle**：成功 config 不含 key；漂移、缺 key、预算不足、运行时 overrun 和 calibration mismatch 明确 `blocked`，不自动回退；fake LLM handshake 必须覆盖 v3 的 `source-digest`、`quality-reader`、`source-direct-audit` 三类 route，且 schema hash、request identity、response/normalized output hash 和 no-network 断言必须成功，否则 R1 不得 promotion；R1 还必须在 embedding handshake 前校验 calibration manifest/artifact identity，并把 manifest ref/SHA 写进 handshake 和 receipt。
- **source payload gate**：M102/R1 在每个 selected Block、embedding route descriptor 和 embedding query 的序列化前，执行 `config/task5-source-sensitive-content-scan-v1.json` 的完整 raw/NFKC 规则；所有 text fields（含 title/question/page_type/provider-visible URI/query）逐字段扫描，identity fields 只有在 source identity 校验后才可序列化。唯一的 `Task5ProviderTransport.call_once` 在组装最终 LLM JSON wire payload 后、socket 前，必须递归枚举最终 payload 的所有 text-bearing JSON pointer（至少 `messages[*].content`、title/question/page_type、provider-visible URI、claim/route metadata、semantic frame），对每个字段重新扫描并把 pointer、source/block/claim ref、scanner actual/canonical SHA、payload digest 和 match digest 写入同一 request receipt；只扫描 Block、模板或中间 prompt 不能替代最终 payload scan。字段缺失、未扫描、payload 漂移或 scanner contract 缺失/漂移都必须 `SOURCE_POLICY_UNVERIFIED`、calls=`0`，不得建立 socket。Embedding descriptor 还必须通过 `task5-reader-path-relation.v1` 的字段级 support/closure verifier；title、question 或 page_type 缺少当前 Block/Claim 或 authenticated CompanyBrain observation 支撑时，route=`unknown`、embedding calls=`0`、不得写 KD_WIN。credential/PII/high-entropy 命中写 source/block/locator/content hash/rule/category/match digest，calls=0、`SOURCE_SENSITIVE_CONTENT`、blocked，不脱敏、不写 raw match。
- **selected-source atomic failure test**：`quality-reader` 是不可拆分的 selected-source projection。任一选中来源命中 `SOURCE_SENSITIVE_CONTENT`，或任一字段出现漏扫、scanner/payload 漂移、selected closure 不完整，必须在 socket 前让整个 projection `blocked/calls=0`；测试必须断言不删 source、不改 closure、不重算 request identity、不重试、不发送剩余来源的 partial payload，且该 projection 不写 Reader/quality/publication。只有不相关 route/projection 可继续；source-local 的“其他来源继续”不得被实现成同一 projection 的部分成功。
- **source-digest route verifier**：D0/R2 先按 `source-scope-producer.v1` 从当前 raw bytes 生成 89 条 source identity、Block/Claim closure 和 source-scope receipt，provider calls 固定为 `0`；它只确认来源可安全进入一次单源 Qwen 请求，不因为原文没有显式 question/page type/五轴标签而丢掉请求。Qwen 返回 typed page type、title、五轴和 Claim refs 后，再由 `source-digest-route-verifier.v1` 逐字段绑定当前 Claim/frame/locator、source/block/claim hash、单源 closure 和 `support_sha256`。原始目录顶层只能作为结构性 product route，文件名只能作为显示标题候选，不能证明 object/scene/boundary 或答案事实。字段无支持、主意图多解、关系不闭合、stale locator 或 output/ledger 漂移时，当前来源 route=`unknown`、只写 Audit、Reader/quality/publication 不生成；但不能把 D0 没有显式 metadata 当成 Qwen calls=`0`。87 个普通来源必须逐条尝试，post-provider route closure 少于 87/87 时最终只能 `not_released`。
- **quality-result artifact**：R3 evaluator 唯一写 candidate attempt `quality/evidence/task5/actual-run/attempts/<attempt_id>/quality-result.json`，状态为 `candidate/not_released`、绑定 `candidate_tree_sha256` 且 `published_tree_sha256=null`。candidate pre-publish surface QA 通过后，只有同一 R3 owner 执行同盘原子 rename；rename 后必须新建不可变 `quality-result-finalize` attempt，重算最终 directory manifest/tree 并确认 candidate/published 一致，才 promotion 到 `quality/evidence/task5/actual-run/quality-result.json`，写最终 `publication_status`/`published_tree_sha256`。rename failure、rollback、finalize failure 或 post-rename drift 只保留失败 attempt，不能 promotion、不能 released。测试必须覆盖成功 rename+finalize 的 tree equality、rename failure、rollback、finalize failure 和 post-rename drift；artifact 恰好有六 case×八 projection×五 dimension、每行绑定 Reader/Audit/route/RenderLedger/source-closure/path-replay/CompanyBrain refs+SHA，并绑定 candidate/final manifest 与 candidate/published tree；run-result、release predicate、post-rename surface QA 和最终 manifest 只能消费同一 promoted ref+SHA，缺/重/漂移即 `UNKNOWN/not_released`。
- **attempt status mapping**：gate attempt 的 `status` 只能是 `passed|failed`；`blocked`、`unavailable`、`cancelled`、`overrun` 只写在 `outcome`，并按运行合同映射进 `exit_code`，不能把这些运行原因当成通过或新建另一种 gate status。
- **receipt**：M102 只能消费已通过的 M101 baseline-preflight receipt，并将其 ref/SHA、promoted root-cause ref/SHA、baseline SHA、path-hash digest 和 parent snapshot/material 绑定到 R1 attempt；之后为本次调用分配 `attempt_id/attempt_seq`，无论通过或失败先写 `repair-gates/attempts/<attempt_id>/{R1.json,tests/R1.json,inverse/R1.patch}`；attempt receipt 写入 inverse patch hash、after snapshot、`inverse_patch_ref`、`outcome` 和 exit code，并包含 `runtime_authority_rehash`（map ref/actual SHA/canonical SHA、sorted 17-key `included_keys`、exact `excluded_paths`、每项 path/schema/actual/canonical SHA、derived runtime contract hash、missing/extra/mismatch 列表）以及 `llm_contract_handshake`（handshake schema ref/SHA、fake request identity、fake response/normalized output SHA、测试结果）。失败只更新 R1 index 的 latest history，不更新 `promoted_attempt_ref`、tests/R1 promotion view 或 inverse/R1.patch；通过才更新后三者。M202 的首个测试前必须校验 R1 index 的 latest/promoted ref、canonical attempt、baseline-preflight、root-cause ref/SHA 和完整 authority-rehash receipt 五件证据。

M102/M202/M252/M302 卡片中的“生成 R*.json、tests/R*.json、inverse/R*.patch”均按上面的 attempt/promotion 规则解释：失败先写 `repair-gates/attempts/<attempt_id>/`，通过后才更新固定 promotion view；固定 view 不是单次不可重跑的失败文件。

### M201 — RED: typed semantic compiler and no fallback

- **Phase**：R2 typed semantic compiler
- **status**：ready
- **depends_on**：design terminal clean
- **goal**：用 fake provider 固定 typed JSON、五轴、五类 page type、slot/Claim lineage 和 raw fallback 禁止规则。
- **files**：`tests/acceptance/test_task5_source_semantic.py`。
- **tests**：先校验 semantic=`630d7757…`、source-digest actual=`247fbc8…`/canonical=`5449076d…`、semantic-frame=`e864fd5f…` 和 source-direct contract hash；还必须覆盖 valid title、title mismatch/path rejection、malformed JSON、unknown field、invalid page type/axis、Claim ref 越界、missing slot、frame concrete field 缺 support span、unknown/not_applicable 空 span结构、required field unknown、逐字段 subject/predicate/object/order/condition/polarity 不等价、source-digest closure 外 Claim、quality-reader selected closure 内多源 Claim 的 owner/co-support/conflict 校验、bounded-lexical 仅诊断不能放行、raw/full-source copy、page-level rewrite、公开 source-digest/SND 的 ReaderTaskPath/入口回放/Reader-Audit 缺失与失败、provider failure 和 prompt 超限。必须把 source-scope producer、post-provider `source-digest-route-verifier.v1`、89 条 coverage partition（87 ordinary + 1 SND replacement + 1 known_empty/duplicate 规则）、`rewrite_guard` 的 whole-source/one-to-one/短来源负例列为独立测试用例；缺 source-scope ledger、support hash 或 rewrite receipt 的 source 不能生成 Reader；缺显式 metadata 但有可读 Claims 的 source 仍必须尝试 Qwen。
- **oracle**：provider 失败或 typed contract 失败时没有 Reader fallback；Audit reason 可定位。
- **STOP**：若测试不能证明 typed JSON、Claim ownership、slot/page-type refs、context overflow 和 provider failure 都不回退 raw Reader，不能进入 M202。

### M202 — GREEN: provider semantic adapter

- **Phase**：R2
- **status**：pending
- **depends_on**：M102、M201；design terminal clean
- **goal**：接入已有 LLM client，生成 typed JSON semantic compile ledger；不让 LLM 直接写 Markdown。
- **files**：`src/knowledge_digest/task5_provider.py`、`src/knowledge_digest/task5_semantic_model.py`、`tests/acceptance/test_task5_source_semantic.py`。
- **contract**：输入只来自 raw snapshot Block/Claim；先按 `config/task5-source-block-claim-contract-v1.json` 生成完整、可回放的 Block/Claim ledger，再由 Qwen v2 typed JSON 经 semantic-frame、`config/task5-semantic-frame-field-closure-v1.json` 的逐字段闭合算法、`config/task5-reader-path-relation-contract-v1.json` 的 relation-parser-v1/ReaderTaskPath、locator/scope/关系/page 校验后渲染。R2 必须在编译前读取并 hash 校验 path/relation/semantic-closure authority，R2 receipt、每个 request/response/replay identity 和 PageProjection 都必须写同一 `reader_path_relation` actual/canonical/derived hash，并同时绑定 semantic-frame、semantic-frame-field-closure、source-block-claim、provider-semantic、source-digest 与 runtime contract 的 actual/canonical/derived hash；route kind、success/negative case、Reader eligibility 和 path-replay 结果必须逐项回写，任何漂移、缺失或漏传即 blocked。source-digest/SND Reader 还要过 route replay、Reader/Audit、closure、lineage 和 rewrite gate；失败 Audit-only/not_released、无 raw fallback、不进五维胜出矩阵。SND v2 只有逐 Block zero-match certificate 才可 Reader；source-direct-audit 固定 Audit-only。两份 semantic ledger 固定路径、canonical JSON+LF、单写者/create-only replay；跨运行只接受绑定真实 receipt/HTTP attempt/run/compiler/parser identity 的 exact replay。
- **oracle**：provider identity/call sequence/output hash/失败 reason/frame/parser snapshot 可回查；任意失败 source 不生成 `full-source` Reader；同 identity 重跑的 response、Reader/path/hash 必须一致，只有真实成功 receipt 的 exact replay 才能省 provider call。
- **receipt**：M202 首个测试前校验 R1 index 与其 canonical passed attempt；完成 typed compiler、lineage 和 no-fallback gate 后先写本次 R2 attempt 的 `R2.json`、`tests/R2.json` 和 `inverse/R2.patch`，再按通过条件更新 R2 promotion view，并绑定该 gate after snapshot/material_id；R2 不修改 `task5_runtime.py`，runtime wiring 由 M302/R4 负责；M252 首个测试前复核 R2 latest/promoted ref 和三件 canonical 证据。

### M251 — RED: evidence-only baseline/cases and real five-dimensional evaluator

- **Phase**：R3 actual quality evaluator
- **status**：ready
- **depends_on**：design terminal clean
- **goal**：先让测试证明静态 baseline、预写答案、只查页存在和摘要覆盖无法构成质量通过；v2 fixture 是唯一可执行 authority，旧 §10.3 描述和 v1 fixture 只能历史回归，不能被 evaluator 消费。
- **files**：`tests/acceptance/test_task5_quality_gate.py`。
- **read_only_inputs**：`config/task5-quality-cases-v2.json`、`config/task5-companybrain-baseline-v2.json`、`config/task5-source-block-claim-contract-v1.json`；M251 只能读取并 hash 校验 frozen authority，不能修改、生成或把 fixture 当作实现产物。v2 实际 `source_paths/projections` 计数以文件字节为准：POS 6/1、CON 2/1、OPR 2/2、DIA 7/1、EXP 5/1、BND 3/2；旧 §10.3.1 文字不覆盖该 authority。
- **tests**：拒绝 `strict_advantage`/verdict/answer fields；actual Reader/Audit file mutation changes verdict；按 `companybrain-route-snapshot-host.v1` 生成并 hash 校验完整 host snapshot，再生成不含 host path 的 `companybrain-route-snapshot-public.v1`；CompanyBrain target、入口链接、任意 graph input 文件、frontmatter/page-type mutation changes route snapshot/`companybrain-observation.v2` and cannot reuse old gap；missing/incorrect snapshot file hash/tree digest→UNKNOWN/CB_MISSING；missing/duplicate/unknown `projection_keys`→INVALID；Audit-only business atom→UNKNOWN；ReaderTaskPath 缺 stage、错误顺序、wrong relation、CB untyped contract 的 path replay 负例；summary cannot alter verdict；TIE/UNKNOWN/INVALID/CB_MISSING block。
- **oracle**：质量 verdict 只从实际文件和冻结 CompanyBrain snapshot 计算。

### M252 — GREEN: actual quality gate and split states

- **Phase**：R3
- **status**：pending
- **depends_on**：M202、M251；design terminal clean
- **goal**：实现 evidence-only baseline/case loader、五维逐 case 重算、embedding route ledger 检查、source closure 和 publication 三状态。
- **files**：`src/knowledge_digest/task5_quality_gate.py`、`tests/acceptance/test_task5_quality_gate.py`。
- **read_only_inputs**：`config/task5-quality-cases-v2.json`、`config/task5-companybrain-baseline-v2.json`、`config/task5-runtime-authority-map-v1.json`、`config/task5-machine-evidence-contract-v1.json`、`config/task5-provider-contract-handshake-v3.json`（actual=`c15c0612…`、canonical=`fc821c35…`）、`config/task5-reader-path-relation-contract-v1.json`（actual=`c3f12166…`、canonical=`16de1b3c…`）、`config/task5-quality-result-v3.json`、`config/task5-companybrain-observation-v2.json`、`config/task5-source-block-claim-contract-v1.json`、`config/task5-source-direct-contract-v1.json`、`config/task5-source-page-manifest-v2.json`、`config/task5-slice-cases-v1.json`；loader 只 hash 校验并读取 frozen authority，且同时校验 actual SHA 与 canonical SHA；R3 先完成 source/block/claim、source/slice/path-relation/machine-evidence authority 的 identity 校验，M301 只能复核，不能首次建立 identity。
- **contract**：slice/full 显式分 mode 和 closure；full 必须闭合 `full_required_source_paths`，slice 只闭合冻结 `slice_required_source_paths`，缺 full 来源只能 `source_not_in_slice/not_evaluable`，不能给 `KD_WIN`、不能进入 full Reader/quality verdict。前四维原子必须在 Reader，只有 Reader-Audit 可用 Audit；五维分数只作诊断，严格胜出还要求 path replay、关系安全、真实 CB gap、8×5 feasibility matrix 和独立 observation。每个 request 计算 spec 的 selected-source identity，单源和多源都必须有非空 closure hash，并进入 provider/route/semantic ledger/PageProjection/RenderLedger/Audit/quality；重排/hash drift 不得 replay。QualityReader 的多源 Claim 必须逐 Claim 带 owner/source/block/locator，并通过 `co_support|conflict|unknown` 关系校验；页面级 rewrite gate、禁路径、`GENERATED_BY` Reader 泄漏和跨 projection boundary 复用都阻断。Reader-Audit 只比较实际 Markdown 可见面，使用冻结 evidence-level 梯度；gap 必须符合 route/taxonomy/business-answer/page-type/Reader-Audit mapping，缺 field/locator/维度映射为 `UNKNOWN`。
- **oracle**：独立重算 `quality_cases_proven/source_closure/publication_status`；记录四层 slice/full 状态，`not_evaluable` 只能来自冻结闭包差异，slice-local failed 仍跑 full 但阻断 released。page-rewrite/path-replay/surface/semantic 任一失败不能由 score 补回；8×5 matrix、逐 projection×dimension observation、同维 advantage basis 和 v2 embedding handshake 必须绑定 snapshot/tree digest，缺 gap/字段/唯一映射或发生复用均为 `UNKNOWN`。
- **dimension oracle**：逐格校验 observation schema 的 mapping：route=`unreachable|wrong_relation`，taxonomy=`missing_taxonomy_axis|wrong_relation`，business-answer=`missing_stage|unsupported_answer_claim|wrong_relation`，page-type=`untyped_contract|wrong_page_type`，Reader-Audit=`missing_provenance|untraceable_claim`；每类必须有对应 observation fields、dimension/文件 hash/行段 locator/scanner version。错配、缺失或复用统一 `UNKNOWN`，不得由分数补回。
- **STOP**：若测试不能拒绝静态答案/verdict/score、不能从实际 Reader/Audit/CompanyBrain 快照重算五维，不能进入 M252。

### M253-R — RED: relation-safe scoring and symmetric atom oracle

- **Phase**：R3 actual quality evaluator
- **status**：ready
- **depends_on**：M252；design terminal clean
- **goal**：在 M253 GREEN 前固定会失败的测试，防止结构分、case-local Claim ref 或词面命中制造假胜出。
- **files**：`tests/acceptance/test_task5_quality_gate.py`。
- **tests**：同义改写不误判、两侧共用 atom forms、泛词不计分、主体/客体互换失败、动作方向反转失败、步骤顺序变化失败、数量/比较符/量词变化失败、条件范围变化失败、否定/冲突 UNKNOWN、Reader-Audit evidence level 对称和 forbidden 归零、source/statement payload 双向闭合失败、遗漏限定词/动作/主体失败、空 claim-lineage span 失败；`relation-parser-v1` 的 canonical code-point offset、protected numeric/opaque token、段落/列表/表格同列与跨列、代码/链接/图片块、多个 cue 冲突、同距主体客体、条件结论边界、无法唯一排序和 ambiguity→Audit-only 分流。
- **oracle**：新增负例在 GREEN 前必须能失败；不得使用静态 verdict/score/answer，且 claim-lineage 不能绕过 relation check。
- **STOP**：若 RED 测试无法独立证明关系安全和 KD/CompanyBrain 对称裁决，不能进入 M253。

### M253 — GREEN: quality scoring and symmetric atom oracle

- **status**：pending
- **depends_on**：M252、M253-R；design terminal clean
- **goal**：实现冻结 v2 evidence-only rubric、对称 `atom_forms`、结构分、五维 strict gate 和 `task5-quality-result.v3`，不读取静态 verdict/score；结果必须符合只读 `config/task5-quality-result-v3.json`，并为每个 `projection_key × dimension` 独立生成 `advantage_basis`。
- **files**：`src/knowledge_digest/task5_quality_gate.py`、`tests/acceptance/test_task5_quality_gate.py`。
- **tests**：provider v2 rubric/baseline、等义改写、泛词/negation/semantic UNKNOWN、TIE/forbidden；fake/offline。Reader-Audit 覆盖双方同一 evidence-level 梯度；按 spec §11.3 覆盖 A/M 分母、空集合 UNKNOWN、round-half-up 两位 TIE、forbidden 不缩分母且独立失败、等级门槛和公式篡改；另覆盖五维 gap mapping、五轴缺失、wrong page type、missing provenance、unsupported answer claim、basis 复用/错配、digest 漂移和 completion 不在 Reader surface；新增逐 atom 缺行/重复、CB present 误算严格优势、CB absent→KD present、回退/unknown/forbidden 和 gap_atom_refs 越界负例。
- **oracle**：KD/CompanyBrain 共用同一 `atom_forms` 和 evidence-level 梯度；只有 baseline 文件缺失/hash 不匹配/applicability 缺失才是 `CB_MISSING`；结构分不能抵消内容缺失；`KD_WIN` 必须逐维读取 `config/task5-quality-result.v3.json` 的 basis contract，严格绑定同一 projection/dimension 的 CB gap、逐 atom observation、gap_atom_refs、strict_improvement_refs、non_regression、KD completion 和两侧 digest；任何缺失、复用、回退或漂移均为 `UNKNOWN`。证据写入固定 `quality/evidence/task5/repair-gates/R3.json` 的 `quality_oracle` 字段，不另建未授权目录。
- **R3 precondition**：M253 在追加 R3 最终事件前，必须读取当前 attempt 的 `attempt_event_index=1` preflight，并按全局 sequence 定位它；逐项比较 `input_hashes`、六个 case 集合、冻结的 8 个 `projection_keys`、baseline `projection_keys`、quality/baseline/source manifest identity、snapshot_tree 和 material_id；每个 projection 必须分别有 route、Reader、Audit、RenderLedger 和五维 quality observation ref，不能只用 case 级记录代替。任何不一致先追加当前 attempt 的 `precondition_failed`/`failed` event、保留旧 event 并 STOP。R3 attempt 还必须有 `embedding_contract_handshake`（handshake schema ref/SHA、full/slice request identity、candidate/vector/query hash、selected/route-only paths 和 selected-path consumption assertion）；缺失或 hash 漂移即 failed。
- **STOP**：M253 未通过或证据未绑定当前快照，M401 不得开始。
- **receipt**：M252 首个测试前校验 R2 promotion/canonical attempt；完成 route/evaluator focused gate 后在本次 R3 attempt 追加 preflight event；M253-R 先完成 RED，随后 M253 校验并追加 final/failed event，一次性写本次 `R3.json`、`tests/R3.json` 和 `inverse/R3.patch` attempt receipt，只有通过才更新 R3 promotion view，最终 quality oracle 必须逐条绑定上述 8 个 projection，且不得重写或删除旧 event。

上条中的 `sequence=1` 按两层 schema 修正为 `attempt_event_index=1`；全局 `R3-events.jsonl` 的 `sequence` 由 exclusive lock 分配并严格递增，重跑不得复用任何 global sequence。M252 只追加该 attempt 的 preflight event，M253 在同一 attempt 追加 final/failed event 并一次性写完整 attempt receipt；不能把 preflight receipt 改写成 final receipt。

### M301 — RED: runtime wiring, slice/full and Downloads

- **state oracle**：`candidate` 仅是运行中检查点；质量、来源闭包、Reader/Audit 或发布硬门失败的终态必须是 `publication_status=not_released`，同时保留真实 `outcome/reason_code`。`blocked|unavailable|overrun|cancelled` 是 global outcome，不得与 `candidate` 拼成终态或被误读为质量失败。

- **duplicate alias oracle**：同 hash alias 保留自己的 89-row coverage、Claim/Audit link 和 `duplicate_alias` 状态，但不额外发 source-digest 或生成重复 Reader；canonical Reader link、budget、输入顺序置换和 conflict/co-support 关系必须稳定。闭合 alias 可通过 canonical Reader link 满足包级 released，但 alias 自身 coverage、canonical_source_id/hash 或 Audit/link 任一缺失/不匹配必须阻断 released。当前真实清单无 alias；full 为 87 个普通 source-digest 加 1 个 SND replacement，仍是 88 个 present Reader 闭包。
- **relation oracle clarification**：测试清单中的“不同内容同 typed target”必须拆成互补 Claim=`co_support`、同一关系事实互斥=`conflict`、无法比较=`unknown`；不得仅凭 `target_key` 阻断，也不得把 unknown 合并成 Reader。

- **Phase**：R4 runtime wiring
- **status**：ready
- **depends_on**：M252、M253；design terminal clean
- **goal**：接入 provider route、slice/full gate、89 closure、Downloads artifact 和 no-fallback 断言；slice 唯一输入为冻结 `task5-slice-cases-v1`（空源不发请求、非空 descriptor=13），full 唯一来源 authority 为 `task5-source-page-manifest-v2.source_snapshot`；精确 `known_empty` 与隐藏/不匹配 empty 必须分开。
- **files**：`tests/acceptance/test_task5_full_run.py`、`tests/acceptance/test_task5_projection.py`。
- **tests**：覆盖四层 slice/full 状态、slice-local bad JSON 继续 full、expected not_evaluable、transport/auth 停止 full、89/empty/duplicate/conflict、source-direct 隔离、descriptor/hash、full 87 source-digest + 1 SND replacement、slice 12 source-digest + 1 SND replacement、所有公开 source-digest/SND Reader 的 page-type ReaderTaskPath、Home→Reader route replay、Reader/Audit 配对、lineage/rewrite gate 失败转 Audit-only/no raw fallback、selected vector/path 越界、多源 closure reorder/hash/block drift、page rewrite gate、唯一 package-release-predicate（87 Reader+1 SND Reader+1 exact known_empty Audit；任一其他 present 缺 Reader 阻断）、SND release-state matrix（zero-match without certificate must Audit-only/not_released; certificate plus complete scan may coexist with package release; incomplete/positive/ambiguous blocks）、M401-R、not_released、Downloads lock/cancel/failure sink 和 secret/payload/policy scan；逐类断言 observed calls、continue decision、failure evidence。
- **lifecycle tests**：S0 identity/target 失败不读 raw/provider、不建 output/lock/staging；S1 独占 lock/staging；M302 只做 M401-R gate-seam 接线，M402 S2 才做 receipt 漂移和 failure-sink rename；加锁失败保留 lock evidence、`failure_evidence_path=null`。详见 plan 的 S0–S4 顺序和 atomic oracle。
- **result-integrity gate**：每个已创建 output/staging 的运行唯一写 `_audit/run-result.json`，符合 `config/task5-run-result-v1.json`；必须有 `publication_status`、`outcome`、`reason_code`、`exit_code`、`observed_calls`、完整 WorkflowHub design identity 和产物 manifest；缺失、损坏或与原始退出码不一致时按 `failed=3`，并测试 blocked/unavailable 的 reason 不可互换。`Audit.md` 仍是人读入口，不是 JSON 目录。
- **oracle**：expected not_evaluable 和 slice-local semantic/path/typed failures 仍跑 full；budget/provider/config/calibration/identity/input/lock/publish/cancel global fatal 停止 full。candidate 不是终态，质量/完整性失败为 not_released 并保留 outcome/reason；transport/auth/timeout/429/5xx/partial embedding 不继续 full，2xx contract/lineage/relation/raw-copy 继续清单但 exit 1。page `copy|unknown` 不生成 Reader/KD_WIN；closure 相同才 exact replay，reorder/hash drift 新 identity且旧 receipt 不覆盖。失败 sink、lock owner、secret/payload/policy 和最终 Downloads 路径都必须可回查。
- **STOP**：若测试不能观察 slice→full、Downloads 输出安全、89 closure 和 provider failure Audit-only，不能进入 M302。

### M302 — GREEN: wire provider route into Task5 runtime

- **route-table contract**：`bundle/Home.md` 是唯一公开轴索引，必须同时提供按问题、按场景两组入口；不生成独立 `modules/`、`boundaries/`、`knowledge/` 目录。每个 Reader 恰好有两条 route row，顺序固定为 `entry_kind → question|entry_scene → product → module → object → scene → boundary → reader_path`，轴值必须来自同一 PageProjection/semantic ledger。每个 render unit 恰好有 `audit/<public_projection_slug>/u-<ordinal>`，Reader 链接到 `Audit.md` anchor，Audit entry 再绑定 source block/hash/locator。直接平铺 Reader、缺轴、跳过问题/场景入口、route/Audit row 不等于 PageProjection 或 replay 断链都失败；M301/M302 必须逐 Reader 验证 route row、Audit replay、链接目标、禁路径/禁名和内部 ID 泄漏。

- **publication layout gate**：除 bundle/Home/Audit、十一份固定 `_audit` machine-evidence 文件（现有七份索引/快照/ledger，加 raw-coordinate-map、SND zero-match certificate、SND verifier receipt、run-result）、五类 Reader 和 `source-not-documented` 回查外，public `companybrain-route-snapshot-public.v1` 固定写 `bundle/_audit/companybrain-route-snapshot.json`；M401 只写 host，M402 只写该 public projection 和通过 promotion 的 SND verifier projection，缺失/泄漏/禁路径即 `blocked/not_released`。M401 还必须消费并复核 promoted `task5-root-cause-evidence.v2`，否则 AC-020 失败。
- **user-surface acceptance**：M302/M401 必须对唯一的实际 candidate bundle 执行 R1-owned `surface-qa --bundle <candidate_bundle_ref> --r4-attempt <R4-promoted-attempt-ref> --directory-manifest-sha256 <directory-manifest-sha256> --candidate-tree-sha256 <candidate-tree-sha256> --receipt <R4-attempt-or-M401-receipt> --network-policy deny`。`candidate_bundle_ref`、R4 attempt ref/SHA、directory-manifest SHA 和 candidate tree digest 是 M401 必填输入，必须由 R4 promotion/manifest 提供，不能由 caller 自报；缺失、漂移或多个候选直接失败。surface-qa 只检查该唯一 bundle，按真实 Markdown 渲染语义解析 `Home.md`、两类入口、Reader 页面、相对链接、Audit anchor、媒体/链接目标和十一份 `_audit` 文件，逐项记录 resolved target、rendered heading/text presence、forbidden path/internal-field scan、Reader→Audit→source-block replay 和 cleanup；证据只写入当前 R4/M401 receipt，绑定同一 candidate ref、bundle manifest/tree digest，不能用 RouteRecord 或“文件存在”代替。命令失败、入口不可达、渲染后正文缺失、媒体/链接漂移或未清理 staging 都是 `not_released`，不是 design/implementation pass。

- **Phase**：R4
- **status**：pending
- **depends_on**：M202、M252、M253、M301；design terminal clean
- **goal**：把 preflight、semantic compile、embedding query/source route、typed projection、actual quality gate 接入 `slice → full`，并创建最终 R4 gate receipt。
- **files**：`src/knowledge_digest/task5_runtime.py`、`src/knowledge_digest/task5_projection.py`、`tests/acceptance/test_task5_full_run.py`、`tests/acceptance/test_task5_projection.py`；`scripts/task5_reader_quality.py` 归 R1 owner，R4 只能调用。
- **contract**：全量 89 条；先校验 source snapshot 和 D0 root-cause evidence 的 `coverage.source_scope`。87 个普通 present 非空 source-digest 必须逐条尝试，只有 87/87 route support 闭合、Qwen typed compile 和 Reader/Audit lineage 全通过时才满足 released 谓词；任一来源 unsupported/ambiguous/drifted 仍保留 Audit/失败证据，最终只能 `not_released`，不能用 raw/full-source 补齐。SND replacement 只有语义零匹配证书闭合时才各生成一个固定 diagnosis Reader，缺证书只能 Audit-only/not_released，known_empty/source-direct 只进 Audit；所有 Reader unit 绑定 Claim/block/hash/locator。QualityReader 必须有真实 embedding query/vector/`top_k=8`、mode-specific selected closure 和 ReaderTaskPath：Jina top-k 负责排序，full/slice 的冻结 required closure 必须完整并入 Qwen，slice 只消费 slice closure，Q-DIA-01 的 7→2 缺口必须写 `source_not_in_slice/not_evaluable`；多源 Claim 必须逐 Claim 绑定 owner/source/block/locator 和关系。候选集空、required path 不存在、descriptor/closure 漂移、并列顺序或 selected closure 不符都在 provider 前 blocked；只因 required closure 超过 top-k 或 top-k 未命中 required path 不阻断；route-only 不进 Qwen/KnowledgeUnit/Reader/Audit/评分；slice partial surface 不进入 full Reader/quality/KD_WIN。Home route table 按问题/场景双入口回放。按 plan S0–S4 执行 Downloads 同盘 staging、锁和 failure sink；M402 首个 raw/provider 前校验 M401-R，`/tmp`、跨设备、held/stale/ambiguous lock 均拒绝。
- **oracle**：route ledger/semantic-compile-ledger 均按 `evaluation_mode + route_kind + source_id|projection_key` 绑定，full/slice 不跨模式复用、不重试；slice/full mode-local bad JSON/schema/lineage/relation/raw-copy 分别继续剩余请求并终态 `not_released`/exit `1`，transport/auth/timeout/429/5xx/partial embedding、identity/budget/input/lock/publish 为 global `unavailable|blocked|overrun`/exit `2`，cancel 为 exit `4`；超预算立即停止；每类记录 class/reason/mode/request identity/observed calls/continue decision，失败/取消 ledger 必须进入 Downloads failure sink。source/quality/publication 三状态不互相覆盖。
- **receipt**：M302 首个动作校验 R3 event chain、R3 promotion/latest ref、canonical test receipt 和 inverse patch，并用本地 gate-seam fixture 验证 M401-R schema 绑定能力；runtime slice/full 与 Downloads/source closure/status gate 完成后先写本次 R4 attempt，失败也保留 `outcome`，只有通过才更新 `R4.json`、`tests/R4.json` 和 `inverse/R4.patch` promotion view，M401 打包前必须复核完整 attempt history 和 snapshot chain。

### SND verifier receipt closure

SND 的 producer certificate 不能自证。每次 `source-not-documented` scan 在 Reader promotion 前，由独立 deterministic verifier 读取当前 source snapshot 和 producer certificate，按 `config/task5-source-not-documented-contract-v2.json.receipt_contract` 逐 Block 重算并写不可变 attempt：`quality/evidence/task5/snd-verifier/attempts/<attempt_id>/verifier-receipt.json`。只有 `status=passed` 且 `source_snapshot_id/source_hash/certificate_ref/certificate_sha256/current_material_id/recomputed_result_digest/comparison_digest` 全部精确匹配的 attempt 才能原子 promotion 到 `quality/evidence/task5/snd-verifier/verifier-receipt.json`，再投影为 `bundle/_audit/source-not-documented-verifier.json`；unknown/blocked/mismatch 只能保留 attempt，不能写 Reader 或 release evidence。M302/R4 的 SND gate、M401 finalize、M402 release predicate 必须读取同一 promoted receipt，并把 receipt ref+actual SHA、canonical SHA 和 source/certificate/material 三方绑定写入 SND projection、directory manifest 和 run-result；旧 certificate、文件存在或 analyzer 自报不能替代 verifier receipt。

M102/M202/M252/M402 的命令宏由 runtime authority map 生成，不允许手写缩减版：runner 首先读取 17 项纳入项和 5 项排除项，按 key 排序，逐项校验 `path/schema/actual_sha256/canonical_sha256`，并将 exact key sets、map actual=`78bea9d08cb1b4e181770d7b8a182ff424512f2fbddd7e40d37f6e9ed1cd2f5b`、map canonical=`0c3f2f0e802479374b4db65b748b6d5034e9a19ade80d60f98423cbbddafc4de`、derived runtime=`ffab8d33b10a766d4c602bcb1cacd5f444f74d34992653df767e495c6dee260b` 写 receipt。命令显式参数与 map 不完全相等、缺 path/schema/actual/canonical、缺 root-cause input manifest、缺 D0 root-cause/source-scope closure、缺 SND verifier receipt 或把 M101 bootstrap 当完整 authority validator，均在首个 provider/embedding call 前 `blocked/calls=0`；这些字段由 authenticated handoff/runner 重读，不接受 caller 自报。

### M401 — focused/full test evidence packet

- **Phase**：R5 verification gate
- **status**：pending
- **depends_on**：M102、M202、M252、M253-R、M253、M301、M302
- **goal**：只完成聚焦/全量测试，生成可绑定当前快照的测试 receipt、AC trace、coverage limits 和剩余风险；本卡不调用正式 review。
- **design-review identity input**：M401 preflight/finalize 必须同时接收同一 `mini_task.design` terminal-clean binding：`review_attempt_ref`、`review_result_ref+sha256`、`review_report_ref`、`review_outcome=available`、`terminal_status=semantic`、`terminal_clean=true`、`design_review_contract_id`、`design_review_contract_hash`、`semantic_hash`、`snapshot_tree`、`material_id`；并绑定 Task5 `runtime_contract_id/runtime_contract_hash/semantic_contract_id/semantic_contract_hash`、promoted `task5-root-cause-evidence.v2` ref+SHA 和 `task5-root-cause-input-manifest-v1` ref+SHA。上述字段与完整 finding dispositions 进入 M401 packet，不能只写 snapshot/material，也不能拿 WorkflowHub review contract 冒充 runtime contract。
- **commands and order**：M401 由现有 `scripts/task5_reader_quality.py m401` 子命令在一个 attempt 内依次完成 preflight、focused、full-regression、finalize；它内部生成 attempt id，不接受未解析 identity。固定命令（从仓库根目录执行）：
  `uv run --frozen python scripts/task5_reader_quality.py m401 --workflowhub-handoff quality/evidence/task5/workflowhub-design-preflight-handoff.json --companybrain '/Users/Hugh/Hugh/Knowledge/CompanyBrain' --evidence-root quality/evidence/task5 --provider-mode fake --network-policy deny --candidate-bundle-ref <candidate_bundle_ref> --r4-attempt-ref <R4-promoted-attempt-ref> --directory-manifest-sha256 <directory-manifest-sha256> --candidate-tree-sha256 <candidate-tree-sha256> --focused-test tests/acceptance/test_task5_provider.py --focused-test tests/acceptance/test_task5_source_semantic.py --focused-test tests/acceptance/test_task5_projection.py --focused-test tests/acceptance/test_task5_quality_gate.py --focused-test tests/acceptance/test_task5_full_run.py --full-test tests/acceptance/test_task5_provider.py --full-test tests/acceptance/test_task5_source_semantic.py --full-test tests/acceptance/test_task5_projection.py --full-test tests/acceptance/test_task5_quality_gate.py --full-test tests/acceptance/test_task5_full_run.py --surface-qa`
  M401 的 authenticated binding args 必须显式落在同一命令/attempt：`--design-review-attempt-ref <design_review_attempt_ref> --design-review-result-ref <design_review_result_ref> --design-review-result-sha256 <design_review_result_sha256> --design-review-report-ref <design_review_report_ref> --design-review-contract-id wh-review.contract.mini-task-design.v1 --design-review-contract-hash <design_review_contract_hash> --design-review-semantic-hash <design_review_semantic_hash> --runtime-contract-id task5-reader-quality-provider-v2 --runtime-contract-hash ffab8d33b10a766d4c602bcb1cacd5f444f74d34992653df767e495c6dee260b --semantic-contract-id task5-provider-semantic-output-v2 --semantic-contract-hash 630d77570a66808fc497800b9b657ebb403e65ada16525b10b0203c286e6efa4 --design-snapshot-tree <design_snapshot_tree> --design-material-id <design_material_id> --root-cause-ref quality/evidence/task5/root-cause/root-cause-evidence.json --root-cause-sha <promoted-root-cause-sha256> --root-cause-input-manifest config/task5-root-cause-input-manifest-v1.json --root-cause-input-manifest-sha256 2909de6d6159deea90e8546150472faf75f0d15ab5f510c8ad3603c6ba80b2d`；runner 必须从 authenticated WorkflowHub handoff/M401 packet 重新读取这些值，并检查 89 条 source-scope ledger；post-provider route 87/87 closure 由 R2/R4 实际重算，缺失、漂移、caller 自报或 semantic hash 不等于 WorkflowHub `buildSemanticProjection()` 重算值均在 finalize/provider 前 blocked/calls=0；这些 args 不是 caller 获权依据。
  `--full-test tests -q` is deliberately forbidden: M401 full regression is exactly the five declared Task5 acceptance files, so unrelated repository tests cannot create a false failure or hide the Task5 result. `--surface-qa` is a required no-network user-surface check that consumes only the supplied candidate bundle/R4 manifest identity and records candidate ref, R4 attempt, directory-manifest SHA, tree digest, command/result hash in the M401 receipt and packet.
  命令必须通过 `/usr/bin/sandbox-exec -p '(version 1)(deny network*)'` 启动测试进程，主动探测 `socket.create_connection`、`socket.getaddrinfo`、`urllib.request.urlopen` 三条负例；同时强制 fake provider、`external_http_attempts=0`，记录 profile/命令 hash、exit 和 calls。sandbox 不可用或任一步骤失败只保留 attempt evidence，不 promotion、不发真实 provider。`SOURCE_SENSITIVE_CONTENT` 测试为 source-local blocked/calls=0、继续其他 mode 请求、最终 `not_released/exit=1`；`SOURCE_POLICY_UNVERIFIED` 为 global blocked/calls=0/exit=2、停止 full。
- **receipt/oracle**：`write-evidence preflight|finalize` 和 `test-receipt` 强制 fake、network deny、进程级 socket/DNS deny，记录实际 command/profile/stdout/stderr hash、exit、count、calls、snapshot/material 和 canonical bytes；每个 attempt 先写 `repair-gates/attempts/<id>/`，通过才 promotion，下一 gate 的 before snapshot 必须等于上一 gate promoted after snapshot。M401 packet 绑定 R1–R4、provider/semantic/source/layout/handshake/calibration/quality/CompanyBrain、AC trace、pre-M402 readiness 和 canonical SHA，不含 M401-R。focused/full 实际 command 都须 exit `0`；旧 receipt、静态 quality JSON、缺 dispositions 或 AC-RP-006/008–013 证据均 STOP。`SOURCE_SENSITIVE_CONTENT` 为 local blocked/calls=0→not_released/1；`SOURCE_POLICY_UNVERIFIED` 为 global blocked/calls=0→2。

### M401-R — terminal implementation review

- **Phase**：R5 verification gate
- **status**：pending
- **depends_on**：M401
- **goal**：使用 M401 生成的测试 receipt、当前快照、AC trace、coverage limits 和 remaining risks，执行真实运行前的正式 `mini_task.implementation` review；该卡只审查，不改代码、不替代测试，也不要求尚未执行的真实 89 条用户结果。
- **review_contract**：review 必须 terminal semantic；所有 finding 必须有 disposition；`unavailable`、non-terminal、partial 或未处置 finding 都不通过。发现问题回到对应 R1–R4 实现卡，修复后重新跑 M401 和 M401-R。
- **receipt/oracle**：每次 review 先写不可变 `quality/evidence/task5/m401-r-receipts/attempts/<review_attempt_id>.json`，只有符合 `task5-m401-r-review-receipt.v1` 且 `available + terminal_clean=true`、绑定当前 M401 packet/current material 的 attempt 才 promotion 到 `quality/evidence/task5/M401-R-review-receipt.json`；schema identity 使用 canonical SHA-256 `74584b624c2c672e6aa4f6d76ca98165f2a06e2fb5c40fca36b39f1807990d1a`，不使用格式化文件的 actual SHA。result/attempt/report/dispositions 可回查，失败/unavailable/partial/未处置 finding 只保留。M401-R 通过后，且仅由 authenticated WorkflowHub adapter，才能生成 `workflowhub-implementation-successor.v1` handoff；该 handoff 必须绑定 M401 packet、M401-R receipt、design/implementation review 的完整 result/attempt/report identity、当前 snapshot/material/worktree、runtime/semantic identity 和 writer attestation。M402 只能消费 successor promoted ref/hash；未 terminal clean、successor 缺字段或 writer 不符立即 STOP。

### M402 — real 89 run after all gates

- **Phase**：R5 real test
- **status**：pending
- **depends_on**：M401、M401-R；`mini_task.implementation` 必须 successful and terminal clean；`unavailable`、partial、non-terminal 或有未处置 finding 都不能满足依赖。
- **goal**：只读 raw/CompanyBrain 做一次新的 slice→full 真实运行并留下可查看产物。
- **SND ordering**：M402 读前只校验 `config/task5-source-not-documented-contract-v2.json` 的静态 schema/actual/canonical SHA，不要求尚不存在的 current receipt；拿到 lock 后先建立本次 raw snapshot、Block/Claim ledger 和 SND producer certificate，再由独立 verifier 生成并 promotion `quality/evidence/task5/snd-verifier/attempts/<attempt_id>/verifier-receipt.json` → `quality/evidence/task5/snd-verifier/verifier-receipt.json`。SND Reader、M401 finalize、release predicate、directory manifest 和 run-result 只消费这一轮 promoted receipt；旧 receipt、certificate 自报或文件存在不能替代它。
- **command**：从仓库根目录执行固定真实入口：`uv run --frozen python scripts/task5_reader_quality.py run --raw-input '/Users/Hugh/Downloads/confluence 原始数据' --companybrain '/Users/Hugh/Hugh/Knowledge/CompanyBrain' --output '/Users/Hugh/Downloads/KnowledgeDigest-task5-reader-quality-provider-real-20260824' --config config/task5-reader-quality-provider-v2.json --provider-config '/Users/Hugh/.config/knowledge-digest/config.json' --baseline-identity-from-root-cause-input RC-CURRENT-BASELINE AUTHORITY_ARGS --quality-config config/task5-quality-cases-v2.json --baseline-config config/task5-companybrain-baseline-v2.json --observation-config config/task5-companybrain-observation-v2.json --slice-config config/task5-slice-cases-v1.json --source-manifest config/task5-source-page-manifest-v2.json --quality-result-config config/task5-quality-result-v3.json --source-direct-contract config/task5-source-direct-contract-v1.json --calibration-manifest config/task5-calibration-manifest-v1.json --calibration-artifact evidence/phase4/calibration-artifact.json --review-manifest quality/evidence/task5/M401-evidence-packet.json --m401-r-receipt quality/evidence/task5/M401-R-review-receipt.json --snd-verifier-contract config/task5-source-not-documented-contract-v2.json --snd-verifier-contract-actual-sha 762f09595fe33d33531dd373cb0bf4f3cf1ee468442d0ebccb68314af7534fa5 --snd-verifier-contract-canonical-sha 253de24de01625c4fa14c5bfab57e81c3ef56dbbd6319fd89f4150152b4263fc --workflowhub-implementation-handoff quality/evidence/task5/workflowhub-implementation-handoff.json`。`AUTHORITY_ARGS` 由 runner 从当前 runtime authority map 生成并在进程内展开，不能由 caller 手写或删减；它负责 17 项 included、5 项 excluded、逐项 path/schema/actual/canonical SHA、map identity 和 derived runtime hash。`--config` 只提供运行参数，不替代 AUTHORITY_ARGS。该入口在读取 raw/CompanyBrain 或发 provider 前，独立读取并 hash 校验当前 M401-R promotion 和 authenticated implementation successor；同时校验 successor 的 `handoff_sha256`、`m401_packet_sha256`、snapshot/material/worktree、design/implementation/runtime/semantic identity、writer attestation 与 M401 packet/M401-R/invocation 三方相等；当前 SND verifier receipt 不作为读前输入，而由本次 source snapshot 生成。M401 packet 不包含 M401-R、SND verifier 或 successor 的反向 ref/hash；缺失、漂移、map expansion 不等价、SND contract identity 不一致或 baseline identity 不一致时 calls=0、blocked，不允许 caller 以环境变量补字段。
- **actual bundle surface QA**：按 plan 的 R1-owned M402 QA 执行：唯一 Downloads staging candidate 形成后、run-result/发布前，绑定实际 candidate、R4 attempt、pre-publish/final manifest/tree、snapshot/material、Reader/Audit、链接媒体、禁字段和 cleanup。receipt 写入 `quality/evidence/task5/m402-surface-qa/attempts/<attempt_id>/surface-qa.json`，`artifact_manifest.surface_qa` 回指 receipt/ref+SHA；M401 fake receipt 不得替代，缺失/漂移/未清理即 `not_released`。
- **inputs**：只有原始 89 条目录和 CompanyBrain 只读快照；不能把旧 candidate 当输入。
- **outputs/lifecycle**：只读 raw/CompanyBrain，输出 Downloads bundle、Reader/Audit、十一份 `_audit` machine-evidence（含 SND verifier receipt）、source/quality/status、CompanyBrain snapshot 和 exit。S0/S1 先写 `task5-preflight-result.v1`，通过后才加锁创建 Downloads 同盘 staging；已创建 output/staging 就必须有 `bundle/_audit/run-result.json`，缺失/损坏按 failed=3；`artifact_manifest.surface_qa` 绑定 pre-publish/final manifest/tree 和 cleanup。
- **oracle/STOP**：S0/S1 identity/哈希/绑定异常=`blocked/exit=2/calls=0`；S2 只接受 M401-R promoted receipt 和静态 SND contract，随后必须生成并 promotion 本次 current SND verifier receipt，失败则不生成 SND Reader、不进入 release predicate。回查 89、slice/full、provider ledger、五维、SND current receipt、surface receipt、manifest/tree、Reader/Audit、链接媒体、cleanup 和 exit；provider/lineage/quality/surface failure=`not_released`，known_empty 只进 Audit；缺 credential/provider/calibration/budget 只保留真实 blocked/unavailable。
- **STOP**：缺 credential、provider unavailable、calibration mismatch 或预算不足时，保存真实 blocked/unavailable 证据并停止；这不满足“审查通过后真实测试”的前置，也不自行修改用户配置或放宽门禁。

### Repair AC-RP mapping required by M401

这十四项是同一 Task5 的证据索引；M401 为每项绑定当前 snapshot、test receipt 或 gate receipt：

| ID | 必须证明 | Owner |
| --- | --- | --- |
| 001 | provider identity、调用、secret scan | M102/M302 |
| 002 | Qwen typed output、Claim/Block 闭包 | M202/M302 |
| 003 | embedding query/vector/top-k/selected closure | M252/M302 |
| 004 | provider failure 只进 Audit、无 raw fallback | M202/M302 |
| 005 | fake 成功、坏 JSON、超时、partial、缺 key、漂移 | M102/M202/M252 |
| 006 | focused/full tests 的命令、exit、count、hash | M401 |
| 007 | M401 readiness pending；M402 才写真实 89-run | M401/M401-R/M402 |
| 008 | evidence-only case/baseline，结果从实际文件重算 | M251/M252/M253 |
| 009 | slice/full 分流；local 继续，global fatal 停止 | M252/M302 |
| 010 | provider failure 不生成 `full-source` Reader | M202/M302 |
| 011 | Reader→render unit→Claim→source locator | M202/M302 |
| 012 | quality/source/publication 三状态独立重算 | M301/M302 |
| 013 | provider/calibration/budget/Downloads identity | M102/M252/M302 |
| 014 | 当前 M401-R terminal-clean promotion | M401-R |

依赖唯一为：`M253-R → M253 → M301 → M302 → M401 → M401-R → M402`；M401 还显式依赖 M102、M202、M252，且必须在其后重跑 focused/full。R1–R4 各自 STOP 并保留 evidence，不得跨 gate 借通过；M302 先验证 R1 fake LLM/R3 fake embedding promotion；M401 的 AC-RP-007 只保留 pre-M402 readiness，M402 才判定真实运行，且必须消费 M401-R promoted receipt 和 SND verifier promoted receipt（若本次运行包含 SND replacement）。

### Design review correction gates

- **M251/M252**：只消费冻结 v2 case/baseline hash；不得从实现代码或旧 v1 fixture 自行选择 atoms、markers、baseline 或 projection 集合。
- **M252**：required atom 缺失、forbidden 命中、字段/lineage 缺失先阻断该 projection；多 projection case 取最低分并要求全部 projection 通过。
- **Q-OPR page type**：二维码和 Zero Touch 保留 `projection_subtype=qr|zero-touch`，但两个 projection 的 `page_type` 都必须是合同允许的 `operation`；`qr`/`zero-touch` 不能成为第六种页面类型。
- **M202**：首个网络请求前完整构建 prompt；`llm.max_input_chars=120000` 超限只写 Audit，不截断、不调用。
- **M102**：只接受批准 calibration SHA-256 `c31b1f8c78a889dff4cdbbab0fb695871c513844b5c8392d52dbbd8ad33e4c06`。
- **M402**：provider unavailable/blocked 只记录真实阻塞，不伪装质量通过，不以 fake provider 代替用户要求的真实 89 条运行。

### Current implementation checkpoint — 2026-08-25

- [x] 修正五维比较器：完整 CompanyBrain 快照才可断言明确缺失；保留自然语义观察；Q-POS/Q-CON direct-answer 进入业务答案门。
- [x] 修正 CompanyBrain source-bound stage 的跨页面泛词误命中，并增加回归测试。
- [x] 记录 live Jina embedding 的实际成功 HTTP batch 数；无该证据时质量结果保持 blocked/not_released。
- [ ] 跑 focused/full 全量回归。
- [ ] 用新 Downloads 目录执行真实 r32 slice→full，并审查 Reader/Audit/质量五维。
- [ ] 补齐当前 WorkflowHub 要求的 authenticated material、M401/M401-R 与独立 review；未完成前不得 close/released。
