# Task5：当前 Reader 编译链实现

## 当前执行卡：IMPLEMENT-CURRENT（v4.7 合同收敛）

### 目标

在不改写冻结四份材料、原始 Confluence 或 CompanyBrain 的前提下，把公开 `digest` 接到唯一的 Reader 编译链：Qwen typed semantic output → Reader 页面，Jina 路由 → Home 问题入口，`quality.py` 只做质量裁决，`publisher.py` 负责锁、校验和原子提交。缺少真实 provider、证据或质量输入时必须失败并保留原因，不能伪造 released。

### 允许修改

- `src/knowledge_digest/compiler.py`
- `src/knowledge_digest/providers.py`
- `src/knowledge_digest/publisher.py`
- `src/knowledge_digest/simple_cli.py`
- `src/knowledge_digest/quality.py`
- `tests/test_simple_*.py`
- `tests/acceptance/test_task5_*.py`

### 先做的行为

1. `digest` 只从输入目录读取，生成 `Home.md`、Reader、`Audit.md` 和 `_digest` 机器证据。
2. Qwen/Jina 必须通过 `providers.py` 的真实接口；fake provider 只用于无网络测试。
3. provider 失败、证据断链、输入漂移或发布器失败都明确返回非成功状态，不生成可误读的半成品。
4. slice→full 复用必须由同一 run context 的精确身份命中，不能拼接两个孤立输出。

### 测试路线

- backend/feature：先跑 Task5 acceptance focused，再跑 `uv run --frozen pytest -q`。
- 关键 oracle：输出布局、89 条来源清单、Reader→Audit→原始定位、五类页面、五维比较、provider calls 和失败状态必须从实际文件/实际命令重算。

### 停止条件

- 需要改冻结 `decision-log.md/spec.md/plan.md/tasks.md`，且没有用户明确批准的同一任务合同纠偏。
- 需要伪造 WorkflowHub、M401-R、CompanyBrain 或 provider 证据。
- 缺失材料只能被默认成通过。

### 当前状态

- 2026-09-01：全量回归 `800 passed, 3 skipped`；仅证明代码回归，不证明 M401/M402 或 released。
- 2026-09-01：当前设计材料已补齐生产链、RenderLedger 和发布回滚合同；实现尚未完成，WorkflowHub 当前仍缺 authenticated make-decision handoff。

### 本 Phase 执行事实（2026-09-01）

- RED：新增行为测试先因 `digest_slice_then_full`、RenderLedger、锁和质量入口不存在而收集失败；这是实现缺口，不是 provider 失败。
- 实现：已修改 `compiler.py`、`quality.py`、`publisher.py`、`simple_cli.py` 及对应测试；没有调用 raw、CompanyBrain 或真实 provider。
- 路由：test-routing-advisor 实际判定为 `fullstack`，理由是编译器、质量裁决、发布事务和公开入口同时变化；本阶段沿用 backend/feature 兼容回归命令并覆盖本地文件事务。
- GREEN：`uv run --frozen pytest -q tests/test_simple_digest.py tests/test_simple_providers.py tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_provider.py tests/acceptance/test_task5_quality_gate.py tests/acceptance/test_task5_full_run.py` → `64 passed`；`compileall`、`git diff --check` 通过。
- 限制：未生成 M401 receipt，未执行 authenticated `mini_task.implementation`，未调用真实 Qwen/Jina，不能进入 M401/M402，也不能宣布 released。

## 本卡完成条件

生产入口、质量裁决和发布状态机都有真实 consumer；focused tests 覆盖成功、provider 失败、证据断链、锁冲突、原子提交失败和共享 run context 复用。实现 receipt 必须记录实际改动、命令、退出码、快照、路径 hash 和可验证 inverse patch；它仍不能替代 M401/M401-R/M402。

## 本轮允许修改

- `src/knowledge_digest/task5_runtime.py`
- `src/knowledge_digest/compiler.py`（同一 Task5 的 slice quality wiring 根因修复）
- `src/knowledge_digest/quality.py`（同一 Task5 的 candidate binding policy 修复）
- `tests/acceptance/test_task5_publication_contract.py`
- `tests/acceptance/test_task5_full_run.py`（仅在已有测试需要补断言时）
- `tests/test_simple_digest.py`（同一回归测试）
- `apply/phase-cards/task5-publish-machine-evidence.md`
- 经用户明确批准的同一 Task5 当前合同文件：`spec.md`、`plan.md`、`tasks.md`、`decision-log.md`、`config/archive/task5/task5-source-not-documented-contract-v2.json`

## 验收条件

1. 使用 `config/task5-publication-layout-v2.json` 时，发布候选必须物化全部 11 个固定 `_audit` 文件。
2. 机器证据只保存哈希、来源相对路径、行/块定位、调用收据和状态，不保存原文、密钥、绝对主机路径或临时目录路径。
3. `source-not-documented` 没有当前 material/workflow verifier 收据时，必须明确为 `blocked`，不得伪装成通过。
4. `directory-manifest.json` 能回查固定布局、文件哈希和禁止路径扫描结果。
5. 现有最小单元测试保持兼容；新增测试先证明当前缺失证据会失败，再证明完整证据可通过校验。
6. 不修改 `/Users/Hugh/Downloads/...` 下任何现有官方结果；真实重跑另行进行。

## 非目标

- 不重新生成知识正文。
- 不修改 CompanyBrain、原始 Confluence、Task4 或历史发布物。
- 不新增 provider 调用，不伪造 WorkflowHub/M401-R 收据。
- 不因测试全绿就宣布 `released`；发布仍需五项质量和当前物料闭环同时通过。

## 测试路线

```bash
uv run --frozen pytest -q tests/acceptance/test_task5_publication_contract.py
uv run --frozen pytest -q
```

## 停止条件

- 发现既有测试依赖旧发布合同且无法兼容。
- 需要修改冻结需求、原始数据或外部 WorkflowHub 物料才能让门禁通过。
- 任何实现会把缺失的当前材料、verifier 或 provider 结果默认为成功。

## 执行事实（由 build-code 执行者填写）

- 2026-09-02 用户批准 v4.4 合同纠偏：精确 V50 缺失继续保留为历史 `blocked/calls=0`，但不再阻断当前 raw-only M401/M402；CompanyBrain 比较基线改为 M402 当次快照；SND 使用 SND-RULE-002 描述性语境规则。

- 2026-08-25 已按冻结合同执行 D0/root-cause-preflight；attempt：`quality/evidence/task5/root-cause/attempts/d0-165d05b72b2a4aaaae1f2e13f7b47226/root-cause-evidence.json`。
- D0 真实结果：`outcome=blocked`、`provider_calls=0`、`embedding_calls=0`。阻断原因包括：冻结的 `RC-USER-V50` 候选目录实际 `file_count=0`、`byte_count=0`，以及当前工作树相对 `RC-CURRENT-BASELINE` 已发生哈希漂移。未替换输入、未更新冻结基线、未调用 provider。
- 当前正式候选 `/Users/Hugh/Downloads/KnowledgeDigest-task5-reader-quality-provider-real-20260825-r30/bundle` 的机器证据复核为 `2/11`，缺 9 个固定 `_audit` 文件；其内部 `quality.json`/`bundle/README.md` 的 `released` 字段与根目录 `not_released` 矛盾，不能采信；因此仍是 `not_released`。
- 本轮实现测试已通过 focused `86 passed`、机器证据测试 `3 passed`、全量 `900 passed, 3 skipped`。这些测试不能代替 D0、M401、M401-R 或真实 89 条运行。
- 当前 `scripts/task5_reader_quality.py` 只有 `run`、`finalize`、`root-cause-preflight`，冻结任务要求的 `m401` 尚未实现；历史 D0-H 仍 blocked，但按 D-093/D-094 已明确不阻断只用当前 raw 89 条的候选修复。继续实现前仍需完成 raw-only preflight、当前实现身份和本轮机器证据门禁；不把历史 V50 输入替换成新候选。
- 2026-08-25 只读检查用户配置：`/Users/Hugh/.config/knowledge-digest/config.json` 的 `.llm.api_key` 与 `.embedding.api_key` 均存在；LLM endpoint 已匹配，但 model 为 `qwen3.8`，不匹配冻结允许的 `qwen3.6`。未读取或写出 key 值，未调用 provider。
- 2026-09-01 固定公开入口与正式门禁分层：`digest` 绑定 `knowledge_digest.simple_cli:main`，只负责简洁 Reader 编译；`scripts/task5_reader_quality.py` 继续承载 `run`、`m401`、`raw-preflight` 等正式 Task5 gate，并新增入口回归测试。
- 2026-09-01 修复完整回归暴露的真实确定性缺陷：Task 2-A Reader index 原来写当前墙上时间，跨秒重放会产生不同字节；现在优先使用输入快照版本日期，非日期版本使用固定合法哨兵值，并保留原有生成字段校验。
- 2026-09-01 执行当前绑定 worktree 的 D0-R：attempt `quality/evidence/task5/raw-preflight/attempts/d0-r-9d1c8e279e1b40f99fd1/raw-preflight.json`，真实原始目录闭合 89 条来源，其中 87 条普通可尝试、1 条已知空源、1 条重复别名，Block/Claim 共 16613 条，provider/embedding/external HTTP 均为 0；未生成 Reader 或发布物。
- 2026-09-01 继续刷新 D0-R：attempt `quality/evidence/task5/raw-preflight/attempts/d0-r-c1238be329eb4eddbdc2/raw-preflight.json`，仍为 89/89 来源、87 条普通可尝试、1 条已知空源、1 条重复别名，provider/embedding/external HTTP 均为 0；未生成 Reader 或发布物。
- 2026-09-01 完成当前实现边界回归：公开 `digest` 只加载 `simple_cli`；来源索引不复制 `raw_text`；Jina 只接收 route metadata；LLM/embedding `retry_attempts` 非零直接拒绝；Task5 focused 测试 `60 passed`，全量 `797 passed, 3 skipped`。
- 2026-09-01 补齐 D0-H 正式入口并执行：最新 attempt `quality/evidence/task5/root-cause/attempts/d0-h-63ce8df2c8af432994cc/root-cause-evidence.json`，冻结的 `RC-USER-V50` 目录不可读，只保留 `failed/blocked` 证据，未替换候选、未 promotion、provider/embedding/external HTTP 均为 0；证据不含主机绝对路径或原文。
- 阶段结论：`not_released / blocked_until_inputs_restored`，不宣布 released，不执行 WorkflowHub close。
- 2026-09-01 修复回归缺陷：Task5 typed semantic output 的内部 `axis_evidence_ids` 未被 `_normalise_page` 接受，曾导致质量分支误报 0 个 Reader 页；修复后 focused 复测 `2 passed`，全量回归为 `804 passed, 3 skipped`，`compileall` 和 `git diff --check` 通过。
- 2026-09-01 当前 WorkflowHub `build-code` 仍为 `ready/in_progress`；当前 `mini_task.design` 没有可复用的 authenticated `make-decision design_preflight`。未伪造 handoff，未进入 M401/M401-R/M402，未读取 raw/CompanyBrain，provider/embedding 调用仍为 0。
- 2026-09-03 修复 Reader lineage 根因：有可用 evidence 时，Task5 semantic summary 不得返回 `原始资料未明确`；UNKNOWN section 不得携带伪 evidence/claim 引用；quality render ledger 删除 Reader 标题、问题和页面类型的无来源豁免。新增回归先以两项失败测试复现，再以 `tests/acceptance/test_task5_source_semantic.py` 与 `tests/test_simple_digest.py` 通过。
- 2026-09-03 本轮实际测试：Task5 focused `116 passed`；全量 `852 passed, 3 skipped`；`git diff --check` 通过。test-routing-advisor 按实际 changed files 返回 `fullstack`，但本改动没有前端或服务部署面，具体验证走本地 compiler→render-ledger→quality 的离线 slice；未调用 raw、CompanyBrain、Qwen 或 Jina。
- 2026-09-03 未扩大本轮文件边界去修改历史比较脚本或只读上下文；模型身份收敛仍由当前 provider/config/Task5 合同负责。Task5 相关回归 `88 passed`，最近一次全量回归 `852 passed, 3 skipped`，`git diff --check` 通过。
- 2026-09-03 根据一次真实 `mini_task.design` provider 返回的可执行 finding，修复当前合同和 M402 前置校验：统一 active 文档的 `fixture_source_count`，补齐 M401-R `needs_human|partial` 的 `terminal_status=semantic`，明确 `workflowhub-implementation-successor.v1` 的顶层/嵌套字段与 self-excluding canonical hash，并使 `compiler.py` 在 M402 首个 raw/provider 读取前校验 handoff canonical bytes、闭合字段、nested ref/hash、M401/M401-R/current identity 和 authenticated attestation。新增两个 handoff 负例；Task5 focused `93 passed`，`git diff --check` 通过。当前仍未生成 authenticated successor，未进入 M401-R/M402。
- 2026-09-03 在上述修改后重新跑完整回归：`uv run --frozen pytest -q` → `854 passed, 3 skipped`；未调用 raw、CompanyBrain、Qwen 或 Jina。该结果只证明仓库回归，不替代 authenticated design、M401/M401-R、真实 M402 或五项胜出。
- 2026-09-04 修正发布状态边界：普通 `digest` 即使编译器的结构候选行全部显示 `KD_WIN`，也只能写 `quality_result_status=candidate`、`publication_status=not_released`、`verdict=UNKNOWN`，并返回 `completed/formal_m402_required`；只有 authenticated `--gate M402` 才允许返回 `released`。新增回归覆盖候选质量结果不自我晋级和普通/正式入口状态差异。
- 2026-09-04 当前实现验证：Task5 focused `70 passed`；全量 `uv run --frozen pytest -q` → `866 passed, 3 skipped`；`compileall`、`git diff --check` 通过。一次真实 v3 运行在全量第 54/87 个来源时被人工中止，未发布 Downloads 结果；没有把半成品当作交付。
- 2026-09-04 可查看的上一份真实候选仍是 `/Users/Hugh/Downloads/KnowledgeDigest-task5-qwen38-real-20260904-v2/bundle`，但它由状态修正前代码生成，只能作为历史 provider-backed candidate，不能按 `released` 采信。M401 packet、M401-R receipt 和 authenticated WorkflowHub successor 仍缺失，正式 M402/close 继续 pending。
- 2026-09-04 再修正质量候选的独立性：compiler 的 `dimension_verdicts` 不再把同一结构观察复制成两个相同 verdict；适用维度写 `[本次结构观察, UNKNOWN]`，只把确定的 `N/A` 保留为 `[N/A, N/A]`。这样没有独立第二轮评估就不会伪装成两轮一致通过；相关测试和全量回归仍为 `866 passed, 3 skipped`。
- 2026-09-07 修复 v23 真实 slice 的同一 Task5 根因：slice 没有 CompanyBrain observation 是预期边界，但 `build_candidate_quality_result` 无条件写入 `companybrain_observation_missing`，被 `_summarize_slice_result` 正确识别为意外 warning，导致 12/12 projection ready 仍被标为 `slice_quality=failed`。新增 `require_companybrain_observation`，默认保持 full/evaluator 严格校验；compiler 仅对 `evaluation_mode=slice` 传 `false`，slice 仍保留 `quality_dimensions_not_all_kd_win`。RED 为 `TypeError: unexpected keyword argument`，GREEN 定向质量回归 `4 passed`，Task5 相关回归 `142 passed`，完整回归 `878 passed, 3 skipped`；`git diff --check` 与 `compileall` 通过。v23 真实候选仍是修复前代码的 `not_released`，未据此宣布 released，需新 attempt 才能证明修复后的 slice/full 结果。
- 2026-09-07 v24 真实重跑验证了上述 slice 修复：12/12 slice projection、89 条 full 输入、87/87 普通来源处理、quality/slice/full 均通过，观察到 143 次 LLM 与 18 次 embedding；但在 staging bundle 原子改名后仍错误引用旧 staging 路径，因 `directory-manifest.json` 不存在退出，结果保留为失败证据，未发布。
- 2026-09-07 修复 v24 暴露的发布收尾根因：`task5_runtime` 在 `os.replace(stage, output)` 前缓存 candidate manifest hash，改名后从 published output 重新读取 manifest hash，再写最终 quality/result；新增改名后 hash 校验回归。定向测试 `2 passed`，`compileall` 与 `git diff --check` 通过。
- 2026-09-07 v25 真实重跑再次失败且如实保留为非发布：Q-DIA-01.diagnosis.query 的 provider verifier 拒绝了不受证据支持的询问措辞，导致该 projection 缺页；根因不是编译器静默兜底，而是冻结 evidence closure 漏掉原始 `GoInsight/16 问数自动识别数据集.md` 的 L31-L32。修正 `config/task5-quality-cases-v2.json` 的 query/boundary/action 证据闭合至 L29-L32，并新增回归断言；定向 `3 passed`、JSON 校验、`compileall`、`git diff --check` 通过。
- 2026-09-07 v26 以修正后的 evidence contract 完成真实 provider-backed M402：输出 `/Users/Hugh/Downloads/KnowledgeDigest-task5-reader-quality-compiler-redesign-formal-20260907-v26`，`run_id=run-d0649285abd54bf3`，89/89 来源、4 个业务产品另含 shared、12 个 projection、99 个 Reader 文件；full/quality/slice/slice_execution/slice_preflight/SND/surface QA 全部通过，120/120 个适用五维比较 verdict 为 `KD_WIN`，无 hard blocker/judge error，观察到 141 次 LLM 与 18 次 embedding，最终 `released`。公开 bundle 不含质量内部输入；bundle manifest 116 条文件记录、禁止路径扫描通过，host receipt、run-result canonical/tree hash 与实际字节闭合。Task5 定向回归 `144 passed`，全量 `880 passed, 3 skipped`；`compileall`、`git diff --check`、Task5 JSON 校验通过。
- 2026-09-07 当前合同复核纠正上一条历史事实的使用边界：v26 由旧 `task5_runtime` 控制面生成，且绑定旧快照与旧六文件 M401 闭包；它保留为 provider-backed 历史候选，不是当前 v4.7 的 M401/M401-R/M402 或 `released` 证据。当前 WorkflowHub promotion refs 的 snapshot/fixture 仍过期，未调用 provider、未写 Downloads、未伪造门禁。
- 2026-09-07 修复 source recovery 合同漂移：`compiler.py` 的 Task5 全局 recovery 上限从 16 收敛到 active plan/spec/tasks 规定的 12；保留单 source 最多追加 3 次。新增常量合同断言和 14 个失败来源的行为回归，证明初始 14 次之外最多 12 次 recovery（总计 26 次）。定向 `2 passed`；最终全量 `uv run --frozen pytest -q` 为 `891 passed, 3 skipped`，`compileall src/knowledge_digest scripts` 与 `git diff --check` 通过。
- 2026-09-07 当前实现继续收敛到 v4.7：M401 与 formal public bundle 共用固定十一文件 machine-evidence 闭包；M402 在读取 raw/CompanyBrain/provider 前绑定当前 worktree、runtime authority 文件哈希与 WorkflowHub runtime identity；source recovery 上限为全局 12、单 source 追加最多 3；Home 路由必须是真实 Markdown link；quality candidate 只有经过同一 owner 的 post-rename finalize、最终 surface QA、tree/manifest 复核和固定 artifact promotion 才能进入 released。
- 2026-09-07 最新回归：`uv run --frozen pytest -q` 为 `892 passed, 3 skipped`；`python -m compileall -q src/knowledge_digest scripts` 与 `git diff --check` 通过。只验证本地代码与 fake/offline contracts，不证明真实 provider 或正式发布。
- 2026-09-07 当前 M402 仍被真实外部状态阻断：promoted M401/M401-R/WorkflowHub refs 仍绑定旧 `snapshot_tree=7c3ebd0f26954c4b3b931f9a621f2d6072ee5637`，当前 checkout 的只读 WorkflowHub snapshot 已为 `a25315f8d4ac2ce9874d44cf22452c6a3baae24b`；当前 runtime config 的 quality-contract hash 也未随本轮冻结 authority 更新。直接调用 `_validate_m402_gate` 在读取 raw/provider 前失败：`M402 runtime authority hash is stale: config/task5-quality-cases-v2.json`。未调用 provider，未写 Downloads，未伪造或覆盖门禁证据。
- 2026-09-07 修复当前材料的实际契约分叉：根 `spec.md`、`plan.md`、`tasks.md` 中仍把旧六文件/`run-result.receipt.json` 当作 public 的 active 描述，已对齐 v4.7 的十一文件 formal closure、host-only quality-result finalize 和 `task5-run-result.v1`；根与 `specs/task5-reader-quality-compiler-redesign/spec.md` 都新增可解析的当前 `## 验收标准`，WorkflowHub `activeAcceptanceCriterionIds` 现在稳定得到 `AC-v4-01…AC-v4-13`，不再回退历史 AC。正式 `status:begin` 仍报告 `quality_status=in_progress`、`product_release_status=not_released`，未升级任何 gate。
- 2026-09-07 文档收敛后的完整回归：`uv run --frozen pytest -q` 为 `892 passed, 3 skipped`；`python -m compileall -q src/knowledge_digest scripts` 与 `git diff --check` 通过。此轮只改当前材料，不调用 provider、不写 Downloads、不伪造 M401/M401-R/WorkflowHub 证据。
- 当前阶段结论：本地实现与回归验证通过；正式交付仍为 `release_pending/not_released`。当前快照尚未由 authenticated WorkflowHub 重发 M401/M401-R/handoff，现有 C3/M401 bundle 不符合十一文件 formal closure；不得宣布 released 或 close。
- 2026-09-07 通过官方 WorkflowHub `verify --action=execute` 重新执行 `uv run --frozen pytest -q`，结果 `892 passed, 3 skipped`；新 receipt `quality/tests/task5-reader-quality-build-code-v30.json`，exit code `0`，当前 snapshot tree `6a7e8373f27f46fb119915ea6aed29c591ea2eab`，receipt hash `c1142456e64558dffb8dafbb4fea91175bbc0a78b04f37644c4112699efa0938`；官方实现 receipt 同步刷新为 `quality/evidence/implementation/47120e11f7deec1ec6f3476cb59d5a7b43cd2f57d427637eecd44a3b660ca9f0.json`，同一 snapshot。
- 2026-09-07 使用上述当前 receipt 运行官方 `build-code`，`risk_tests_fresh=satisfied`，但 `acceptance_criteria`、`stage_end_spec_analyze`、`finding_dispositions`、`integration_review` 仍 missing；stage outcome `unavailable`，`quality_status=incomplete`，`product_release_status` 仍为 `not_released`。运行中未调用 provider、未写 Downloads、未手写缺失 gate。
- 2026-09-07 authority/hash 收敛后重新做本地全量回归：`892 passed, 3 skipped`（60.04s），`compileall` 与 `git diff --check` 通过；M402 读前探针已通过本地 runtime authority，随后如实停在外部 handoff 的旧 `runtime_contract_hash=07524fc4…`，当前 authority 重算为 `94795519…`，未读取 raw/CompanyBrain、未调用 provider。
- 2026-09-07 通过官方 WorkflowHub `verify --action=execute` 重跑 `uv run --frozen pytest -q`：`892 passed, 3 skipped`，新 receipt `quality/tests/task5-reader-quality-build-code-v31.json`，snapshot tree `a5af1785e7b27c11cc7622aac7d0ecccc6524044`，receipt hash `9902bd8d1d0125bc621a6f5fe61fa3c9c643586dde8c492ab26b378953c51063`；authenticated implementation receipt 为 `quality/evidence/implementation/b3446ab7173ebbb1f73cea4e3b297909444ce7840538b74e35469bf0be9e5c66.json`，同一 snapshot。
- 2026-09-07 使用 v31 receipt 运行官方 `build-code`：`risk_tests_fresh=satisfied`，`acceptance_criteria`、`stage_end_spec_analyze`、`finding_dispositions`、`integration_review` 仍 missing；stage outcome `unavailable`，`quality_status=incomplete`，`product_release_status=not_released`。未调用 provider、未写 Downloads、未伪造 gate。

### C3 私有 fixture producer 修复卡（2026-09-07）

- **目标**：让 C3 真正生成可供 M401 消费的、fake/no-network、十一项 `_audit` 闭合 bundle；不增加 public CLI，不读取 raw/CompanyBrain，不产生真实质量结论。
- **允许文件与符号**：`src/knowledge_digest/compiler.py` 的 `_validate_closed_fixture_files`、`_run_c3_fixture`；`tests/acceptance/test_task5_compiler_formal_tree.py` 的 C3 focused cases；本卡执行事实。
- **覆盖 AC**：AC-v4-01、AC-v4-02、AC-v4-03、AC-v4-04、AC-v4-05、AC-v4-06、AC-v4-07、AC-v4-08、AC-v4-09、AC-v4-10、AC-v4-11、AC-v4-12、AC-v4-13 的 fixture machine-closure trace 绑定；不宣称真实 raw/CompanyBrain/provider 质量通过。
- **测试路由**：实际改动跨 compiler、publisher boundary 和 repair evidence，沿用 `fullstack` 风险级别；具体 backend 行为走 focused compiler/publication acceptance，不运行真实 provider。
- **非目标**：不修改四份冻结材料、外部 WorkflowHub/M401-R、Downloads、原始资料或 CompanyBrain；不写当前正式 gate promotion。
- **停止条件**：缺少外部 AC trace、formal bundle 校验失败、attempt/run-root 已存在、provider seam 未显式注入时，在任何 C3 写入前失败。

### C3 卡执行事实（2026-09-07）

- RED：逆向补丁回归先真实失败；旧 `_m401_inverse_patch` 生成删除 patch，不能在 after snapshot 上执行合同要求的 `git apply --check --reverse`，stderr 为 `already exists in working directory`。
- 修复：抽出 `_validate_closed_fixture_files` 供 C3 预发布校验和 M401 目录校验共用；新增私有 `_run_c3_fixture`，显式注入 fake provider、要求外部 AC trace、在发布前验证十一项 `_audit` 闭包，然后只写 `C3/run-root/bundle`、`attempt.json`、`inverse.patch`。补丁生成器收敛为通用 `_repair_inverse_patch`，使用“空树→输出”的创建 patch，reverse apply 可回滚。
- focused：`uv run --frozen pytest -q tests/acceptance/test_task5_compiler_formal_tree.py` → `13 passed`；包含缺 trace、四产品 fixture、固定字段、十一项 machine closure、已有 attempt 拒绝和 reverse-apply。
- C3 contract slice：`uv run --frozen pytest -q tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_quality_gate.py tests/acceptance/test_task5_projection.py tests/test_simple_digest.py` → `86 passed`。
- 邻接回归：`uv run --frozen pytest -q tests/acceptance/test_task5_compiler_formal_tree.py tests/acceptance/test_task5_contract.py tests/acceptance/test_task5_provider.py tests/acceptance/test_task5_source_semantic.py tests/test_simple_providers.py` → `50 passed`；全量 `uv run --frozen pytest -q` → `895 passed, 3 skipped`；`compileall`、`git diff --check` 通过。
- Review：`wh-review ... doctor` → `status=ok`；本轮未发起 broker/provider 审查请求，故 review 仍为未取得，不能当作 clean review 或 gate pass。
- 限制：测试产物均为 pytest 临时目录；未写正式 `quality/evidence/task5/repair-gates/` promotion，未调用真实 provider，未读取 raw/CompanyBrain，未修改 Downloads；C3/M401/M401-R/WorkflowHub 当前证据链仍未闭合。

- 2026-09-07 C3 实现后的官方 build-code 刷新：通过 authenticated WorkflowHub `verify --action=execute` 执行 `uv run --frozen pytest -q`，exit `0`；receipt `quality/tests/task5-reader-quality-build-code-v32.json`，当前 snapshot tree `24c898f566aef4867325149a7d1050240a5f87fe`，receipt hash `27580c4c2fc5aa562450073378e61cfb20011e32879e5dac48a58da663c02379`。实现 receipt 同步刷新为 `quality/evidence/implementation/5523c9ba7b4722bcb74347dd0a2c1fc09c9492bece9e270899ca220314e1c3c5.json`，同一 snapshot；官方 build-code 仍为 `quality_status=incomplete`、`stage_outcome=unavailable`、`product_release_status=not_released`，`acceptance_criteria`、`stage_end_spec_analyze`、`finding_dispositions`、`integration_review` 仍 missing。未调用 provider，未写 Downloads，未生成正式 C3/M401 promotion。

- 2026-09-08 收紧 C3 AC trace：`_m401_trace` 现在要求每个 AC-v4-01…13 的 `actual_result` 与 `failure_counterexample` 都包含唯一的相对测试函数锚点 `tests/...py::test_...`，并拒绝重复/缺失锚点；`_run_c3_fixture` 同时要求 trace 内命令与 attempt command 完全一致。新增泛化 trace fail-closed 负例，并把 C3 与兼容 M401 fixture 改为 13 个实际测试函数锚点；未增加 public CLI、未读取 raw/CompanyBrain、未调用 provider、未写正式 C3 promotion。
- 2026-09-08 本轮验证：`uv run --frozen pytest -q tests/acceptance/test_task5_compiler_formal_tree.py` → `14 passed`；C3 owner slice `uv run --frozen pytest -q tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_quality_gate.py tests/acceptance/test_task5_projection.py tests/test_simple_digest.py` → `86 passed`；两者合并并含相关回归 → `100 passed`；最终 `uv run --frozen pytest -q && python -m compileall -q src/knowledge_digest scripts && git diff --check` → `896 passed, 3 skipped`，compileall/diff-check 通过。
- 2026-09-08 限制：本轮只证明 C3 trace 结构和本地行为测试；没有写 `quality/evidence/task5/repair-gates/` 正式 C3/M401 promotion，没有刷新 M401-R/WorkflowHub successor，没有调用真实 Qwen/Jina、raw 或 CompanyBrain，没有写 Downloads；官方 WorkflowHub 当前 stage 仍 `quality_status=incomplete` / `product_release_status=not_released`。
- 2026-09-08 通过官方 WorkflowHub `verify --action=execute` 重跑当前 `uv run --frozen pytest -q`，exit `0`；receipt `quality/tests/task5-reader-quality-build-code-v33.json`，snapshot tree `11f12b7f4a40093ed979c8f6c6d68ce24a65049a`，receipt hash `fe4831469a477b342c2e79177708cbe9e5d14c375d3bfe572ca09c0b6033eea1`，output hash `ab08f63ae0021c3bbac8b739fa4fbceb8c433a212c698d54a856f67f4dd6ead7`。该官方事实只更新测试 receipt，不改变 M401/M401-R/M402 或 release 状态。

### 同一 Task 的薄入口契约纠偏（2026-09-08）

- **原因**：按 active spec 的 public `digest --gate M401 --fixture-bundle ... --m401-attempt ... --m401-run-root ...` 实际调用时，`simple_cli` 在进入 compiler 前因两个历史 reader positionals 必填而退出；这使已生成的 C3 attempt 不能被 public M401 消费。
- **允许文件**：`src/knowledge_digest/simple_cli.py`；`tests/acceptance/test_task5_publication_contract.py`；不改 M401 compiler、gate schema、四份冻结材料或历史 runtime。
- **验收**：M401 可省略 reader positionals 并继续进入 compiler；普通 digest/M402 仍要求 `new_dir` 与 `kb_dir`；不增加 CLI/gate，只修正同一 public 入口的参数边界。
- **停止条件**：若需要改变 M401 gate 语义、读取 raw/CompanyBrain/provider 或增加第二入口，停止并保留当前 parser 缺口。

- 2026-09-08 parser 修复后重新取证：官方 WorkflowHub `verify --action=execute` 执行 `uv run --frozen pytest -q` 成功，receipt `quality/tests/task5-reader-quality-build-code-v34.json`，snapshot tree `23ebac7da58c0d6e5a99a1c448744f6521123308`，receipt hash `5deb7efd2b29f00ad6004b11640a1eb2d51c2b27f8cdc9350544248d5b742ada`，output hash `bda293886d29784f89b26d8ba02ad6f15a20c3b26cffd5651ff4558ddc851b20`。
- 2026-09-08 绑定 v34 snapshot/material 生成新 C3 attempt：`quality/evidence/task5/repair-gates/attempts/c3-v34-20260908/C3`，status `passed`，bundle tree `81aa5b3f8db7a2d3e2f0e0ef0ad8d46c6f37a6d10698c606155b925dc081f9a2`，manifest `e6b0835713af602e43ac7744a74a785162dbef5d74fc9e2b68ecd109fc5bde82`，逆向应用检查 exit `0`；仅使用 fake providers 和受控四产品 fixture。
- 2026-09-08 通过修正后的 public flag-only M401：`digest --gate M401 --fixture-bundle ...c3-v34... --m401-attempt ...m401-v34... --m401-run-root ...m401-v34.../run-root` 返回 `completed`；attempt-local packet `quality/evidence/task5/repair-gates/attempts/m401-v34-20260908/M401/M401-evidence-packet.json` 为 `passed/pre_m402_readiness=true`，13 条 AC trace、fixture tree/manifest 与 C3 相等，network-deny focused `124`、full `146` 均 exit `0`，逆向应用检查 exit `0`。M401 attempt 与 packet 绑定 snapshot `23ebac7d…`、material `3ddd3bad…`。
- 2026-09-08 边界：C3/M401 仍是 attempt-local，未 promotion 到 `quality/evidence/task5/M401-evidence-packet.json`；M401-R、WorkflowHub successor、当前 R1-R4 promotion refs 仍缺失。未调用真实 Qwen/Jina、raw 或 CompanyBrain，未写 Downloads；因此仍 `not_released/release_pending`，不能把 M401 attempt-local passed 当作 M401-R/M402/released。
