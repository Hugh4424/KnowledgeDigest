# Task5 当前生效任务卡 v4.7（2026-09-04）

> 只有本节生效：从文件开头到本文件末尾的唯一归档分隔线之前全部属于当前任务卡；归档分隔线及其后全部内容是历史资料，旧命令、旧 hash 和旧输出树均不再授权执行。

## 当前修订 v4.7（2026-09-04）：进入实现前的页面、状态和 fixture 硬核对

M402 的最终 public `_audit` 只允许 active spec 固定的十一项文件；`bundle/_audit/run-result.json` 是 public receipt。`quality-result`、CompanyBrain observation 和 host-run receipt 都由同一 M402 attempt 写入 `quality/evidence/task5/actual-run/` 的不可变证据，run-result 只保存 quality artifact 的 ref+SHA，不复制第二份质量结果。

LINEAGE-001 的唯一缺口例外是精确 `原始资料未明确` 且无 evidence 的 section：保留 `Reader.section` 与 `Reader.answer_body` 两行 ledger，分别计入 `unknown_units`，不伪造绑定，也不进入事实 lineage 分母；其余事实 unit 必须 100% raw-bound。

`AC-v4-01…AC-v4-13` 的唯一完整定义在 active `spec.md`；本任务卡只记录执行入口和证据归属，不复制第二套验收定义。

这四项是同一 Task5 的实现验收子项，不是新增任务或后续任务；未全部有当前 receipt 前，M401 不得通过。设计审查不属于这些硬门：`mini_task.design` 没有可认证的 `terminal-clean` 结果时，只记录 DESIGN-ADVISORY 的缺失/风险，不阻断 M401、M401-R 或 M402。

- **ENTRY-001**：检查 `pyproject.toml` 的 `digest` 入口和 `simple_cli.main` 的调用图；允许它作为薄适配层，但必须证明业务编排唯一进入 `compiler.digest`，CLI 不生成业务文本/分类/质量 verdict，旧 runtime/provider/evaluator 零生产 import。
- **OUTPUT-001**：用 fake/no-network 运行真实 public entry，验证正式结果只在隔离测试 run root 的 `bundle/` 产生；Reader 只从 `bundle/Home.md` 进入 `products/<product>/<page-type>/...`，机器闭包只能精确包含 active `spec.md` 开头列出的十一项 `_audit` 文件，不得产生 `_digest/modules/boundaries/knowledge/staging/attempt` 公共路径。真实 Downloads 只由 M402 写入。
- **BASELINE-001**：构造 CompanyBrain 文件 hash/tree、raw source manifest、observation 的漂移和跨 run 负例；验证 `quality.py` 只接受同一 M402 的 `companybrain_snapshot_id/companybrain_tree_sha256/observation_sha256/source_manifest_sha256`，缺失或漂移只能 `CB_MISSING/UNKNOWN`。
- **LINEAGE-001**：构造 Reader 标题、问题、正文句、五轴、页面类型、section 和 Home route 的无 evidence、错 source、错 raw hash、错 locator、重复 unit 负例；验证 compiler 中间 evidence ledger 每个可见 unit 恰好一行且 `lineage_coverage=100%`，再验证 formalizer 移除中间 ledger 后 public bundle 仍由 active 十一项机器闭包回查，失败时不发布。

每项都要记录：当前命令、输入 snapshot/material、stdout/stderr/result hash、实际结果、失败反例和 `attempt_id`。凡是 gate 写隔离 run-root，`attempt.json` 必须写 `run_root_ref`；M401-R 不写 run-root 时不得生成伪造引用。不能用旧测试、旧候选、静态质量 JSON 或“文件存在”替代；这四项通过后仍必须经过 M401、authenticated M401-R 和真实 M402。

Provider 配置的执行边界也属于当前任务卡：默认读取 `~/.config/knowledge-digest/config.json`，M402 的 authenticated runner 可用显式 `--provider-config` 覆盖；LLM 只准 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`，embedding 只准 `https://llm.paxszapp.com/v1` 的 `jina-embeddings`，receipt 必须写实际模型。每个 provider section 先取直接 `api_key`，缺失时才按 `api_key_env` 回退；根级 `api_key` 仅作迁移兼容补入缺失 section。配置、key、endpoint、model 或 calibration 的 preflight 失败必须在首个请求前记录 `blocked|unavailable` 与 `provider_calls=0`；密钥不得进入任何 public/host receipt、payload、cache 或报告，绝对配置路径仅 host-only 可见。

补充反例必须落到对应卡片：C2 校验 `qwen_payload_sha256` 绑定实际 `model.generate` payload 字节；LINEAGE-001 校验同一 `route_name` 重复命中同一 `home_target_page_identity` 时渲染前失败；C0/BASELINE-001 校验 CompanyBrain observation row 的 `status` 只接受 `present|absent|unknown|forbidden`，并按 spec 映射 `CB_MISSING/UNKNOWN/N/A`，不得由实现自行扩展。

四组行为测试的 gate owner 固定为：`ENTRY-001` 与 `OUTPUT-001` 在 `tests/acceptance/test_task5_publication_contract.py`；`BASELINE-001` 在 `tests/acceptance/test_task5_quality_gate.py`；`LINEAGE-001` 在 `tests/acceptance/test_task5_projection.py`。M401 focused/full 命令必须覆盖这三个 owner 文件，其他测试只作相邻回归，不替代四组 owner。逐 AC trace 的 implementation anchor 必须落在真正覆盖该 AC 的具体测试函数；当 gate owner 只覆盖通用入口、而具体 Reader/Home/lineage 行为由 `tests/test_simple_digest.py` 覆盖时，允许 AC trace 引用该相邻回归，但不能因此取消 gate owner 的覆盖要求。`tests/acceptance/test_task5_full_run.py` 是 M401 full 的 slice→full/run-result 回归 owner，负责验证运行级闭包和非网络完整编排；它不替代上述四组行为 owner。

C0 的 authority/schema/hash/slice 派生测试唯一承载文件为 `tests/acceptance/test_task5_contract.py`；该文件与四组行为测试同属当前 Task5 测试面，C0/M401 命令必须显式包含它。

M402 表格中的通过条件与 spec 同义且更具体：所有 `applicable=true` 的 projection×dimension row 必须为 `KD_WIN`，所有 `applicable=false` 的 row 必须恰为 `N/A`，矩阵不得缺行、重复或多出其它 verdict；“五维全 KD_WIN”不能单独作为通过依据。

slot 的 `route_name:page_identity` 和 `route_name:home_target_page_identity` 只表示 `route_name + ":" + home_target_page_identity` 实际值，字段名不进入 bytes。M401-R receipt 采用 `task5-m401-r-review-receipt.v1`，除现有字段外必须含 `source_receipt_ref`、`source_receipt_sha256`，顶层 promotion 只原样提升 attempt-local source receipt。纯 lineage/quality 失败按 `not_released`/exit 1，global identity/authority/provider 失败才按 `blocked|unavailable`/exit 2。

M401 packet 同样由 authenticated adapter 将通过 attempt source 原样 promotion 到 `quality/evidence/task5/M401-evidence-packet.json`；source ref/SHA 只记录在同一 M401 attempt 的 `attempt-receipt.json`，promotion view 与 source bytes 完全一致。M402 host-only `quality-result.json` 顶层必须写 `companybrain_snapshot_id`、`companybrain_tree_sha256`、`observation_sha256`，逐 row 的 companybrain digest 必须与其一致；public bundle 只保存该 artifact 的 ref+SHA。

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
| M402 | `uv run --frozen digest <raw_input> <downloads_run_root> --companybrain-root <companybrain_root> --config config/task5-reader-quality-provider-v2.json --quality-config config/task5-quality-cases-v2.json --provider-config <provider_config> --gate M402 --m401-packet quality/evidence/task5/M401-evidence-packet.json --m401-r-receipt quality/evidence/task5/M401-R-review-receipt.json --workflowhub-successor quality/evidence/task5/workflowhub-implementation-handoff.json`（`raw_input`、`companybrain_root`、`provider_config` 和 Downloads 输出根由 authenticated runner 注入；实际路径/身份只进 host-only receipt 的 `provider_config_ref` 等字段） | `<authenticated Downloads run_root>/bundle/_audit/run-result.json`；host-only=`quality/evidence/task5/actual-run/attempts/<id>/host-run-receipt.json` + `companybrain-observation.json` + `quality-result.json`（均由同一 M402 attempt 写入，不进入 public bundle） | 真实 89 条、四产品、Jina/Qwen、Reader/Audit 闭包；所有 `applicable=true` 行为 `KD_WIN`、所有 `applicable=false` 行恰为 `N/A`，且 projection×dimension 矩阵无缺行、重复或其它 verdict；host receipt、observation、quality artifact、public run-result 和最终 tree/hash 互相闭合 | `not_released/blocked` |

C0–C2 只验证合同、输入/反例和 fake provider seam；C3 是独立的 fake/no-network Reader/Audit/quality contract attempt，必须使用自己的隔离 `run_root_ref`，不能和 M401 的实现审查或 M402 的真实 Downloads 运行合并为同一张卡。C3 的 attempt、bundle 和 receipt 都必须留在 `repair-gates/attempts/<id>/C3/`；M401 只消费这些不可变字节和反例结果，不把 C0–C3 的合并 pytest 退出码当作 C3 已执行。

`M401-R-review-receipt.json` 固定包含 `schema_version`、`review_kind`、`m401_packet_ref`、`m401_packet_sha256`、`review_result_ref`、`review_result_sha256`、`source_receipt_ref`、`source_receipt_sha256`、`snapshot_tree`、`material_id`、`terminal_status`、`terminal_clean`、`all_findings_disposed`、`finding_dispositions`、`outcome`、`status` 和 `reason_code`，不得省略或增加未声明字段。M401-R 先在自己的 attempt 目录写不可变 source receipt，再由同一 authenticated adapter 原样提升到顶层 promotion view；promotion view 不追加 source ref/SHA，也不能另写或编辑内容，来源 ref/SHA 只保留在 receipt 自身的固定字段中。M401-R 只读 `.../M401/M401-evidence-packet.json`、同目录 `attempt.json`、`attempt-receipt.json` 和 `inverse.patch`，并复算 packet/attempt receipt SHA 后完成 inverse 校验；通过后才更新 promotion view，不判断真实五维胜负；M402 才负责真实运行和五维结论。BASELINE-001 只使用 fixture 构造的 CompanyBrain 树/hash，真实 CompanyBrain 仅在 M402 读取。

## C1：89 条 Evidence 闭包

C1 是离线只读合同门，不读取用户 raw、CompanyBrain 或 provider，也不写 host-run-receipt。它使用冻结的 `task5-source-page-manifest-v2.json`、受控 fixture 和 source semantic 测试，验证 89 行 source manifest 的字段、产品归属、Block/Claim locator、content hash、空源/重复别名/失败状态和 compiler 中间 `_audit/sources.jsonl` 映射。真实 89 条 raw 的快照、Block/Claim 生成和 `source_manifest_sha256` 只由 M402 的 `compiler.digest` 在 authenticated runner 中完成；M402 再按 89 个 RunManifest source rows 的 canonical JSON 规则重算，并与中间 projection 相等；该中间文件在 formal audit 前移出 public bundle。

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


## ARCHIVE-NON-ACTIVE: previous root material

# mini-task tasks：Reader 质量整合

| ID | 任务 | AC |
| --- | --- | --- |
| T01 | 来源扫描、产品/模块映射和 unclassified/general 兜底 | 01,03,07 |
| T02 | 正文清理、Reader 投影和超长拆分 | 04,05,06 |
| T03 | 产品 overview、知识类型入口、模块 index、根导航 | 01,02,06 |
| T04 | 接入 `task3_full_release.py --raw-input` | 07,09 |
| T05 | 失败边界和旧包保护测试 | 07,08 |
| T06 | 接口形状、80 分代理、相关测试和完整 pytest | 01-09 |
| T07 | 真实资料运行并与 CompanyBrain 对比 | 01-09 |
| T08 | 一次 implementation wh-review，修复有效 findings | all |

顺序：`T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08`。

设计审查结果：一次 `mini_task.design` 已完成；major finding 已通过兜底和拆分修复，minor findings 已通过 80 分口径、最小接口和过程元数据处置闭合。不得机械重复设计审查。

完成定义：相关 acceptance 与完整 pytest 通过；真实运行有独立 output、source manifest、质量报告、比较报告和降级说明；能回答产品层级、overview、模块入口、来源覆盖、Reader 泄漏和正文是否仍是原文堆放；wh-review findings 原样留存。

## T07/T08 收尾复跑（2026-08-19）

- 正式 89 条输出：`/Users/Hugh/Downloads/KnowledgeDigest-task4-reader-quality-compiler-real-20260819-v39-89`。
- 结果：`source_count=89`、`reader_source_count=88`、`failure_count=0`、`package_status=candidate`。
- 已知 title-only 空页 `emm for android /AE - AirViewer厂商管理.md` 只在精确 `source_uri + content_hash` allowlist 下进入 Audit `not_applicable`，保留原始快照，不进入 Reader，不生成 Claim；其他空源仍 hard fail。
- CompanyBrain 机器对照：`better_than_companybrain`；`blocking_reasons=[]`；路径和边界/来源清晰度严格更好，其他轴不变差。
- 回归结果：聚焦 `28 passed`；声明的最终验收集合 `291 passed in 4.40s`；完整 pytest `733 passed, 3 skipped`。
- 对应决策：`specs/task4-reader-quality-compiler/decision-log.md` 的 D-026；正式候选已完成，未把候选冒充生产 `released`。
- verify-code 外部 WorkflowHub review provider 仍不可用，已原样记录，不能写成外部复核通过。
- 用户对齐事实（2026-08-19）：用户明确要求只执行 `verify-code` 并关闭 KnowledgeDigest 任务，不归档当前会话；已按此执行。
