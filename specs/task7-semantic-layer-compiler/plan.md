# 实现计划：task7 语义层页面编译器（K1）

- **Input**：`specs/task7-semantic-layer-compiler/decision-log.md`（approved 2026-09-13）、`specs/task7-semantic-layer-compiler/spec.md`（build-spec 冻结 d495816e…）
- **Template version**：`plan-task.v4`

## 材料导航

| 章节 / 材料锚点 | 职责与摘要 | M/S/B/P 读取时机 |
| --- | --- | --- |
| `decision-log.md#已选方向` / `#验收标准` | 已确认方向、18 条 D 决定、AC-01…13 原始口径 | M：计划与验收对齐时逐条读 |
| `spec.md#5 功能需求` / `#11 验收标准` | 20 条 FR 行为契约与 13 张四段 AC 卡 | M：任务卡 FR/AC 绑定 |
| `plan.md#Technical Decisions` / `#Phase P1…P7` | 工程方案、文件边界、依赖与回滚 | S：执行前速读；B：跨 Phase 回查 |
| `tasks.md#Phase P1…P7` | 15 张任务卡、命令、oracle、完成区 | B：build-code 逐卡执行 |

## Quick Read

- **Goal**：`digest` 一次运行把 89 份冻结 Confluence Markdown 编译成一个 KD测试 批次目录——保真拆块、确定性归组、同构页面、五件机读审计；同输入连跑两次字节一致。
- **Non-goals**：不做入口导航/发布回滚/删码/查询集验收/向量库（来源：decision-log NG-003…NG-007，D-001/D-014）；不改 CompanyBrain/gbrain/停摆流水线（NG-008）；分批恢复本卡不激活（D-013）。
- **Before**：`digest` 走旧 reader 路径（固定 240 行窗口拆块、改写文本），89 份语料的参考型内容大面积丢失；基线测试 16 failed / 892 passed / 3 skipped（失败分布：15×test_task2a_reader_bundle + 1×test_task0_runtime_audit，根因均为仓库外证据文件缺失，实测清单见 Technical Context）。
- **After**：`digest` 默认执行新的语义编译行为；旧行为完整保留在 `scripts/legacy_digest_reference.py` 可独立运行；新链路自带逐字节保真审计与机读批次状态。
- **Main risk**：模型不可用时新主题的英文 slug 生成回退链不完整会导致页面无法落盘——已设计确定性回退（文件名 ASCII 段提取），仍失败则显式阻塞。
- **Next step**：T001（RED：拆块边界与整块聚合测试）。
- **来源**：decision-log R-009…R-041；spec FR-SRC/BLK/GRP/CMP/PUB/AUD/CLI/REG-001…。

## Technical Context

### Global Constraints

- **Verified facts**：冻结语料 89 份（4 顶层目录、无更深嵌套、无宏 XML）；冻结清单 `config/task4-source-coverage-89-input.v1.json`（条目字段 `source_uri/source_id/content_hash/byte_count`）；task5 台账 `expected_status` 分布 present=88 / empty=1（正好充当 known_empty fixture 依据）；gbrain slug 规则删非 ASCII 且同 slug 覆盖；基线 911 个测试收集（`--collect-only` 实测），16 个失败节点已实测冻结，精确清单（AC-10/OPEN-010 基线）：
  1. `tests/acceptance/test_task0_runtime_audit.py::test_runtime_audit_records_frozen_calibration_hash`（根因：根目录 `evidence/phase4/calibration-artifact.json` 缺失）
  2. `tests/acceptance/test_task2a_reader_bundle.py::test_full_fixture_emits_positive_trust_signals_and_audit_evidence`
  3. `tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_fail_closed_after_content_or_event_mutation`
  4. `tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[source_fingerprint]`
  5. `tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[locator]`
  6. `tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[target_path]`
  7. `tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[page_type]`
  8. `tests/acceptance/test_task2a_reader_bundle.py::test_validator_reconciles_frontmatter_and_audit_without_input_context`
  9. `tests/acceptance/test_task2a_reader_bundle.py::test_entry_coverage_mismatch_fails_closed`
  10. `tests/acceptance/test_task2a_reader_bundle.py::test_entry_producer_missing_fails_closed`
  11. `tests/acceptance/test_task2a_reader_bundle.py::test_changed_fixture_provenance_fails_closed_before_publishing`
  12. `tests/acceptance/test_task2a_reader_bundle.py::test_malformed_fixture_selection_without_sample_id_is_structured`（×2 重复节点，pytest 去重按 1 计）
  13. `tests/acceptance/test_task2a_reader_bundle.py::test_malformed_fixture_selection_without_selection_reason_is_structured`
  14. `tests/acceptance/test_task2a_reader_bundle.py::test_real_selected_fixtures_close_footnote_to_claim_and_replay`
  15. `tests/acceptance/test_task2a_reader_bundle.py::test_validator_rejects_bundle_symlinks_and_non_allowlisted_files`
  16. `tests/acceptance/test_task2a_reader_bundle.py::test_validator_rejects_incomplete_claim_provenance`
  根因（实测）：15 个共用 `quality/evidence/task2-entry/` 目录缺失，1 个为上述 calibration-artifact 缺失；非代码回归。**测量修正登记**：spec PFACT-008 写「16 个失败全部挂在 test_task2a_reader_bundle」，按实测应为 15+1；本清单为权威测量事实，spec 文本的分布表述在 spec-owner 下次修订时同步（差异只涉分布不涉 AC-10 判定口径）。
- **Language / runtime**：Python ≥3.11（pyproject.toml:9）；唯一运行时依赖 PyYAML 6.0.2（pyproject.toml:10）；测试 pytest≥8 dev 组。
- **Primary dependencies**：`compiler.py` 的 `_paragraph_evidence`（2945-2991，字节不改写拆块）与 `_formal_raw_coordinate_map`（1717-1782，块级指纹）；`draft.py` 的 `normalize_structure`（96 起，标题树 + `lines:N-M` 定位）；`llm.py` provider seam（模型调用）；`task5_runtime.py:176-204` 的 Downloads 子目录校验先例。
- **Storage / state**：批次目录 = `/Users/Hugh/Downloads/KD测试/<YYYY-MM-DD>-<n>/`（每次尝试新建，含失败骨架）；模型缓存 = 仓库内 `cache/model-cache/`（任务级固定位置，`.gitignore` 忽略，不随批次目录销毁）；语料根只读。
- **Testing**：`uv run --frozen pytest -q`（48.72s 基线实测）；无 conftest.py，fixture 内联于各测试文件；89 语料合成 fixture 在 `tests/fixtures/task1_topic_axis_89/`（new_dir/items 恰好 89 份）。
- **Target environment**：本机 macOS CLI；产物供 Obsidian 读者与 gbrain 下游消费（后者 DEF-002 未验证）。
- **Unresolved facts**：模型 provider 具体可用性属运行时事实（SCN-007 矩阵已覆盖不可用路径）；`emm for android ` 目录尾随空格在相对路径中的保留形态由 P2 归一化 fixture 固定。

## Code Anchors

- **Verified anchors**：`src/knowledge_digest/compiler.py:2945` `_paragraph_evidence`（标题/列表/表格行/代码块各自成块、字节不改写；表格按行拆需聚合）；`compiler.py:1717` `_formal_raw_coordinate_map`（`block_content_sha256` + 行列坐标，非重叠校验）；`draft.py:96` `normalize_structure`（heading_level/parent_locator/fragment_locator）；`reader_compiler.py:441` `_split_chunks` + `:26` `PART_BODY_LINES=240` 与 `:157/:221` 改写函数（绕行对象）；`simple_cli.py:67` main（默认分支 218-242 调 `compiler.digest`，`:151-156` 离线分支）。
- **Existing interfaces**：`_paragraph_evidence(lines, source_id) -> list[dict]`（evidence_id/source_id/start_line/end_line/text/status）；`normalize_structure(raw_items) -> list[dict]`（fragment_id/content_type/heading_level/parent_locator/fragment_locator）。
- **Read now**：上述五个锚点 + `pyproject.toml:13`（digest 注册）+ `config/task4-source-coverage-89-input.v1.json` 首条 entry。
- **Must read before task**：`llm.py` provider seam（P5 前）；`task5_runtime.py:148-204`（P7 批次目录校验先例）；`tests/acceptance/test_task2a_reader_bundle.py` 的 subprocess CLI 测试形态（P7 改挂参考）。
- **Context mode**：Lite（锚点已实测，重读量小）。

### Reuse → Extend → New

| Capability | Decision | Existing anchor | Reason / removal condition |
| --- | --- | --- | --- |
| 保真拆块基底 | extend | `compiler.py:2945 _paragraph_evidence` + `draft.py:96 normalize_structure` | 复用字节不改写语义；追加连续表格行聚合与 FR-BLK-001 分类优先级（原实现按行拆表，不可原样用） |
| 块级指纹 | reuse | `compiler.py:1717 _formal_raw_coordinate_map` 的 sha256 约定 | 直接采用其 block_content_sha256 口径，避免第二套指纹 |
| 模型调用 | extend | `llm.py` provider seam | 复用 Qwen 客户端与凭据读取约定；外包裹 semantic_cache 冻结层 |
| 模型缓存 | new | 无 | 无既有任务级跨运行缓存；consumer=semantic_compiler；owner=build-code；测试=test_task7_cache.py；K4 删旧码时可一并移除 |
| 批次目录校验 | reuse | `task5_runtime.py:176-204 _validate_output_target` 的形态 | 借鉴 Downloads 直接子目录强制，不 import（属 task5 运行时） |
| 语义编译编排/归组/claim/页面/审计 | new | 无（旧路径全部绕行） | 保真+同构+审计是新链路，旧模块无任一满足；consumer=semantic_cli；删除条件=K4 旧码清理时评估 |

## Solution Design

### Overview

新链路是一条单向管道：`semantic_cli`（digest 新入口）→ `semantic_compiler`（编排：对账→拆块→归组→编译→校验→写入）→ 六个专项模块。拆块复用 `_paragraph_evidence` 后再聚合表格行并分类，块携带 heading_path；归组按 spec 的归一化规则在 product 作用域内分组；claim 管道把叙述切片打成句子级 claim 并生成稳定 `claim_id`；模型只经 `semantic_cache` 接触（键 = 模型标识 + 提示模板版本 + 主题映射版本 + 页面复合输入指纹，每主题单次复合调用产标题/导读/slug 候选）；页面渲染 16 字段 frontmatter、英文 slug（缓存主路径 + 文件名 ASCII 段回退）、双链与分页；审计层落五件 `_audit/` 并推五类状态。旧 `digest` 默认分支改派新链路，旧行为整体迁至 `scripts/legacy_digest_reference.py`，旧模块全部不删不改（K4 边界）。

数据流：语料目录 + 冻结清单 → 对账（差异→骨架批次+blocked）→ 每源拆块（块带 source_path/content_hash/line_range/kind）→ 第二方法扫描交叉验证 → 标题名归组（+显式主题映射）→ 逐主题组编译（参考块逐字入页；叙述 claim 逐条带出处；模型产标题/导读/同义建议走缓存）→ 结构校验（16 字段/slug 唯一/双链/300 行）→ 写批次目录 + manifest 最后落盘。失败语义：任何阶段失败按 D-008 进阻塞清单，批次状态机读，不伪装完成。

### Module responsibilities

#### semantic_split

- **Responsibility**：整块单元拆块、FR-BLK-001 边界与分类优先级、坏行归属、独立第二方法扫描器
- **Consumes**：源文件行序列、`draft.normalize_structure` 输出
- **Produces**：`Block(source_path, block_id, content_hash, kind, line_start, line_end, text, heading_path)` 全集 + 第二方法比对报告
- **Must not decide**：页面归属与主题分组（归 group）；叙述切句（归 claims）

#### semantic_group

- **Responsibility**：标题名归一化、product 作用域分组、显式主题映射应用（含 `audit_only_sources` 声明读取）、疑似同义建议输出
- **Consumes**：Block 流（含 heading_path）、`config/task7-topic-map.json`
- **Produces**：`TopicGroup(key, product, module_anchor, members)` 列表
- **Must not decide**：缓存键构成（归 cache）；页面文件名（归 page）

#### semantic_claims

- **Responsibility**：句子级 claim 切分、稳定 claim_id、span 映射、导读逐句回溯与留空规则
- **Consumes**：叙述块、导读模型候选、原文行
- **Produces**：`Claim(record…)` 全集（含 status=原文未明确 的被拒导读句）
- **Must not decide**：旁路文件落盘格式（归 audit）

#### semantic_page

- **Responsibility**：frontmatter 16 字段、英文 slug（含回退与批内唯一）、`[[wikilink]]` 相关页面、300 行分页与 oversized 附录 part、读者侧出处行、附件标注
- **Consumes**：TopicGroup、Claim、Block、模型标题/导读（经 cache）
- **Produces**：页面字节 + 页面清单条目
- **Must not decide**：批次状态与审计字段（归 audit）

#### semantic_cache

- **Responsibility**：模型结果冻结、复合键、miss→call→write-back、任务级持久化
- **Consumes**：provider client（llm.py seam）、键材料（成员指纹/主题键/版本）
- **Produces**：标题/导读/同义建议/slug 候选的确定性结果
- **Must not decide**：provider 不可用时的产品语义（归 compiler 的 SCN-007 矩阵执行）

#### semantic_audit

- **Responsibility**：五件 `_audit/` 产物、五类状态推导、覆盖不变量校验、阻塞清单、批次状态、成本记账
- **Consumes**：全管道事实
- **Produces**：reference-blocks.jsonl / sources.jsonl / page-manifest.json / run-metrics.json / suspected-synonyms.md
- **Must not decide**：页面内容（归 page）

#### semantic_compiler / semantic_cli

- **Responsibility**：编排与 digest 入口、预检计划打印、SCN-007 降级矩阵、骨架批次、退出码
- **Consumes**：上述全部模块
- **Produces**：批次目录 + 退出码（0=complete；1=blocked/interrupted）
- **Must not decide**：任何产品行为语义（全部在 spec）

### Interfaces, data, and lifecycle

- **Interfaces / schemas**：Block/Claim/TopicGroup 为进程内 dataclass；Block 携带 `heading_path`（标题栈，semantic_split 从 draft.py 标题树填充，semantic_group 据其取公共 H2 祖先定 module）；审计文件 schema 以 spec FR-AUD-001/002/004 的字段清单为准（JSONL + 单 JSON）；缓存条目为 JSONL（`{"cache_key","model_id","prompt_version","topic_map_version","result","created_from_fingerprint"}`）；显式主题映射 `config/task7-topic-map.json` 含 `topic_aliases` 与 `audit_only_sources` 两个键（初始均空），audit_only 声明输入 = 该文件 `audit_only_sources` 列表 ∪ task5 `source_snapshot.expected_status == "audit_only"` 的来源（当前分布无该值，机制为 fixture 与未来语料备好）。
- **Data flow / state**：无跨进程状态；manifest 最后落盘；中断 = 半成品 + `run_status=interrupted|blocked`；缓存与批次目录生命周期无关。
- **API contract**：无网络接口；CLI 面 = `digest <语料目录> [--manifest <对账清单路径>]`，`--manifest` 默认 `config/task4-source-coverage-89-input.v1.json`，fixture 语料在测试中传入配套小清单（T013）。
- **UI / external code**：N/A — non_ui。
- **Fail-loud behavior**：对账差异、slug 回退失败、结构校验失败、模型不可用且无缓存（按矩阵降级或阻塞）全部显式落阻塞清单；audit_only 声明核验冲突（声明块入 products，或未声明而块零入 products）同样进阻塞清单；任何字段缺失拒绝写「完成」。

## UI Delivery Contract (仅 UI phase/task 使用)

N/A — 本任务 `ui_applicability=non_ui`（decision-log UI applicability 三来源一致），无浏览器界面/路由/交互组件；不产生 UI contract facts。

## File Boundary

### NEW

- `src/knowledge_digest/semantic_split.py`
- `src/knowledge_digest/semantic_group.py`
- `src/knowledge_digest/semantic_claims.py`
- `src/knowledge_digest/semantic_page.py`
- `src/knowledge_digest/semantic_cache.py`
- `src/knowledge_digest/semantic_audit.py`
- `src/knowledge_digest/semantic_compiler.py`
- `src/knowledge_digest/semantic_cli.py`
- `scripts/legacy_digest_reference.py`
- `config/task7-topic-map.json`
- `tests/acceptance/test_task7_split.py`
- `tests/acceptance/test_task7_group.py`
- `tests/acceptance/test_task7_claims.py`
- `tests/acceptance/test_task7_pages.py`
- `tests/acceptance/test_task7_cache.py`
- `tests/acceptance/test_task7_audit.py`
- `tests/acceptance/test_task7_e2e.py`
- `tests/fixtures/task7_e2e/`（T013 构造的端到端小语料目录，内含配套小清单 manifest.json）

### MODIFY

- `src/knowledge_digest/simple_cli.py`
- `.gitignore`
- `AGENTS.md`（digest 使用说明同步；T014）

### DO NOT TOUCH

- 删除证明（deletion proofs）：本计划不涉及删除任何既有文件（no deletion）；NEW 17 项为纯新增，MODIFY 3 项为窄修改，K4 才负责删码
- `src/knowledge_digest/compiler.py` / `pipeline.py` / `reader_compiler.py` / `reader_bundle.py` / `reader_quality.py` 等全部既有模块（K4 删码边界；新链路只 import 不修改）
- `specs/task7-semantic-layer-compiler/decision-log.md` 与 `spec.md`（已冻结材料）
- `CONTEXT.md`（术语登记归 build-spec 已完成）
- `docs/adr/`（OPEN-007：不改 ADR 0013）
- CompanyBrain 全树、gbrain 配置与索引、停摆自动化流水线、`/Users/Hugh/Downloads/confluence 原始数据`（只读输入）
- `tests/` 既有全部测试文件（AC-10 的改挂/废弃动作发生在新测试文件内，不动旧文件本体）

## Technical Decisions

### DEC-001 — 语义编译链路整体为 new，拆块基底 extend 复用

- **Problem**：需要一条保真第一、直接产出同构语义层页面并自带审计的编译链路；旧 reader 路径（固定窗口+改写）全部不可用。
- **Options**：A 全新自研拆块（丢弃 `_paragraph_evidence`）；B extend 复用 `_paragraph_evidence` + `normalize_structure`，追加表格聚合与分类优先级；C 改造旧 reader_compiler（被拒绝：它的窗口拆块与改写正是要绕开的缺陷）。
- **Selected**：extend（拆块基底）+ new（编排/归组/claim/页面/缓存/审计六模块）
- **Reason**：B 保住「字节从不改写」的已验证语义且最小化新代码；六模块对应 spec 的六个 FR 簇，职责窄、可独立 RED/GREEN。
- **Consequence / risk**：新模块长期维护面增加（K4 时评估去留）；`_paragraph_evidence` 若被 K4 删除，semantic_split 需内聚化（记入风险 PLAN-RISK-003）。
- **Fallback**：拆块聚合逻辑独立成纯函数，若上游改动可用 `normalize_structure` 单锚点重建。
- **F10 real threat**：无此新链路则 K1 的 AC-01/02/04 无任何实现载体，89 份语料继续丢参考型内容（真实已发生的问题，非 speculative）。
- **F10 existing cover**：旧链路覆盖的是「场景化摘要索引」，不覆盖「参考保真知识页」——正是要被替换的行为；无任何既有模块可改造达成 spec FR-PUB/AUD。
- **F10 bypassable**：模型改写诱惑由 spec FR-CMP-003 强制「模型只经 cache 写标题/导读」+ AC-02 逐字节 diff 压制，绕过即测试红。
- **F10 maintenance cost**：7 个新模块 + 1 个脚本 + 7 个测试文件；每次 spec 变更只需动对应单模块（窄契约）；K4 删旧码时一并评估删除条件。
- **F10 disposition**：keep

### DEC-002 — 英文 slug：模型缓存主路径 + 文件名 ASCII 段确定性回退；每主题单次复合模型调用

- **Problem**：gbrain slug 规则删空非 ASCII，中文主题名必然碰撞（实测 89→37 slug）；OPEN-003 要求冻结生成方式、碰撞后缀策略与 import-order 无关性；且 FR-AUD-005 调用预算上界 = 合并后主题数 × 2 + 20，模型调用结构必须在该上界内可复算。
- **Options**：A 模型把主题键译成英文标题再 slug 化（随缓存冻结）；B 仅取文件名 ASCII 段；C 拼音（多音字不稳定，弃）；调用粒度另选：每产物一次（3 次/主题）vs 每主题一次复合调用（1 次/主题）。
- **Selected**：A 主路径（slug 候选与标题/导读同缓存键族，确定性由缓存冻结保证）+ B 回退（provider 不可用且无缓存时：取成员来源文件名的 ASCII 段做 slug；无 ASCII 段则该页进阻塞清单）；**调用结构冻结为每主题组一次复合调用**（同一请求返回标题+导读+slug 候选，一个 cache_key），同义主题建议按 product 聚合另发（≤4 个 product）；碰撞后缀 = 同 base slug 按主题键字典序编号 `-2/-3`，与导入顺序无关。
- **Reason**：复合调用使实际调用数 ≈ 主题数 + product 数 ≤ 2×主题数 + 20 恒成立（FR-AUD-005 可复算）；A 质量最高且免费获得 AC-06 字节一致；B 保证 SCN-007 下页面仍可落盘。
- **Consequence / risk**：回退 slug 可读性差但合法且唯一；模型可用后重跑即恢复高质量 slug（键变→缓存重算）。
- **Fallback**：阻塞清单显式记录 slug 失败页，不静默丢弃。

### DEC-003 — 旧 digest 行为整体迁至 scripts/，digest 默认分支只走新链路，旧 flag 明确拒绝

- **Problem**：D-018 要求 digest 换门牌号且「不新增子命令、不双行为猜输入」；AC-09 要求旧能力保留可对照、两者互不影响。
- **Options**：A digest 按 flag 分流新旧（拒：一个命令两种行为）；B digest 只走新链路，旧行为完整复制为 scripts/legacy_digest_reference.py（原模块不动）；遗留 flag（--no-llm/--quality-config/--slice-config/--gate 等）的处理：B1 静默忽略 / B2 明确报错并指向 legacy 脚本。
- **Selected**：B + B2 — digest 对历史 flag 直接报错退出（非零），提示使用 `python scripts/legacy_digest_reference.py`；不保留任何旧分发分支（含 --no-llm）。
- **Reason**：门牌号唯一；旧路径能力 100% 保留（脚本调同一批未修改的旧模块）；「digest 仍走旧路径」在测试里成为可断言的失败模式，AC-09 双方互不影响成立。
- **Consequence / risk**：旧测试中进程内直调旧模块的用例不受影响；直调 simple_cli 默认分支或带历史 flag 的用例会红——这正是 AC-10/OPEN-005 要分类改挂或标废弃的对象。
- **Fallback**：legacy 脚本不可运行时，旧路径仍可通过进程内直调 `knowledge_digest.compiler.digest` 对照（脚本本身即此形态）。

## Test Strategy

设计 RED/GREEN，不在 build-plan 执行命令。两者使用同一 `gate_cmd` 与 oracle identity。

| Target | Task | Role | gate_cmd / expected_exit | Oracle / evidence_path |
| --- | --- | --- | --- | --- |
| FR-BLK-001/002, AC-01 | T001 | RED | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"` / 1 | ORACLE-SPLIT-001 — 整块聚合/分类优先级/坏行/第二方法比对断言失败信号 / `quality/evidence/build-code/task7/T001/` |
| FR-BLK-001/002, AC-01 | T002 | GREEN | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"` / 0 | ORACLE-SPLIT-001 — 上述断言通过且负例（坏表/粘 bullet）保留 / 同上 |
| FR-GRP-001/002, AC-06 | T003 | RED | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"` / 1 | ORACLE-GROUP-001 — 归一化/product 作用域/显式映射/建议不改成员断言失败信号 / `quality/evidence/build-code/task7/T003/` |
| FR-GRP-001/002, AC-06 | T004 | GREEN | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"` / 0 | ORACLE-GROUP-001 — 划分确定性 + 模型建议只进报告 / 同上 |
| FR-AUD-002/CMP-002/004, AC-04/11 | T005 | RED | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_claims.py -q"` / 1 | ORACLE-CLAIM-001 — claim_id 稳定性/span 映射/被拒导读锚点断言失败信号 / `quality/evidence/build-code/task7/T005/` |
| FR-AUD-002/CMP-002/004, AC-04/11 | T006 | GREEN | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_claims.py -q"` / 0 | ORACLE-CLAIM-001 — 零无锚点 span + 多 claim 句逐条映射 / 同上 |
| FR-PUB-001/003, CMP-001, AC-02/03/07 | T009 | RED | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_pages.py -q"` / 1 | ORACLE-PAGE-001 — 16 字段/slug 不动点且唯一/双链/300 行/逐字节块断言失败信号 / `quality/evidence/build-code/task7/T009/` |
| FR-PUB-001/003, CMP-001, AC-02/03/07 | T010 | GREEN | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_pages.py -q"` / 0 | ORACLE-PAGE-001 — 页面字节与结构断言全过 + oversized 附录 part / 同上 |
| FR-CMP-003, AC-06/12 | T007 | RED | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_cache.py -q"` / 1 | ORACLE-CACHE-001 — 复合键/命中不重调/缺缓存写回/负例失效断言失败信号 / `quality/evidence/build-code/task7/T007/` |
| FR-CMP-003, AC-06/12 | T008 | GREEN | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_cache.py -q"` / 0 | ORACLE-CACHE-001 — 键变必失效（含改合并页非主来源负例）/ 同上 |
| FR-AUD-001/003/004/005, AC-05/08/12/13 | T011 | RED | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_audit.py -q"` / 1 | ORACLE-AUDIT-001 — 五件 schema/五类状态/覆盖不变量/成本记账断言失败信号 / `quality/evidence/build-code/task7/T011/` |
| FR-AUD-001/003/004/005, AC-05/08/12/13 | T012 | GREEN | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_audit.py -q"` / 0 | ORACLE-AUDIT-001 — 覆盖双向一致 + 真实 0 附 reason / 同上 |
| FR-CLI-001/SRC-001/002/PUB-002/REG-001, AC-08/09/10/01 | T013 | RED | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_e2e.py -q"` / 1 | ORACLE-E2E-001 — 对账/骨架批次/计划打印/digest 新行为断言失败信号 / `quality/evidence/build-code/task7/T013/` |
| FR-CLI-001/SRC-001/002/PUB-002/REG-001, AC-08/09/10/01 | T014 | GREEN | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_e2e.py -q"` / 0 | ORACLE-E2E-001 — 端到端小语料出批 + 基线 16 节点不变 / 同上 |

规划涉及真实验收时，在现有接口契约和任务卡中绑定 tier、数据 source/sample/scenario、逐 AC oracle 与原始证据消费者。最终聚合卡 T015 为 `acceptance_role=acceptance`、`e2e_scope=not_required`、`ui_scope=non_ui`，acceptance_data 全部为 command tier（真实执行器输出逐 AC 断言 JSON）；build-code 的认证 outcome 驱动真实执行，verify-code 认证执行事实。

## Rollback and Recovery

- **Global recovery rule**：只回滚当前实现改动（新模块/新测试/两处 MODIFY），四份材料与既有质量事实保留；批次目录与缓存可随时重建。
- **Irreversible boundaries**：commit/push/merge/archive/cleanup 需另行授权（本计划不含）；旧模块删除属 K4，本卡不执行。
- **Recovery owner**：build-code 执行者回退到同任务修复；无法修复时回 build-plan 修计划，不回 make-decision（无方向变化）。

### Engineering Risk Handoff

- **PLAN-RISK-001**：provider 不可用 + 缓存缺失时英文 slug 回退仍失败的页面
  - **Affected IDs**：FR-PUB-001；AC-03；SCN-007
  - **Trigger**：模型不可达且无缓存，且成员来源文件名无 ASCII 段
  - **Consequence**：该页无法落盘，进阻塞清单
  - **Mitigation or STOP**：显式阻塞（model_unavailable_no_cache 变体 slug_fallback_exhausted）；恢复后重跑
  - **Handling Stage**：build-code
  - **Verification**：test_task7_e2e.py 的 provider 不可用负例
- **PLAN-RISK-002**：旧测试改挂/标废弃的分类错误导致 AC-10 基线失真
  - **Affected IDs**：FR-REG-001；AC-10；OPEN-005
  - **Trigger**：把非 digest 绑定用例误判为可废弃
  - **Consequence**：用例集合变化被计数掩盖
  - **Mitigation or STOP**：分类清单逐文件标注绑定面；16 节点 ID 清单冻结于 plan；STOP=分类无法判定
  - **Handling Stage**：build-code
  - **Verification**：基线比对脚本按节点 ID 集合判定
- **PLAN-RISK-003**：`_paragraph_evidence` 上游（compiler.py）在 K4 被删/改导致 semantic_split 断裂
  - **Affected IDs**：FR-BLK-001；T002
  - **Trigger**：K4 删旧码
  - **Consequence**：拆块基底失效
  - **Mitigation or STOP**：聚合逻辑纯函数化、单锚点 import；K4 时内聚化
  - **Handling Stage**：K4（延期）
  - **Verification**：K4 时重跑 test_task7_split.py

## Implementation Order

P1 拆块（块是下游唯一输入）→ P2 归组（依赖块的 heading_path）→ P3 claim（依赖叙述块切片）→ P4 缓存（生产页面消费的标题/导读/slug 冻结结果）→ P5 页面（依赖组+claim+缓存产物）→ P6 审计（消费全管道事实）→ P7 命令/E2E（消费全部 + 旧路径迁移）。全部串行：每 Phase 的 GREEN 是下一 Phase RED 的事实输入。

## Dependencies and Parallelism

- **Dependencies**：T001→T002→T003→…→T014→T015 全链；模块间 producer-before-consumer 如上。
- **Parallel work**：无 — 单链路逐 Phase 推进（并行声称会触发文件重叠检查，本计划不做并行声称）。
- **External dependencies**：pytest≥8（dev 组已声明）；冻结清单与语料根（只读）；provider 配置（~/.config/knowledge-digest/config.json，运行时读取，不入库）。

## Requirement and Verification Traceability

| Source / decision | FR | AC | Phase / Task | Depends on | Exact files | Command / oracle |
| --- | --- | --- | --- | --- | --- | --- |
| R-028/R-029；D-010 | FR-BLK-001/002 | AC-01 | P1 / T001-T002 | none | `src/knowledge_digest/semantic_split.py` | `bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"` / ORACLE-SPLIT-001 |
| R-021/R-015；D-003/D-007 | FR-GRP-001/002 | AC-06 | P2 / T003-T004 | T002 | `src/knowledge_digest/semantic_group.py`; `config/task7-topic-map.json` | test_task7_group.py / ORACLE-GROUP-001 |
| R-015/R-019；D-004/D-005 | FR-AUD-002/CMP-002/004 | AC-04/11 | P3 / T005-T006 | T002 | `src/knowledge_digest/semantic_claims.py` | test_task7_claims.py / ORACLE-CLAIM-001 |
| R-013/R-035/R-036；D-005/006/015 | FR-PUB-001/003/CMP-001 | AC-02/03/07 | P4 / T007-T008 | T004/T006 | `src/knowledge_digest/semantic_page.py` | test_task7_pages.py / ORACLE-PAGE-001 |
| R-013/R-035/R-036；D-005/D-006/D-015 | FR-PUB-001/003/CMP-001 | AC-02/03/07 | P5 / T009-T010 | T006/T008 | `src/knowledge_digest/semantic_page.py` | test_task7_pages.py / ORACLE-PAGE-001 |
| R-014/R-024/R-025；D-008/009 | FR-AUD-001/003/004/005 | AC-05/08/12/13 | P6 / T011-T012 | T008/T010 | `src/knowledge_digest/semantic_audit.py` | test_task7_audit.py / ORACLE-AUDIT-001 |
| R-011/R-026/R-041；D-002/011/012/016/018 | FR-CLI-001/SRC-001/002/PUB-002/REG-001 | AC-01/08/09/10 | P7 / T013-T015 | T012 | `src/knowledge_digest/semantic_compiler.py`; `src/knowledge_digest/semantic_cli.py`; `scripts/legacy_digest_reference.py`; `src/knowledge_digest/simple_cli.py` | test_task7_e2e.py / ORACLE-E2E-001 |

## Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| 宪法（workflowhub CONSTITUTION.md v1.8.0） | `specs/task7-semantic-layer-compiler/plan.md` | no change | T001-T015 | 计划遵宪法 22 条，不改宪法 |
| 技能/文档（AGENTS.md） | `AGENTS.md` | change | T013-T014 | digest 行为切换后需同步 AGENTS.md 使用说明（开发命令一节） |
| 测试 | `tests/acceptance/test_task7_*.py` | change | T001-T015 | 新增 7 个测试文件；旧测试分类动作在 build-code（OPEN-005） |
| 配置 | `config/task7-topic-map.json`; `.gitignore` | change | T003/T013 | 显式主题映射输入 + 缓存目录忽略 |

## Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"workflowhub/CONSTITUTION.md","hash":"18bed97f134e00723bc96635f6ee2223b4367fb8baa0a9087594a35ef63478dd","id":"workflowhub-constitution","version":"1.8.0","clause_count":22,"checklist_ref":"workflowhub/constitution-checklist.md","checklist_hash":"7d028c2919d2ef7749489d4a716be273a0dd986e7ea795a6b052c25a8d5dc12f"}`
- **F1**：新链路把重活下沉到七个窄职责模块，simple_cli 只做派活收结果 — 薄核心 ✓
- **F2**：模块间以 Block/Claim/TopicGroup dataclass 窄契约交互，不互读内部状态 ✓
- **F3**：推进只看四材料；批次写入前的身份/hash/结构错误 fail-loud（manifest 最后落盘、失败不写完成）✓
- **F4**：wh-review 为质量事实非 gate；findings 处置留在本任务修复（build-spec 已示范 12/12 fixed）✓
- **F5**：不新增 gate；gate_cmd 只是测试命令 ✓
- **F6**：执行事实写任务外置记录（quality/），任务不绑 runner 路径 ✓
- **F7**：本阶段正常确认在 publish 步经 confirm --action=decision 取得；不可逆操作另行授权 ✓
- **F8**：复用优先（_paragraph_evidence/normalize_structure/llm seam），无 replacement 链 ✓
- **F9**：RED 预期非零、结构校验失败拒绝写完成、缺失质量事实保持 incomplete ✓
- **F10**：自动化按真实收益——只加 7 模块不加 CI/新 gate；实跑验证优先（AC-06 两次实跑比对）✓
- **F11**：正常执行优先：无新增控制面；辅助事实缺失不阻塞（research receipt 缺失不挡计划）✓
- **Q1**：质量事实不作准入证；完成需真实测试/逐 AC/审查/交接 ✓
- **Q2**：推进资格（四材料）/发布结构（manifest 原子尾写）/完成判据（RED-GREEN+review+确认）分离 ✓
- **Q3**：独立 wh-review 异源审查；本计划 lens（eng-review/simplicity）只产 advisory ✓
- **S1**：复用 mature 锚点不造轮子（拆块/标题树/指纹/provider seam）✓
- **S2**：不适用外部技能改造；声明 not_applicable — 无采用中的外部技能需改造
- **S3**：决策日志锚点已按最新代码复核（2945 而非旧 2940），就地更新 ✓
- **S4**：新链路指标进 run-metrics.json（耗时/调用/token/缓存命中），统一执行记录 ✓
- **S5**：重取证派子代理，主会话只收结论 ✓
- **S6**：拆块参考市面保真切片实践（整块单元+双方法交叉验证），不闭门造车 ✓
- **S7**：一阶段一技能；新模块按既有 src-layout 目录约定 ✓
- **S8**：新模块纯 stdlib+既有依赖，不绑宿主，可独立搬运测试 ✓

## 阶段执行记录（build-plan）

### conditional-spec-research 执行记录（step 2）

一轮只读取证（子代理，含一次基线测试实跑）：拆块/指纹/标题树/reader 窗口锚点全部复核（`_paragraph_evidence` 实际 2945-2991，旧锚点 2940 已漂移）；55 个模块行数清单；simple_cli 三分支分发面；49 个 acceptance 测试文件与无 conftest 事实；冻结清单首条 entry 与 `expected_status` 分布（present=88/empty=1）；基线 911 收集、16 失败节点 ID 完整清单与根因（仓库外证据缺失，非代码回归）；缓存/输出落点既有约定（`_digest/runs`、Downloads 直接子目录强制先例）。正式 research receipt 无 build-plan 公共发布入口，按合同记未供给，事实已固化进 Technical Context 与各 Phase Knowledge。

### simplicity-guard 四阶梯执行记录（step 5）

- 拆块：P2——extend 复用 `_paragraph_evidence`+`normalize_structure`，不重写（DEC-001）。
- 主题归组/页面/审计：P3——无既有覆盖（旧路径全部绕行），最小新增六模块。
- 缓存：P3——无任务级既有缓存；consumer/owner/test/删除条件齐备（Reuse 表）。
- 分批恢复/原子发布/向量库：P0 不成立（D-013/NG-004/NG-007）。
- 旧行为保留：P2——脚本化迁移，不双轨并行（DEC-003）。
- 结论：无 scope creep；无未证明长期能力；每处新增均给出删除条件。

### plan-eng-review 执行记录（step 6）

- 需求→任务映射：20 FR / 13 AC 全部落入 T001-T015，双向追溯表闭合。
- 模块归属：七模块与 Phase 一一对应，文件互不跨 Phase；`compiler.py`/`draft.py` 只 import 不修改。
- 接口锚点：`_paragraph_evidence`/`normalize_structure` 签名与消费方已核；slug 回退链有明确锚点（成员来源文件名）。
- 状态/失败路径：SCN-007 矩阵在 P7 执行；骨架批次（对账失败）与 manifest 尾写顺序在 P6/P7。
- 依赖序：全链串行无环；并行声称为零（无文件重叠风险）。
- RED/GREEN：七对同命令同 oracle，RED 非零/GREEN 0，负例保留在各卡 coverage limits。
- 回滚：每 Phase 回滚 = 删新文件 + 还原两处 MODIFY；不可逆操作不在本计划。
- 实现效果：消费方（digest 入口→semantic_cli→compiler→六模块）在 P7 端到端可证。

### test-routing 预判记录（step 7 输入）

全部任务为单一功能域内行为变化（Python 模块级，无 UI/网络接口/数据库/部署配置），按 test-routing-advisor 判类标准预判 `feature`；独立顾问的正式判类结果见任务卡 test tier 字段（已在 tasks.md 记录顾问返回的 JSON）。

## Phase P1 — 保真拆块与双方法块清单

### Goal

89 份语料（及 fixture）被拆成整块单元块流，表格行聚合为整块、坏行原样、分类优先级确定；独立第二方法产出可比清单。

### Files

- **NEW**：`src/knowledge_digest/semantic_split.py`; `tests/acceptance/test_task7_split.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：`src/knowledge_digest/compiler.py`（只 import `_paragraph_evidence`）；语料根目录（只读输入）

### Tasks

- `T001`：RED — 拆块边界/整块聚合/分类优先级/坏行/第二方法比对测试先行失败
- `T002`：GREEN — semantic_split 最小实现使上述测试通过并保留负例

### Verify

`bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"` / 0；ORACLE-SPLIT-001；证据 `quality/evidence/build-code/task7/T002/`。

### Knowledge

块字段形态（source_path/block_id/content_hash/kind/line_start/line_end/text）与 FR-BLK-001 优先级表交给 P2/P3。

### STOP

命令损坏、`_paragraph_evidence` 签名与锚点不符、或需放宽整块定义时返回 spec（FR-BLK-001）核对。

### Done

test_task7_split.py 全绿；坏表/粘 bullet/坏行 fixture 逐字节对上；第二方法差异为空；RED 证据留存。

### Risks and rollback

上游锚点漂移（PLAN-RISK-003）；回滚 = 删除两新文件，无既有面影响。

## Phase P2 — 主题归组与显式映射

### Goal

标题名归一化 + product 作用域分组确定性成立；显式主题映射机械生效；模型建议不改变页面成员。

### Files

- **NEW**：`src/knowledge_digest/semantic_group.py`; `config/task7-topic-map.json`; `tests/acceptance/test_task7_group.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：`config/` 其余冻结清单（只读输入）

### Tasks

- `T003`：RED — 归一化/作用域/显式映射/建议不改成员测试先行失败
- `T004`：GREEN — semantic_group 实现使测试通过

### Verify

`bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"` / 0；ORACLE-GROUP-001；证据 `quality/evidence/build-code/task7/T004/`。

### Knowledge

TopicGroup 字段（key/product/module_anchor/members）与 topic-map 配置形态交给 P4/P5。

### STOP

归一化规则与 spec FR-GRP-001 冲突、或需要语义相似度归组时返回 spec。

### Done

同输入两次运行划分一致（确定性断言）；显式映射 fixture 生效；建议输出形状只读。

### Risks and rollback

归一化过度/不足；回滚 = 删除三新文件。

## Phase P3 — claim 管道与双轨溯源

### Goal

句子级 claim 切分、稳定 claim_id（char 区间 + occurrence_index）、span 级正文↔旁路映射、被拒导读句锚点登记全部成立。

### Files

- **NEW**：`src/knowledge_digest/semantic_claims.py`; `tests/acceptance/test_task7_claims.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：spec FR-AUD-002 字段清单（只读契约）

### Tasks

- `T005`：RED — claim_id 稳定性/span 映射/多 claim 句/被拒导读锚点测试先行失败
- `T006`：GREEN — semantic_claims 实现使测试通过

### Verify

`bash -c "uv run --frozen pytest tests/acceptance/test_task7_claims.py -q"` / 0；ORACLE-CLAIM-001；证据 `quality/evidence/build-code/task7/T006/`。

### Knowledge

Claim 记录形态（含 claim_kind/status/retrieval_evidence 必填规则）交给 P4/P6。

### STOP

切分规则需改写原文、或 claim_id 稳定性无法在不改原文下保证时返回 spec。

### Done

重复句同来源不碰撞；多 claim 句逐条映射；被拒导读句 page_anchor=intro 且 retrieval_evidence 必填。

### Risks and rollback

句子切分与中日文标点边界；回滚 = 删除两新文件。

## Phase P4 — 模型缓存

### Goal

复合键（模型标识+提示模板版本+主题映射版本+页面复合输入指纹）缓存冻结、命中不重调、缺缓存调用写回、改一字节必失效。

### Files

- **NEW**：`src/knowledge_digest/semantic_cache.py`; `tests/acceptance/test_task7_cache.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：`~/.config/knowledge-digest/config.json`（用户凭据，只读）；凭据禁止写入代码/产物/缓存

### Tasks

- `T007`：RED — 键构成/命中/写回/负例失效测试先行失败
- `T008`：GREEN — semantic_cache 实现使测试通过

### Verify

`bash -c "uv run --frozen pytest tests/acceptance/test_task7_cache.py -q"` / 0；ORACLE-CACHE-001；证据 `quality/evidence/build-code/task7/T008/`。

### Knowledge

缓存条目 schema 与目录约定（`cache/model-cache/`，gitignore）交给 P7。

### STOP

需把凭据写入缓存、或键无法覆盖成员来源变化时返回 spec FR-CMP-003。

### Done

改合并页非主来源负例失效；缓存条目不含凭据；同输入两次读取字节一致。

### Risks and rollback

缓存目录误入 git；回滚 = 删除两新文件并清理 .gitignore 行。

## Phase P5 — 页面渲染、命名与分页

### Goal

16 字段 frontmatter、英文 slug（不动点+批内唯一+回退链）、`[[wikilink]]` 相关页面、300 行分页与 oversized 附录 part、读者侧出处行、附件标注全部落地。

### Files

- **NEW**：`src/knowledge_digest/semantic_page.py`; `tests/acceptance/test_task7_pages.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：真实 CompanyBrain 页面（同构基准只读抽样，不写入）

### Tasks

- `T009`：RED — 16 字段/slug 不动点唯一/双链/分页/逐字节块/出处行测试先行失败
- `T010`：GREEN — semantic_page 实现使测试通过

### Verify

`bash -c "uv run --frozen pytest tests/acceptance/test_task7_pages.py -q"` / 0；ORACLE-PAGE-001；证据 `quality/evidence/build-code/task7/T010/`。

### Knowledge

页面字节契约（frontmatter 值域/引用行模板/相关页面节）交给 P6 审计与 P7 端到端。

### STOP

slug 回退链穷尽、或 16 字段值与真实 CompanyBrain 抽样不符时返回 spec FR-PUB-001。

### Done

抽样 10 页结构断言全过；超 300 行参考块进附录 part；逐字节 diff 零差异。

### Risks and rollback

slug 碰撞编号误配；回滚 = 删除两新文件。

## Phase P6 — 审计与机读批次状态

### Goal

五件 `_audit/` 产物、五类状态推导（audit_only 声明式输入）、覆盖不变量（含 duplicate_alias 别名分支）、批次状态、成本记账全部机读可验。

### Files

- **NEW**：`src/knowledge_digest/semantic_audit.py`; `tests/acceptance/test_task7_audit.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：冻结清单（对账基准只读）

### Tasks

- `T011`：RED — 五件 schema/状态/覆盖/成本记账测试先行失败
- `T012`：GREEN — semantic_audit 实现使测试通过

### Verify

`bash -c "uv run --frozen pytest tests/acceptance/test_task7_audit.py -q"` / 0；ORACLE-AUDIT-001；证据 `quality/evidence/build-code/task7/T012/`。

### Knowledge

manifest 最后落盘约定与状态词表交给 P7 骨架批次。

### STOP

五类 fixture 无法构造、或覆盖校验需要第三态时返回 spec FR-AUD-003/AC-13。

### Done

五类 fixture 逐类核对过；真实 0 计数附 reason；manifest 反查双向可达。

### Risks and rollback

状态推导与正文漂移；回滚 = 删除两新文件。

## Phase P7 — 命令切换与端到端

### Goal

`digest` 默认分支执行新语义编译；旧行为迁至 scripts/ 可独立运行；对账骨架批次、计划打印、端到端小语料出批、AC-10 基线 16 节点冻结。

### Files

- **NEW**：`src/knowledge_digest/semantic_compiler.py`; `src/knowledge_digest/semantic_cli.py`; `scripts/legacy_digest_reference.py`; `tests/acceptance/test_task7_e2e.py`; `tests/fixtures/task7_e2e/`
- **MODIFY**：`src/knowledge_digest/simple_cli.py`; `.gitignore`; `AGENTS.md`
- **DO NOT TOUCH**：`src/knowledge_digest/compiler.py` 等旧模块（legacy 脚本只调不改）；`docs/adr/`

### Tasks

- `T013`：RED — 对账/骨架批次/计划打印/digest 新行为/基线节点/SCN-007 三态/双跑 diff/中断注入测试先行失败
- `T014`：GREEN — semantic_compiler/semantic_cli/legacy 脚本/入口改派/AGENTS.md 同步使测试通过
- `T015`：FINAL — 聚合验证全部适用 AC 与跨任务 seam（acceptance_role=acceptance）

### Verify

`bash -c "uv run --frozen pytest tests/acceptance/test_task7_e2e.py -q"` / 0；ORACLE-E2E-001；证据 `quality/evidence/build-code/task7/T015/`。

### Knowledge

交付 build-code：digest 门牌号已切换；legacy 脚本为旧行为唯一入口；AGENTS.md 使用说明需同步（T014 一并改）。实现 guard：`CacheIntegrityError` 后 provider result 只进诊断，不进入页面渲染；页面必须使用确定性 fallback；对账失败仍记录已完成工作的真实 `elapsed_ms`，并使用非 provider 的失败 reason。

### STOP

旧行为无法完整迁移、或基线 16 节点无法冻结时返回 plan（本文件）修计划。

### Done

端到端 fixture 语料出批且 manifest 机读；legacy 脚本可运行；基线节点 ID 清单落 plan；T015 聚合通过。

### Risks and rollback

旧测试大面积变红的误读（实为 AC-10 分类对象）；回滚 = 还原 simple_cli.py 与 .gitignore，删四新文件。
