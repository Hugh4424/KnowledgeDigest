# Build Plan: Phase 0 Knowledge Digest

## Goal

Implement the approved Phase 0 manual `digest(new_dir, kb_dir)` loop in a small Python package. The plan turns the spec into phase-by-phase work with exact proposed file paths, runnable checks, handoff knowledge, and STOP points.

## Minimal Path

Use one local Python package, Markdown files, JSONL stage products, queue Markdown files, and atomic file writes. Do not add scheduler/daemon/watch, graph database, complete dual-store productization, full source-attribution product, CAS, journal, two-phase commit, persistent retry queue, or a human-review product workflow.

## File List

| Path | Action | Purpose | Tasks |
|---|---|---|---|
| `pyproject.toml` | create | package metadata, console script, pytest config | T001, T010 |
| `src/knowledge_digest/__init__.py` | create | package marker/version | T001 |
| `src/knowledge_digest/cli.py` | create | `digest` CLI entry and exit-code handling | T001, T003 |
| `src/knowledge_digest/config.py` | create | default thresholds and optional config loading | T001 |
| `src/knowledge_digest/errors.py` | create | stage-aware user error types and stderr formatting | T001-T003 |
| `src/knowledge_digest/paths.py` | create | `new_dir`, `kb_dir`, run directory, and dry-run path resolution | T002, T003 |
| `src/knowledge_digest/kb_structure.py` | create | `kb.structure.md` parser and default roots | T002 |
| `src/knowledge_digest/jsonl.py` | create | JSONL read/write helpers | T004-T009 |
| `src/knowledge_digest/ingest.py` | create | S1 RawItem creation, dedupe, empty-shell filtering | T004 |
| `src/knowledge_digest/cluster.py` | create | S2 complete-linkage clustering and tiers | T005 |
| `src/knowledge_digest/queues.py` | create | needs_review / insufficient_signal queue writing | T005-T009 |
| `src/knowledge_digest/retrieve.py` | create | S3 top-k association and evolution decisions | T006 |
| `src/knowledge_digest/draft.py` | create | S4 draft, claim, unsupported claim, split suggestion outputs | T007 |
| `src/knowledge_digest/faithfulness.py` | create | claim support and fallback behavior | T007 |
| `src/knowledge_digest/writeback.py` | create | S5 temp file, fsync, atomic rename, archive/write-report | T008 |
| `src/knowledge_digest/provenance.py` | create | S6 provenance audit and final source enforcement | T009 |
| `src/knowledge_digest/pipeline.py` | create | S1-S6 orchestration for one manual run | T003-T009 |
| `tests/acceptance/test_phase0_digest.py` | create in T001, extend through T010 | phase-specific gates and final AC-001 through AC-011 acceptance assertions | T001-T010 |
| `tests/fixtures/phase0_digest/new_dir/items/filter-update.md` | create skeleton in T002, extend in T010 | revise sample input | T002, T010 |
| `tests/fixtures/phase0_digest/new_dir/items/chart-faq.md` | create skeleton in T002, extend in T010 | merge_multiple sample input | T002, T010 |
| `tests/fixtures/phase0_digest/new_dir/items/empty-shell.md` | create skeleton in T002, extend in T010 | empty-shell filtering sample | T002, T010 |
| `tests/fixtures/phase0_digest/new_dir/items/long-release.md` | create skeleton in T002, extend in T010 | split suggestion sample | T002, T010 |
| `tests/fixtures/phase0_digest/new_dir/sources.jsonl` | create skeleton in T002, extend in T010 | source manifest sample | T002, T010 |
| `tests/fixtures/phase0_digest/kb_dir/kb.structure.md` | create skeleton in T002, extend in T010 | KB structure sample | T002, T010 |
| `tests/fixtures/phase0_digest/kb_dir/pages/goinsight/filtering.md` | create skeleton in T002, extend in T010 | revise target page | T002, T010 |
| `tests/fixtures/phase0_digest/kb_dir/pages/goinsight/chart-types.md` | create skeleton in T002, extend in T010 | merge target page | T002, T010 |
| `docs/plans/phase0-implementation-spec.md` | modify | add final implementation-plan reference after approval | T011 |
| `specs/kd-phase0-digest-spec/plan.md` | create/modify | build-plan artifact | build-plan |
| `specs/kd-phase0-digest-spec/tasks.md` | create/modify | task list artifact | build-plan |
| `specs/kd-phase0-digest-spec/data-contracts.md` | create/modify | data contract artifact | build-plan |
| `specs/kd-phase0-digest-spec/research.md` | create/modify | research artifact | build-plan |

## Phase 1: CLI, config, and filesystem contracts

### Goal

A user can invoke `digest(new_dir, kb_dir)`; the program validates required inputs, parses defaults/config, creates a run directory, and fails with documented exit code/stderr before changing formal KB files. Done means AC-001 and AC-002 pass for legal run skeleton and three missing-input cases.

### Files

- `pyproject.toml`
- `src/knowledge_digest/__init__.py`
- `src/knowledge_digest/cli.py`
- `src/knowledge_digest/config.py`
- `src/knowledge_digest/errors.py`
- `src/knowledge_digest/paths.py`
- `src/knowledge_digest/kb_structure.py`
- `src/knowledge_digest/pipeline.py`
- `tests/acceptance/test_phase0_digest.py` (created in T001; extended by T004-T010)

### Tasks

- T001: CLI entry, required/optional args, defaults, exit-code/stderr mapping, and the initial `tests/acceptance/test_phase0_digest.py` gate skeleton used by later phase gates.
- T002: `new_dir`, `kb_dir`, `kb.structure.md` validation, and minimal fixture skeletons required by Phase 1 gate commands.
- T003: run directory/report skeleton and dry-run no-formal-KB-change guard.

### Verify

- gate_cmd: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "cli_contract or missing_inputs or dry_run_contract"`
- display_cmd: `python -m knowledge_digest.cli --help`
- pass/fail: gate_cmd exit code 0 is pass; any non-zero exit is fail. display_cmd is informational only.

### Knowledge

Record stderr examples, created run directory path, and dry-run no-change evidence in `tasks/kd-phase0-digest-spec/progress.md` under “Phase 1 evidence”.

### STOP

STOP after Phase 1 until the gate_cmd passes and the evidence section is written. No human approval is required for this internal implementation phase; build-plan’s Step 9 human approval remains the only stage-level approval.

## Phase 2: S1-S4 processing pipeline

### Goal

The run converts inputs into RawItems, clusters them without weak-chain merges, chooses evolution paths with top-k candidates, and emits safe drafts with unsupported claims removed or queued. Done means AC-003 through AC-006 and AC-010 pass.

### Files

- `src/knowledge_digest/jsonl.py`
- `src/knowledge_digest/ingest.py`
- `src/knowledge_digest/cluster.py`
- `src/knowledge_digest/queues.py`
- `src/knowledge_digest/retrieve.py`
- `src/knowledge_digest/draft.py`
- `src/knowledge_digest/faithfulness.py`
- `src/knowledge_digest/pipeline.py`
- `tests/acceptance/test_phase0_digest.py`
- all files under `tests/fixtures/phase0_digest/new_dir/` (skeleton created in T002; scenario content extended by T004-T010)

### Tasks

- T004: S1 ingest, exact dedupe, empty-shell filtering, RawItem/duplicates/ingest-failed outputs.
- T005: S2 complete-linkage clustering, tiering, queue writes, model-failure handling.
- T006: S3 top-k retrieval and `new`/`revise`/`merge_multiple` decision records.
- T007: S4 drafts, claims, unsupported claims, removed claims, faithfulness fallback, split suggestions.

### Verify

- gate_cmd: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "s1 or s2 or s3 or s4 or split_suggestion"`
- display_cmd: `find /tmp/knowledge-digest-acceptance -path "*/_digest/runs/*" -maxdepth 5 -type f | sort`
- pass/fail: gate_cmd exit code 0 is pass; any non-zero exit is fail. display_cmd is informational only and must not override gate_cmd.

### Knowledge

Record sample output counts for `raw-items.jsonl`, `duplicates.jsonl`, `ingest-failed.jsonl`, `clusters.jsonl`, `evolution-decisions.jsonl`, `drafts.jsonl`, `unsupported-claims.jsonl`, and `split-suggestions.jsonl` in `tasks/kd-phase0-digest-spec/progress.md` under “Phase 2 evidence”.

### STOP

STOP after Phase 2 until gate_cmd passes and Phase 2 evidence is written. Do not proceed to writeback while S4 can still emit unsupported claims into final bodies.

## Phase 3: Atomic writeback, provenance, and acceptance fixture

### Goal

The run writes or plans formal KB changes without partial writes, enforces valid provenance for every final claim, preserves old information correctly, and proves the constructible sample covers all acceptance criteria. Done means AC-001 through AC-011 all pass.

### Files

- `src/knowledge_digest/writeback.py`
- `src/knowledge_digest/provenance.py`
- `src/knowledge_digest/pipeline.py`
- `tests/acceptance/test_phase0_digest.py`
- all files under `tests/fixtures/phase0_digest/kb_dir/` (skeleton created in T002; final scenario content extended by T010)
- `docs/plans/phase0-implementation-spec.md`

### Tasks

- T008: S5 temp-file/fsync/atomic-rename writeback, archive behavior, write-report, dry-run planned changes.
- T009: S6 provenance audit and final claim source enforcement.
- T010: Complete the constructible acceptance fixture and full-suite assertions; test file and minimal fixture skeleton already exist before T001-T009 gates run.
- T011: Documentation update linking final implementation plan and sample checks after build-plan human approval.

### Verify

- gate_cmd: `python -m pytest tests/acceptance/test_phase0_digest.py -q`
- display_cmd: `python -m knowledge_digest.cli tests/fixtures/phase0_digest/new_dir tests/fixtures/phase0_digest/kb_dir --dry-run`
- pass/fail: full acceptance pytest exit code 0 is pass; any non-zero exit is fail. display_cmd is informational only and must not mutate fixture KB.

### Knowledge

Record final run report path, write-report summary, provenance-audit summary, dry-run no-change evidence, and AC-011 forbidden-scope grep evidence in `tasks/kd-phase0-digest-spec/progress.md` under “Phase 3 evidence”.

### STOP

STOP after Phase 3 until full acceptance gate_cmd passes, evidence is written, and code review/verify-code stages run. This phase does not auto-close the parent workflow.

## Business Impact Coverage

| Spec impact item | Task | File path | Verify |
|---|---|---|---|
| revise preserves still-valid old claims and sources | T007, T008 | `src/knowledge_digest/draft.py`, `src/knowledge_digest/writeback.py` | pytest assertion in `test_phase0_digest.py` checks old supported claim remains after revise |
| merge_multiple can affect multiple pages and records reason | T006, T010 | `src/knowledge_digest/retrieve.py`, fixture chart/filter pages | pytest checks multiple target_paths and reason in `evolution-decisions.jsonl` |
| queue visibility without review product workflow | T005, T007, T009 | `src/knowledge_digest/queues.py` | pytest checks `_queues/needs_review.md` and `_queues/insufficient_signal.md` entries |
| archive visibility for removed content | T008 | `src/knowledge_digest/writeback.py` | pytest checks archive path or removed_claims contains reason and snapshot |
| empty-shell source never pollutes final provenance | T004, T009 | `src/knowledge_digest/ingest.py`, `src/knowledge_digest/provenance.py` | pytest checks empty-shell source final reference count is 0 |
| dry-run does not modify formal KB | T003, T008 | `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/writeback.py` | pytest snapshots pages/archive/queues before and after dry-run |
| failure rerun recomputes from files, no persistent retry queue | T003, T008 | `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/writeback.py` | pytest simulates failure, reruns, and verifies no retry queue file is required |
| long documents are not truncated | T007, T010 | `src/knowledge_digest/draft.py`, `long-release.md` fixture | pytest compares RawItem line count and split suggestion, no truncation |
| manual spot-check classes remain traceable | T004, T007, T009, T010 | fixtures and provenance module | pytest checks FAQ, error code, parameter, URL, bilingual term, design link traceability |

## Standards

### Delivery Standards

- Each phase must have its gate_cmd pass before the next phase starts.
- Done evidence must be written to `tasks/kd-phase0-digest-spec/progress.md`.
- Stage-level build-plan completion still requires Step 9 human confirmation before stage-result.

### Exception Standards

- Missing `new_dir`, missing `kb_dir`, or missing `kb.structure.md` returns exit code 1 and does not modify formal KB files.
- External model/embedding failure returns exit code 2 or queues the current cluster only where the spec allows continuation.
- Faithfulness failure removes unsupported claims or falls back; if no safe draft remains, exit code 3.
- Write failure returns exit code 4 and leaves official pages old-or-new, never half-written.
- Optional index sync failure returns exit code 5.

### Test Standards

| Phase | gate_cmd | display_cmd |
|---|---|---|
| Phase 1 | `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "cli_contract or missing_inputs or dry_run_contract"` | `python -m knowledge_digest.cli --help` |
| Phase 2 | `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "s1 or s2 or s3 or s4 or split_suggestion"` | `find /tmp/knowledge-digest-acceptance -path "*/_digest/runs/*" -maxdepth 5 -type f \| sort` |
| Phase 3 | `python -m pytest tests/acceptance/test_phase0_digest.py -q` | `python -m knowledge_digest.cli tests/fixtures/phase0_digest/new_dir tests/fixtures/phase0_digest/kb_dir --dry-run` |

### Code Standards

- Follow repository AGENTS.md instructions and any future project-local style rules.
- Use existing lint/type/test tools once `pyproject.toml` defines them; lint errors are hard failures for verify-code.
- Keep file I/O explicit and testable; no hidden background daemon, scheduler, database, CAS, journal, or persistent retry queue.
- Do not introduce a second source of truth for KB structure beyond `kb.structure.md` and parsed defaults.

## Acceptance Mapping

| AC | Covered by tasks | gate_cmd assertion |
|---|---|---|
| AC-001 | T001, T003, T010 | full acceptance run produces exactly one run report |
| AC-002 | T001, T002, T010 | three missing-input cases exit 1 and do not modify formal KB |
| AC-003 | T004, T010 | S1 counts raw/duplicate/ingest-failed and zero empty-shell S2 entries |
| AC-004 | T005, T010 | every cluster has tier and decision_reason; low confidence queues exist |
| AC-005 | T006, T010 | S3 preserves up to top_k candidates and records action/reason |
| AC-006 | T007, T010 | unsupported claims do not enter final body |
| AC-007 | T008, T010 | write failure leaves formal page old-or-new and write-report records status |
| AC-008 | T009, T010 | every final claim has at least one valid source_uri |
| AC-009 | T004, T007, T009, T010 | six info classes remain traceable |
| AC-010 | T007, T010 | long-release has split suggestion and no truncation |
| AC-011 | T001-T011 | grep/assertions find no scheduler, graph DB, dual-store productization, heavy transaction system, persistent retry queue, or review product workflow requirement |

## Constitution Check

- [x] **F1 薄核心** — 判据：计划只要求手动 CLI 和 S1-S6 文件级处理，未引入调度核心或平台化编排。
- [x] **F2 窄契约** — 判据：跨边界契约固定为 CLI 参数、目录结构、JSONL 字段和 Markdown 队列。
- [x] **F3 物理事实靠机器校验但不阻断** — 判据：plan/tasks/analysis 和 baseline 只记录事实；非阻断项不改变 stage 推进。
- [x] **F4 质量靠异源审查与人而非阻断式质量门** — 判据：Step 8 记录独立审查，Step 9 交给人确认，不用自建质量门替代人。
- [x] **F5 gate 谨慎添加出事再补无用则移除** — 判据：仅保留 spec 要求的输入校验、faithfulness、原子写回和人工确认，不新增通用 gate 平台。
- [x] **F6 统一外置执行记录** — 判据：stage 产物、review、metrics 和 future stage-result 都落在 task record/worktree 约定路径。
- [x] **F7 推进与不可逆操作不自动越过人** — 判据：Step 9 是硬门；未获继续确认前不写 stage-result、不提交完成状态。
- [x] **F8 简单优先** — 判据：采用文件夹、Markdown、JSONL、原子 rename；明确排除图数据库、CAS、journal 和持久队列。
- [x] **F9 可证伪不假绿** — 判据：baseline 不可得项写 unknown；review 不可跑时写 unavailable，不伪造 pass。
- [x] **F10 自动化按真实收益添加，不为机器可校验本身堆基建** — 判据：新增机制都对应已观察的信息丢失或半写风险；未添加额外 CI/gate/schema 平台。
- [x] **Q1 记事实而非阻断** — 判据：constitution 和 baseline 只入计划事实，不阻断成功。
- [x] **Q2 gate 三类划分** — 判据：输入校验是入口校验，baseline/analysis 是记录采集，Step 9 是人工确认。
- [x] **Q3 异源审查加人工把关** — 判据：计划包含独立审查记录和人工确认块，不自审自放行。
- [x] **S1 能用外部就不造轮子** — 判据：计划复用文件系统、Markdown、JSONL、OpenAI-compatible 配置，不造图谱/数据库框架。
- [x] **S2 外部技能可针对项目改造合宪** — 判据：只消费 workflowhub build-plan/spec-plan/task 约定产物，不改技能本体。
- [x] **S3 迭代时保持最新并就地检查** — 判据：本阶段读取当前 SKILL.md 和当前 upstream spec/decision-log 后生成。
- [x] **S4 自定义技能必须有指标系统** — 判据：stage 启动写入 metrics skeleton，完成后待 Step 9 放行再 updateOwnResult。
- [x] **S5 自定义技能方便子代理调用省主上下文** — 判据：后续开发任务按 Stage 1-3 和具体文件契约拆分，可交给子代理实现。
- [x] **S6 自定义技能参考市面方案不闭门造车** — 判据：计划沿用 spec 中 complete-linkage、faithfulness、atomic rename 等成熟实践。
- [x] **S7 一阶段一技能一工作流一文件夹** — 判据：build-plan 产物集中在 `specs/kd-phase0-digest-spec/` 与 task artifacts。
- [x] **S8 自定义技能可独立调用可搬运** — 判据：产物以 Markdown/JSONL 路径契约描述，不绑定某个运行时服务。


## M10 Baseline Comparison

| 指标名 | M12 实值 | M10 baseline | delta |
|---|---|---|---|
| missed_step_rate | unknown（仅 upstream make-decision/build-spec 两段已完成且已落盘，全五段值待 verify-code 完成后才可计算） | 0.05 | unknown |
| test_execution_rate | unknown（build-plan 阶段无测试执行数据，待 build-code/verify-code） | 0.8295 | unknown |
| review_execution_rate | unknown（review 阶段尚未执行） | 1 | unknown |
| rework_rounds | unknown（全流程未完成，无返工数据） | 6.075 | unknown |
| rework_proxy_count | unknown（全流程未完成，无代理返工数据） | 25.25 | unknown |


## F10 Gate

| Proposed mechanism | Real threat | Existing coverage | Bypass check | Maintenance cost | Decision |
|---|---|---|---|---|---|
| Required CLI path and config validation | Missing dirs or malformed thresholds can create confusing partial runs. | Spec defines exit code 1 and stderr requirements. | Parser rejects before S1. | Low. | Keep. |
| Empty-shell filtering in S1 | Empty crawl pages pollute clusters and final provenance. | FR-STRUCTURE-001 / FR-BEHAV-001. | Acceptance fixture checks zero final references. | Low. | Keep. |
| Complete-linkage clustering thresholds | Weak-chain similarity can merge unrelated material. | FR-STRUCTURE-002. | min_pair_similarity and decision_reason are recorded. | Medium, bounded to S2. | Keep. |
| Claim-level verify and faithfulness fallback | LLM may synthesize unsupported claims. | FR-STRUCTURE-004. | unsupported-claims and drafts can be asserted. | Medium, justified. | Keep. |
| Temp file + fsync + atomic rename | Write interruption can corrupt knowledge pages. | FR-STRUCTURE-005. | write-report and page snapshot assert old-or-new. | Low. | Keep. |
| Queue files | Low-confidence material otherwise disappears. | FR-STRUCTURE-002/003/004/006. | queue files are observable. | Low. | Keep. |
| Scheduler, graph DB, CAS, journal, persistent retry queue | none in Phase 0 | Out Of Scope forbids them. | Adds unused infrastructure. | High and ongoing. | Exclude. |

F10 result: plan/tasks contain no new mechanism beyond the spec-required validation, queue, faithfulness, provenance, acceptance, and atomic write behaviors. No post-F10 removal required. Review round 2 changed only task ordering for test skeleton creation; it did not add scope or new mechanisms.

