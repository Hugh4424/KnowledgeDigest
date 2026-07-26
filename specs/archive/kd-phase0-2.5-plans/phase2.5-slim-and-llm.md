# Phase 2.5 实施计划：瘦身 + 接入真实 LLM 提炼

状态：**B1–B6 已落地并提交**（`c075570` @ `cursor/phase2.5-slim-llm-closeout`）
日期：2026-07-26（收口 2026-07-27）
基线：main @ 8316bf7（clean），当时 `uv run pytest tests/ -q` = 76 passed（其中约 11 个为纯形状检查，见下）；收口后 **131 passed**
输入：`/tmp/kd_review/architecture-audit.md`、`/tmp/kd_review/code-review.md`、`/tmp/kd_review/test-verification.md`

**验收测试口径**：计划文中「76 个验收测试」是 B1 前基线，含约 11 个纯形状检查（只 `assert callable(...)` / `.exists()` / 查 `--help` 字符串），约 14% 不验证行为；B6 已对关键空跑/溯源/落盘缺口补行为断言，形状检查是否保留见 `docs/plans/open-questions.md`。

本文已归档；活文档入口见 [`docs/plans/README.md`](../../../docs/plans/README.md)。

| 批次 | 状态 |
|---|---|
| B1 瘦身主刀（删 recovery，S5/S6 直写） | ✅ |
| B2 append-only / 写前归档 | ✅ |
| B3 rethink/risk/90天/去重收敛 | ✅ |
| B4 LLM 生成器 + 注入链 | ✅ |
| B5 脏样本 fixtures | ✅ |
| B6 测试补强 + 文档状态表 | ✅（本文件） |

---

## 0. 本轮目标与已拍板决策

**一句话目标**：把 3867 行「事务机制很重、核心是恒等函数」的现状，改成 ~2400 行「防丢失完整、真的会用 LLM 提炼」的小工具。

用户已拍板，不可改：

| # | 决策 | 含义 |
|---|---|---|
| 1 | 删 recovery.py 全套事务机制 | CAS / journal / 两阶段提交 / **recovery 内重量锁**全删，用「写前归档只增不删」替代。接受极端写失败时知识库半写；原文在归档里，重跑即恢复。let it crash。**保留** CLI 级 flock（`lock.py`）仅防双进程误踩，不是 CAS |
| 2 | 补真正的 LLM 提炼生成器 | `default_generator` 目前是恒等函数，本轮换成真实现 |
| 3 | LLM 接入方式 | **不用任何 CLI**。实现 OpenAI 兼容 + Anthropic 兼容两种 HTTP API 格式，从环境变量读 base_url / api_key / model，代码保持轻量 |
| 4 | 总目标 | 简单小巧好维护的 skill，把乱文档转成结构化知识库。**防丢失 9 条硬约束原封不动** |

**硬边界（本轮绝不碰）**：
- `ingest.py` 空壳判定 / 指纹去重 / 失败快照
- `kb_structure.py` why/版本字段 fail-closed 门禁
- `draft.py` 的 `_component_spans` / `_page_groups` 拆页逻辑（防丢失第 5 条）
- `provenance.py` 的 claim 级溯源与归档（只删 90 天清理那段）
- `_validate_candidate`（draft.py:374-406）的 5 条硬门 —— 接 LLM 后这是唯一防漂移防线，**只能加强不能削弱**

---

## 1. 关键结构事实（决定了批次顺序）

这三条是排序的根据，不是背景：

**F1. S5/S6 真身被包在 copytree 克隆里。**
`_prepare_formal_outputs`（pipeline.py:457-549）第 489 行 `shutil.copytree(paths.kb_dir, prepared_kb)` 克隆整个知识库，而 511-542 行的 writeback / audit_provenance / source_index / archive_claim_records / `_update_claim_history` / cleanup_expired_archives —— **这是 S5/S6 的真正实现** —— 全部跑在克隆目录里。
所以删 recovery 不是纯删除，是**先把 511-542 剥出来直写真 kb_dir，再删外面那层壳**。这决定了批次 1 必须是「剥离+删除」一个动作，不能拆成两批。

**F2. `_update_claim_history` 被调用两次，语义不同。**
- `pipeline.py:738` 传 `persist=False` —— 只建 supersede 链，不落盘
- `pipeline.py:529` 在克隆里默认 `persist=True` —— 真写盘
删 recovery 时这个双调用契约极易改错。C1 的 append-only 修复必须在这个契约理清之后做（→ 批次 2 依赖批次 1）。

**F3. generator 注入缝断在 draft() 参数上。**
`Generator = Callable[[dict], Any]`（draft.py:290）只是 type alias；`generator` 仅是 `draft()` 的 kwonly 参数（draft.py:494）；**pipeline.py:675/709 两处调用都不传**，cli.py 也不暴露。
config.py 是纯 JSON 加载，**无任何环境变量读取**，且 `_CONFIG_KEYS` 白名单（config.py:21-31）会拒绝未知字段。
所以「接 LLM」不只是写个 client，还要新拉一条 cli → config → pipeline → draft 的注入链，并改白名单。

---

## 2. 批次总览与依赖图

```
B1 瘦身主刀（recovery + pipeline 编排 + writeback 回滚 + 相关测试）
 │        ↓
 ├────────┼──────────────┐
 ↓        ↓              ↓
B2 数据   B3 二次瘦身    B4 LLM 生成器      B5 脏样本 fixtures
丢失修复  (rethink/risk   （可与 B2/B3 并行）  （可与 B1-B4 全程并行）
          /90天/去重)
 └────────┴──────────────┴──────────────────┘
                    ↓
              B6 测试补强 + 文档状态表
```

| 批次 | 一句话 | 依赖 | 可并行 |
|---|---|---|---|
| B1 | 剥出 S5/S6 直写 kb_dir，删 recovery.py 全套 | 无 | 否（主刀，独占） |
| B2 | 修 claim-history / pending-review / writeback 三个数据丢失 bug | B1 | ✅ 与 B3、B4 并行 |
| B3 | 压单轮 rethink、删 risk 引擎、删 90 天清理、收敛重复工具函数 | B1 | ✅ 与 B2、B4 并行 |
| B4 | LLM 生成器（OpenAI + Anthropic 兼容）+ 注入链 | B1（B3 完成后更省事） | ✅ 与 B2 并行 |
| B5 | 补真实脏文档 fixtures | 无 | ✅ 全程可并行 |
| B6 | 修空跑测试、补回滚/溯源内容断言、更新文档状态表 | B1-B5 | 否（收口） |

**并行建议**：B1 单独跑完 → 然后 B2 / B3 / B4 三个并行（改动文件基本不重叠，见各批次「涉及文件」）→ B5 任何时候都能起 → 最后 B6 收口。

**文件冲突提示**：B3 和 B4 都会碰 `draft.py` 和 `config.py`。若三路并行，建议 B3 先合入（它只删代码），B4 在其上加 provider 配置，避免 `_CONFIG_KEYS` 白名单和 rethink 循环处打架。若怕冲突，退化为 B3 → B4 串行，B2 仍并行。

---

## 3. 批次详情

### B1 — 瘦身主刀：剥离 S5/S6 + 删除 recovery 全套

**目标**
让 writeback 直接写真 `kb_dir`，不再走「克隆整库 → diff → staging → 两阶段提交」。删掉设计文档明确判「删除」的全部机制（design:113 / :123-125 / :163）。

**做法（顺序不可换）**
1. 把 `_prepare_formal_outputs` 内 511-542 行的 S5/S6 调用块（writeback → audit_provenance → source_index → archive_claim_records → `_update_claim_history`）提取成一个新函数 `_commit_outputs(paths, drafts, ...)`，路径参数从 `prepared_kb` 换成 `paths.kb_dir`。
2. 删除外壳：`_prepare_formal_outputs`（457-549）剩余部分、`shutil.copytree`（489）及 `tempfile.TemporaryDirectory`、`shutil` import（pipeline.py:7）。
3. 删除 staging/diff 层：`_formal_snapshot_paths`(376-389)、`_file_bytes`(390-399)、`_output_kind`(400-410)、`_stage_formal_diff`(412-454)、`_mark_report_committed`(552-569)。
4. 删除 run 身份与 resume 分支：591-632（`build_input_manifest` / `manifest_hash` / `stable_run_id` / `RecoveryPaths.for_run` / `load_recovery_state` 恢复路径）。
5. 删除锁生命周期：696-701（acquire_lock）、745-766（prepare + mark_prepared + plan_hash）、778-779（commit_staged_outputs）、786-794（record_recovery_error + release_lock）。用普通 try/except 或直接不捕获（let it crash）。
6. 删除 `pipeline.py:29-43` 整个 recovery import 块。
7. `rm src/knowledge_digest/recovery.py`（694 行）。
8. 删 `writeback.py:236-266` 批量回滚块（在两阶段提交之下本已冗余）。**注意：删回滚不等于放弃防丢失 —— 防线转移到 B2 的「先归档后覆盖」顺序修正上，两者必须一起看。**
9. 测试：删 `tests/acceptance/test_phase2_rethink.py:17-30` 的 recovery import 块 + 8 个硬删测试（`test_run_identity_is_stable...`(200)、`test_commit_persists_state...`(217)、`test_second_writer_is_rejected...`(251)、`test_dry_run_does_not_create_lock...`(273)、`test_partial_commit_resumes...`(322)、`test_commit_rejects_baseline_conflict...`(353)、`test_delete_tombstone_is_idempotent...`(385)、`test_same_input_after_commit...`(413)）；改写 2 个灰色测试（`test_phase4_regression_targets_and_cli_boundary_remain_explicit`(425) 去掉 recovery 断言、`test_insufficient_signal_only_commits_its_queue_entry`(450) 走新的直写路径）。

**涉及文件**
- `src/knowledge_digest/pipeline.py`（794 → 目标 ~300）
- `src/knowledge_digest/recovery.py`（删除）
- `src/knowledge_digest/writeback.py`（275 → ~210，删回滚块）
- `tests/acceptance/test_phase2_rethink.py`（14 → 6 个测试）

**验收标准**
```bash
uv run pytest tests/ -q          # 期望 68 passed（76 - 8 硬删）
test ! -f src/knowledge_digest/recovery.py
! grep -rn "recovery\|copytree\|acquire_lock\|two_phase\|staged" src/knowledge_digest/
wc -l src/knowledge_digest/pipeline.py   # 期望 ≤ 350
```
- 手工冒烟：`digest` 跑一遍 fixtures，确认页面确实落到真 `kb_dir`（不是 tmp），`_archive/records.jsonl` 有记录
- 确认 `_update_claim_history` 只剩一处调用点（F2 的双调用契约收敛为单一路径）

**风险**：这是唯一的高风险批次。`audit_run` 原本 ~220 行、4 条写入退出路径内联，剥离时容易漏掉某条路径的产物写入。建议剥离后逐条比对 `report.json` 的键集合与 B1 之前一致（除 `recovery` 块外）。

---

### B2 — 修数据丢失 bug

**目标**
修掉三处 review 认定为 CRITICAL/HIGH 的真实丢失路径。

**做法**
1. **C1 claim-history.jsonl 全量重写 → append-only**（pipeline.py:325，`_update_claim_history` 内）
   现状 `write_jsonl(history_path, [*history, *new_records])` 是 truncate + 全量重写，一次写失败就是整份历史丢失。
   改为 O_APPEND 真追加：只追加 `new_records` + 独立的 supersede 标记行。读侧（264 行 `read_jsonl`）按 append 语义重建 active 索引 —— 后出现的 supersede 行覆盖先前状态。
2. **H5 pending-review.jsonl 无条件截断**（pipeline.py:326）
   现状只写本轮 pending，上一轮遗留条目被抹掉且无归档。改为与现有内容按 `(source_uri, fragment_locator)` 合并去重。
3. **C2 归档账本 records.jsonl 非原子**（writeback.py:269 → `provenance.append_jsonl` → `write_jsonl`）
   `append_jsonl` 实际是「读全量 + 写全量」。改为 O_APPEND 真追加。**这是「写前归档只增不删」方案的地基，优先级等同 C1。**
4. **H2 先覆盖后归档，顺序反了**（writeback.py:229-234）
   现状先循环写所有目标页，再循环写归档文件；归档阶段失败时原文已被覆盖。
   **改为：先落盘全部归档内容 → fsync 确认成功 → 再写目标页。** 这一条 + C2 就是替代 recovery 的「写前归档只增不删」本体。
5. **H1 OSError 逃逸**（writeback.py:235）：B1 已删回滚块，此项自然消失。改为不捕获（let it crash）—— 归档已在前，原文可从 `_archive/` 恢复。
6. **H3 delete 无内容备份**：随 recovery.py 删除而消失。确认新的归档路径覆盖了 delete 场景 —— 若 writeback 存在删除页面的分支，删除前必须先归档全文。

**涉及文件**
- `src/knowledge_digest/pipeline.py`（`_update_claim_history` 252-327）
- `src/knowledge_digest/writeback.py`（229-271）
- `src/knowledge_digest/provenance.py`（`append_jsonl`）
- `src/knowledge_digest/jsonl.py`（可能新增 `append_jsonl_line`）

**验收标准**
```bash
uv run pytest tests/ -q
uv run pytest tests/acceptance/ -q -k "history or pending or archive or rollback"
```
新增测试必须包含：
- 跑两轮 digest，断言 claim-history.jsonl 行数单调递增，第一轮的记录在第二轮后仍在文件里
- 上一轮 pending 条目在本轮源未失败时仍保留
- **归档先于覆盖**：monkeypatch 让目标页写入失败，断言 `_archive/` 里已有该页原文全文，且原文可从归档还原
- `records.jsonl` 并发/中断下不丢行（模拟写到一半）

**依赖**：B1（`_update_claim_history` 的双调用契约必须先收敛）

---

### B3 — 二次瘦身：死码与重复

**目标**
删掉当前 100% 空转的机制和重复实现，约省 450 行。

**做法**
1. **rethink 压单轮**（draft.py:528-585）
   `default_generator` 是恒等函数，第 2 轮必然与第 1 轮字节相同、559-563 立刻判 converged —— 这套多轮循环今天是死码路径。
   压成：调 generator 一次 → `_validate_candidate` → 不过就走 `faithfulness_check` fallback（draft.py:589 已有）。
   **保留 `_validate_candidate` 全部 5 条硬门和 fallback 分支**，只删循环控制与轮次记录。
2. **删签名自适配**（draft.py:321-336 `_invoke_generator`）
   `inspect.signature` 猜 1/2/3 参数形态是假通用性。固定为 `generator(context)`，签名不对就报错（let it crash）。删 `inspect` import。
3. **删 risk 规则引擎**（config.py:48-242）
   13 条阈值规则唯一产出是 `max_rounds ∈ {1,3}`；单轮化后这个数字不再被消费。删 `_STRUCTURED_LINE_PATTERNS`(48-53)、`_is_structured_line`、`_candidate_claim_count`、`_component_count`、`build_risk_signals`、`evaluate_risk`、`risk_decision` 及别名(239-241)，以及 `HIGH_RISK_MAX_ROUNDS` / `SINGLE_RISK_MAX_ROUNDS` 常量。
   连带删测试 `test_risk_rules_cover_boundaries_and_preserve_double_high_match`(test_phase2_rethink.py:103)。
4. **删 90 天清理**（provenance.py:196-266 `cleanup_expired_archives` + B1 后残留的调用点）
   归档改为只增不删。删对应测试（test_phase1_loss_prevention.py:195/207/216/229 四处）。
5. **收敛重复工具函数**
   - 新建 `src/knowledge_digest/text_similarity.py`，放 `_TOKEN_RE` / `_tokens` / `_similarity`（cluster.py:15,18-19,22-26 与 retrieve.py:14,17-18,21-25 逐字相同）。两边改为 import。
   - 4 份原子写：`recovery.py` 的 3 份随 B1 消失，`writeback._atomic_write` 成为唯一实现。B3 确认无残留即可。
   - 结构化行正则：`config.py:48` `_STRUCTURED_LINE_PATTERNS` 随 risk 引擎删除；若 `draft.py:17-20` 的 `_HEADING_RE/_FAQ_RE/_ERROR_RE/_PARAM_RE` 仍被拆页逻辑使用则保留在 draft.py（拆页是防丢失，不动）。

**涉及文件**
- `src/knowledge_digest/draft.py`（702 → ~420）
- `src/knowledge_digest/config.py`（308 → ~110）
- `src/knowledge_digest/provenance.py`（266 → ~190）
- `src/knowledge_digest/cluster.py` / `retrieve.py`（各减 ~12 行）
- 新增 `src/knowledge_digest/text_similarity.py`（~15 行）
- `tests/acceptance/test_phase2_rethink.py`、`test_phase1_loss_prevention.py`

**验收标准**
```bash
uv run pytest tests/ -q
! grep -rn "inspect\|max_rounds\|evaluate_risk\|risk_decision\|cleanup_expired" src/knowledge_digest/
grep -c "_similarity" src/knowledge_digest/cluster.py src/knowledge_digest/retrieve.py  # 各 1 处（import 后的调用）
wc -l src/knowledge_digest/*.py   # 合计目标 ≤ 2500
```
- **回归硬门**：`test_all_invalid_rounds_use_claim_fallback`(test_phase2_rethink.py:181) 必须仍然通过 —— 它验证「generator 产出无法溯源时回退逐条拼接」，是接 LLM 前最重要的防漂移测试

**依赖**：B1

---

### B4 — LLM 提炼生成器（本轮唯一创造价值的批次）

**目标**
把 `default_generator` 的恒等函数换成真实的 LLM 提炼，支持 OpenAI 兼容 + Anthropic 兼容两种 API 格式。这是设计文档 design:49 的核心承诺（「LLM 提炼合并」），目前一行都没实现。

**做法**
1. **新建 `src/knowledge_digest/llm.py`（目标 ≤ 150 行）**
   - 只用标准库 `urllib.request` + `json`（当前 pyproject 运行时依赖为**零**，不引入 httpx/openai/anthropic SDK，保持零依赖）
   - 两个格式适配：
     - OpenAI 兼容：`POST {base_url}/chat/completions`，header `Authorization: Bearer {key}`，body `{model, messages:[{role,content}]}`，取 `choices[0].message.content`
     - Anthropic 兼容：`POST {base_url}/v1/messages`，header `x-api-key: {key}` + `anthropic-version: 2023-06-01`，body `{model, max_tokens, messages}`，取 `content[0].text`
   - 环境变量：`KD_LLM_FORMAT`（`openai` | `anthropic`）、`KD_LLM_BASE_URL`、`KD_LLM_API_KEY`、`KD_LLM_MODEL`
   - **失败即报错退出**（拍板 3 + design:111）：非 2xx、超时、JSON 解析失败、缺 key 全部抛 `ValidationError`。**不做重试、不做降级、不做 fallback 到恒等函数** —— 静默降级回恒等函数会让「有没有真的提炼」变得不可观测，这正是当前问题的成因。
2. **结构化提炼 prompt**
   - 输入 context 已有：`items` / `source_text` / `initial_body` / `claims` / `old_target_body`（draft.py:536-545 构造）
   - 输出要求 JSON：`{"final_body": str, "claims": [{claim_fingerprint, text, source_uri, fragment_locator}], "coverage_mapping": {...}}`
   - prompt 中必须写死的约束（对应防丢失 9 条）：
     - 不得丢弃任何 claim，不得截断，不得因「问号结尾 / 纯字母数字 / 双语」等表面规则删行
     - 每条 claim 的 text 必须**逐字**出现在 final_body 中（这是 `_validate_candidate` 400-401 的硬门，prompt 里提前声明可大幅降低失败率）
     - 表格/代码块保持原结构，不得改写为散文
     - 保留决策动机(why)与版本历史类陈述
3. **忠实度校验接回**
   - 不新增校验逻辑 —— `_validate_candidate`（draft.py:374-406）的 5 条硬门原样生效，LLM 产出走同一条路
   - 校验不过 → `faithfulness_check` fallback（draft.py:589），落 `status` 到 report。**这条路径接 LLM 后从「理论分支」变成「真实高频分支」，B6 必须给它加断言**
4. **打通注入链（F3，改 4 个文件）**
   - `config.py`：`_CONFIG_KEYS` 白名单（21-31）加 provider 相关键；`DigestSettings`（39-45）加字段；新增环境变量读取（当前完全没有）
   - `draft.py`：`default_generator`（311-318）改为按配置构造真实 generator；`Generator` alias 保持
   - `pipeline.py`：675 / 709 两处 `draft()` 调用把 generator 传下去
   - `cli.py`：加 `--llm-format` / `--no-llm`（离线跑测试用）开关

**涉及文件**
- 新增 `src/knowledge_digest/llm.py`
- `src/knowledge_digest/draft.py`（default_generator 段）
- `src/knowledge_digest/config.py`（provider 配置 + env）
- `src/knowledge_digest/pipeline.py`（675/709 传参）
- `src/knowledge_digest/cli.py`
- 新增 `tests/acceptance/test_phase25_llm.py`

**验收标准**
```bash
uv run pytest tests/ -q                    # 全绿，且不发任何网络请求
uv run pytest tests/acceptance/test_phase25_llm.py -q
grep -c "import" src/knowledge_digest/llm.py    # 只有标准库
grep -rn "openai\|anthropic" pyproject.toml     # 零匹配（不加运行时依赖）
```
测试用 monkeypatch 替换 `urllib.request.urlopen`，必须覆盖：
- OpenAI 格式请求体/header 正确，响应正确解析
- Anthropic 格式请求体/header 正确，响应正确解析
- 缺 `KD_LLM_API_KEY` → ValidationError，**不静默降级**
- HTTP 500 / 超时 → ValidationError 退出，不重试
- LLM 返回丢了一条 claim → `_validate_candidate` 拒绝 → 走 fallback，且最终页面**不丢内容**（端到端断言到落盘 md）
- LLM 返回改写了 claim 文本（漂移）→ 400-401 硬门拒绝

**依赖**：B1。与 B3 有 `draft.py` / `config.py` 文件重叠，建议 B3 先合入。

---

### B5 — 真实脏文档 fixtures

**目标**
现有 10 个 fixture 最大 292 字节、全是理想化手写 markdown，「防丢失」结论全建立在「输入是规范 markdown」这个前提上。补真实脏样本。

**做法**
在 `tests/fixtures/phase0_digest/new_dir/items/` 下新增至少 5 个样本，覆盖 test-verification 报告点名的缺失特征：
1. `dirty-html-residue.md` — 残留 `<div>` / `&nbsp;` / `<br/>` / 全角空格 / BOM
2. `dirty-cjk-mixed.md` — 中英混排、CJK 标点、双语术语表、错误码与参数名
3. `dirty-malformed-frontmatter.md` — YAML 缺引号、tab 缩进、重复 key
4. `dirty-longline.md` — 单行 800+ 字符，含 URL 与代码片段
5. `dirty-deep-structure.md` — 嵌套列表、markdown 表格、h3/h4 深层标题、代码块

**涉及文件**：`tests/fixtures/phase0_digest/**`（纯新增，不改现有 fixture）

**验收标准**
```bash
uv run pytest tests/ -q          # 现有测试不受影响（纯新增文件）
uv run pytest tests/acceptance/ -q -k "dirty"
```
- 每个脏样本跑通 digest 全链路不崩
- **逐行核对**：按 phase1 `test_ac12_long_document_is_reorganized_without_loss`(306) 的写法，读 `(kb_dir/"pages").rglob("*.md")` 真实落盘内容，剥掉 Provenance 段后断言原文每一行都在
- 表格行、代码块行必须保持原结构（不被改写为散文）

**依赖**：无。**全程可与任何批次并行。**

---

### B6 — 测试补强 + 文档收口

**目标**
修掉空跑测试，补上 review 点名的 5 个覆盖缺口，更新文档状态表。

**做法**
1. **修空跑测试**（test-verification 第 2 节，已实证）
   `test_phase0_digest.py:494` `test_s5_atomic_failure_keeps_original_page_and_records_failed_write` 的 draft claim 只有 `text` + `source_uri`（523-529 行），在 writeback.py:176-183 的 provenance 前置校验就被拦下，`os.replace` 调用 **0 次** —— `pytest.raises(match="atomic write failed")` 匹配到的是 provenance 错误，不是真实写失败。第 534-535 行断言恒真。
   修法：补齐 claim 的 `claim_fingerprint` / `content_fingerprint` / `fragment_locator`，让流程真正走到 `_atomic_write`；**并在 monkeypatch 桩里加计数器断言 `os.replace` 确实被调用过**（防止再次退化为空跑）。
   注意：B1 删了回滚块、B2 改了归档顺序，这个测试要按新语义重写 —— 断言变成「写失败时原文完整保留在 `_archive/`」。
2. **补溯源内容对应性断言**（缺口 2/3）
   - `test_s6_provenance_audit_keeps_only_valid_final_sources`(437)：现状只查键存在 + 非空，把所有 source_uri 换成同一个合法 URI 也能通过。改为按 `fragment_locator` 行号回原文取行，与 `claim_body` 逐字比对。
   - `test_ac03_every_final_claim_has_replayable_lineage`(phase1:143)：现状只验 `startswith("lines:")` 前缀，「可重放」从未被重放。改为解析行号并真的回原文取该行断言相等。
3. **补 phase0 落盘断言**（缺口 4）
   `test_long_document_is_kept_complete_and_emits_split_suggestion`(678) 只查 `drafts.jsonl` 中间产物。改为读 `pages/**.md` 断言（照 phase1:315-319 写法）。
4. **补多页部分失败场景**（缺口 5，按 B1/B2 新语义）
   构造 2 页 draft，第 2 页写入失败，断言：第 1 页可能已被覆盖（接受半写，这是拍板 1），但**两页原文都完整存在于 `_archive/`**，且重跑能恢复。这条直接验证「写前归档只增不删」替代 recovery 是否成立。
5. **补 LLM fallback 覆盖**：B4 引入后 `faithfulness_check` fallback 从理论分支变高频分支，补端到端断言（fallback 时最终页面不丢内容）。
6. **更新 `docs/plans/` 状态表到真实进度**
   - `universal-knowledge-digest-design.md`：Phase 2 标为「已回退，按拍板 1 删除」；补一条记录说明 Phase 2 曾被无条件启用（本应是条件性的，design:200-203），触发条件从未满足
   - `phase0-implementation-spec.md`：状态对齐
   - 新增本文件的完成状态
   - **纠正「76 个验收测试」的表述**：其中 11 个是纯形状检查（只 `assert callable(...)` / `.exists()` / 查 --help 字符串），约 14% 不验证任何行为，文档里应标注
7. **开放问题**写入 `.omc/plans/open-questions.md`

**涉及文件**
- `tests/acceptance/test_phase0_digest.py`、`test_phase1_loss_prevention.py`、`test_phase2_rethink.py`
- `specs/archive/kd-phase0-2.5-plans/universal-knowledge-digest-design.md`、`phase0-implementation-spec.md`、`phase2.5-slim-and-llm.md`（收口后自 `docs/plans/` 迁入归档）
- `.omc/plans/open-questions.md` / `docs/plans/open-questions.md`

**验收标准**
```bash
uv run pytest tests/ -q                  # 全绿
uv run pytest tests/ -q -p no:randomly   # 顺序无关
! grep -rn "skip\|xfail\|\.only" tests/  # 无跳过
```
- **反空跑硬门**：全仓搜 monkeypatch 桩，每个桩必须有「被调用过」的计数断言
- 逐条核对 test-verification 第 4 节的 5 个缺口全部关闭
- 文档状态表与 `git log` / 实际代码一致

**依赖**：B1-B5 全部完成

---

## 4. 全局完成标准

```bash
uv run pytest tests/ -q                                    # 2026-07-27: 131 passed
wc -l src/knowledge_digest/*.py                            # 实测 ~3093（见下）
test ! -f src/knowledge_digest/recovery.py
! grep -E '\[project\.dependencies\]|^dependencies\s*=' pyproject.toml   # 运行时依赖仍为零
```

**行数说明**：原目标「≤2500 / ~2400」是删 recovery + B3 瘦身、**尚未计入** `llm.py`（~200）与单轮 rethink 审计字段时的估算。防丢失硬边界（ingest / draft 拆页 / provenance / writeback / faithfulness / kb_structure）合计仍约 1200+ 行不可砍。实测合计 **~3093**，相对基线 3867 净减 ~774（主要是删 recovery 694 + 其他收敛，再加回 LLM/锁/text_similarity）。本轮**不再为凑数字破坏拆页/硬门**；行数目标修订为「无 recovery、零运行时依赖、防丢失块不膨胀」。

| 标准 | 状态 |
|---|---|
| 代码瘦身（无 recovery；防丢失块未砍） | ✅ 3093 行；`recovery.py` 已删 |
| LLM 提炼真实生效（正向用例接受模型 body） | ✅ `test_phase25_llm.py` |
| 无 LLM 配置时不静默降级（缺 key / `--llm` 路径报错） | ✅ |
| 不再 copytree 整库 | ✅ |
| 原子写收敛到 `writeback._atomic_write`；相似度收敛到 `text_similarity` | ✅ |
| 防丢失 9 条硬约束仍成立 | ✅（B6 补强溯源回放/落盘/多页归档） |
| 文档状态表反映真实进度 | ✅（本文件 + design + phase0 状态头） |

---

## 5. 关键风险（3 条）

**R1 — B1 剥离 S5/S6 时漏掉写入路径（可能性中，影响高）**
`audit_run` 原有 ~220 行、4 条不同的写入退出路径内联，S5/S6 真身（pipeline.py:511-542）嵌在 copytree 克隆里。剥出来直写 kb_dir 时容易漏产物或改错 `_update_claim_history` 的 persist 双调用契约（F2）。
*缓解*：剥离前后逐条 diff `report.json` 的键集合（除 `recovery` 块）；B1 完成后确认 `_update_claim_history` 只剩一个调用点。

**R2 — 删回滚 + 删 recovery 后，防丢失出现真空窗口（可能性低，影响高）**
拍板 1 接受半写状态，前提是「原文在归档里」。但 B1 删回滚块和 B2 改归档顺序是两个批次 —— 如果 B1 合入而 B2 未完成，中间态既没有回滚也没有「先归档后覆盖」，比现状更差。
*缓解*：**B1 和 B2 必须同一轮合入，不可只发 B1**。或在 B1 内先把 writeback 的归档/覆盖顺序调正（H2），再删回滚块。

**R3 — 接入 LLM 后 `_validate_candidate` 硬门大量拒绝，全部走 fallback（可能性中，影响中）**
硬门要求每条 claim 的 text **逐字**出现在 `final_body`（draft.py:400-401）。真实 LLM 提炼几乎必然改写措辞 —— 结果是校验全不过、全走逐条拼接 fallback，等于绕了一圈还是恒等输出，「补 LLM」变成无效功。
*缓解*：B4 的 prompt 必须显式声明这条硬门；B4 验收里加「LLM 产出被接受」的正向用例（不只测拒绝路径）；若实测拒绝率过高，作为开放问题上报用户拍板（放宽为语义校验 vs 保持逐字），**不要自行放宽硬门** —— 那是当前唯一的防漂移防线。

---

## 6. 开放问题（同步写入 `.omc/plans/open-questions.md`）

- [ ] `_validate_candidate` 逐字硬门与 LLM 改写的冲突（R3）—— 若实测拒绝率高，是放宽为语义校验还是保持逐字？影响 LLM 提炼是否真正生效
- [ ] LLM 环境变量命名（`KD_LLM_*`）是否与用户其他工具冲突 —— 影响配置一致性
- [ ] 归档只增不删后的磁盘增长 —— 是否需要单独的 `kd-gc` 子命令（本轮删了 90 天清理）
- [ ] 11 个纯形状检查测试（约 14%）是保留还是替换为行为测试 —— 影响「76 个验收测试」这个数字的含金量
