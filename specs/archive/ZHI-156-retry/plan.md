# 防丢失机制完整版与溯源层加固：实施计划

## 概要

在现有本地手动 `digest` 流水线中补齐可验证的来源快照、claim 级溯源、可恢复归档、结构前置检查和长文无损重组。继续复用现有 S1–S6、`_digest` 运行目录、`_archive` 与原子写入；不增加联网、调度、CAS/journal、双库适配或阈值标定工具。

## 技术上下文

- Python 3.11，现有入口为 `knowledge_digest.cli`，主编排在 `src/knowledge_digest/pipeline.py`。
- S1 `ingest.py` 已识别空壳和失败来源；S4 `draft.py` 已保留 claim、`removed_claims` 与超长提示；S5 `writeback.py` 已使用文件级原子写入和页面快照；S6 `provenance.py` 已生成来源审计。
- 当前缺口：来源校验信息没有完整快照契约；claim 没有固定指纹、内容指纹和片段位置；移除记录未持久保存原因和原文；结构声明不阻断写入；长文只给出提示、不产生重组页和覆盖映射。
- 研究结论：不需要外部研究。冻结规格与现有模块边界足以决定最小改造；所有校验只基于本次本地输入，不请求外网。

## 约束和关键决定

1. `fragment_locator` 固定为唯一片段定位字段名。对行级 claim 使用稳定的原文行范围；对组件重组使用输出页内的连续范围。
2. `claim_fingerprint` 由 `source_uri` 和规范化原文计算；`content_fingerprint` 由整个本地来源快照计算。内容变更创建新版本，记录双向替换关系，不做语义合并。
3. 失败来源仍生成来源快照和诊断，但不会成为 S1 可处理 `RawItem`，不会进入正式页面来源索引。已有正式 claim 不因后续失败被删除，只进入待复核清单。
4. 完整正文和来源快照归档至知识库声明的 `_archive` 根下，记录 `retain_content_until`；每次非 dry-run 在正式处理后清理到期正文/快照，只保留长期元数据。
5. `why_field` 与 `version_field` 必须在 `kb.structure.md` 中声明非空字段名。任一缺失时先输出诊断和补全建议，`allow_official_write=false`，不进入 S5。
6. 长文按标题块、完整 FAQ、错误码条目、参数条目、代码块及其紧邻解释的优先级分组，按原始顺序贪心装页。不可再拆分的超阈组件完整保留并显式标记；任何未覆盖输入片段或 claim 阻断正式写入。
7. `max_doc_lines` 继续使用现有 `DigestSettings.max_lines`：默认值为 300，可由 JSON 配置中的 `max_doc_lines`（兼容 `max_lines`）或 CLI 的 `--max-doc-lines` 覆盖；本期不新增阈值来源或标定机制。

## 接口和数据契约

### 来源快照和校验

扩展 S1 记录为 `SourceSnapshot`：`source_uri`、`captured_at`、`content_fingerprint`、`validation_status`、`validation_reason`、`validated_at`、正文快照和输入路径。S1 输出有效 `RawItem` 时携带所需快照引用；失败项写入来源快照和待复核/失败报告而非丢弃。

### Claim 和版本关系

每个最终 claim 包含 `claim_fingerprint`、`source_uri`、`content_fingerprint`、`fragment_locator`、`verification_status`，以及可选 `supersedes`/`superseded_by`。正式页的 Provenance 区和 S6 审计从同一结构化 claim 记录渲染，确保页面可回查到本地已校验快照。

### 归档和保留

复用 `writeback.py` 的原子文件工具和结构声明的 archive 根。替换、移除、校验事件生成归档记录：操作、时间、原因、claim/页面、来源快照、完整内容、`retain_content_until` 和长期溯源元数据。归档清理只清除到期完整内容及关联快照；元数据、定位、关系和原因保留。

### 结构检查和正式写入边界

`kb_structure.py` 新增解析/验证结构契约的接口，返回缺失字段、补全建议和 `allow_official_write`。`pipeline.py` 在生成 S5 变更前执行该前置检查；`writeback.py` 在写入前复核来源状态和覆盖映射。任何前置检查、来源二次校验或覆盖映射失败时，只写诊断、待复核和归档记录，不写正式页面或来源索引。

### 重组和覆盖映射

`draft.py` 从来源原文生成连续逻辑组件和按页分组的重组方案。每个输出页保留组件顺序；`split_suggestion` 列出原文、页面顺序、组件、超阈原因和未截断事实。覆盖映射把每个输入片段/claim 指到至少一个输出页与 `fragment_locator` 范围，供 S5 发布前验证。

## 实施顺序

1. 在 `kb_structure.py` 建立结构契约解析和 fail-closed 诊断；在 `pipeline.py` 接入早期检查，确保不合格输入永远到不了正式写入。
2. 在 `ingest.py` 和 `provenance.py` 建立本地来源快照、确定性内容指纹和校验状态；保留失败快照并输出待复核信息。
3. 在 `faithfulness.py` 和 `draft.py` 生成含固定指纹、来源内容指纹和 `fragment_locator` 的 claim；补齐失败保留、变更关系和带原因/原文的 `removed_claims`。
4. 在 `draft.py` 实现组件识别、无损分页、split suggestion 和覆盖映射；先验证覆盖完整再把重组结果交给 S5。
5. 在 `writeback.py` 扩展正式页面渲染、来源索引过滤、归档事件、版本关系和多页重组写入；沿用每文件原子替换，并在提交前做全批前置校验，避免部分正式索引。
6. 在 `pipeline.py` 汇总结构检查、来源过滤、待复核、归档清理和 split 结果到运行报告；仅在非 dry-run 成功通过全部正式前置条件后触发写入。
7. 新建 Phase 1 验收簇，先覆盖混合来源、溯源/版本、归档/保留、结构失败和长文重组，再运行现有 Phase 0 回归。

## 任务摘要

| 任务 | 交付 | 依赖 | 可并行 |
| --- | --- | --- | --- |
| T001 | 结构契约和 fail-closed 检查 | 无 | T002 |
| T002 | 本地来源快照和校验状态 | 无 | T001 |
| T003 | Claim 指纹、定位、版本和失败保留 | T002 | T004 |
| T004 | 归档、90 天保留和受限清理 | T002 | T003、T005 |
| T005 | 无损组件重组和覆盖映射 | T003 | T004 |
| T006 | 正式写入总校验、来源过滤和运行报告 | T001、T003、T004、T005 | 否 |
| T007 | Phase 1 验收簇和 Phase 0 回归 | T006 | 测试骨架可提前编写 |

## 测试策略和证据

- 新增 `tests/acceptance/test_phase1_loss_prevention.py`，固定本地夹具，不联网。
- 验证混合簇中抓取失败/空壳来源在最终来源索引的引用数为 0，所有最终 claim 具备四个溯源字段并能定位到已验证快照。
- 验证内容变化创建新版本、双向关系；后续校验失败不删除旧 claim，待复核和重试状态可见。
- 验证替换/移除归档带原文、快照、原因和 90 天截止；到期只删除全文/快照，未到期可核对恢复。
- 验证 Why 或版本字段缺失时无正式页面；两者具备且其他检查通过时允许写入。
- 验证 FAQ、错误码、参数、代码块与紧邻解释不被拆开；覆盖映射完整、顺序稳定、不可拆分超阈组件可见且不截断。
- 运行 `python -m pytest tests/acceptance/test_phase1_loss_prevention.py -q`，再运行全部 `python -m pytest -q` 保护 Phase 0 行为。

## 回退和失败处理

- 实现只在每次运行的知识库目录中创建可追溯诊断与归档；不修改外部来源。
- 任何正式写入前置检查失败时保持原正式页面不变。写入过程仍使用现有临时文件、fsync 和 replace，单页失败留下失败记录并抛出错误。
- 归档清理只处理明确超过 `retain_content_until` 的完整内容；长期元数据不参与清理。若清理或写入异常，运行失败并保留可读报告。

## 需求映射

| 需求 | 实施落点 | 验证 |
| --- | --- | --- |
| FR-01, AC-01 | `ingest.py`、`provenance.py` 的本地快照和状态记录 | 本地快照完整、无联网断言 |
| FR-02, AC-02 | S1 失败隔离、S5 来源二次过滤 | 空壳/失败 URI 最终引用数为 0 |
| FR-03, AC-03, AC-04 | `faithfulness.py`、`draft.py`、`provenance.py` | 四字段完整；变更生成双向版本关系 |
| FR-04, AC-05 | `pipeline.py`、`provenance.py` 的待复核报告 | 失败后旧 claim 可读且有原因/重试状态 |
| FR-05, FR-06, AC-06, AC-07, AC-08 | `writeback.py` 的归档与清理 | 原文/快照、原因、90 天保留与元数据保留 |
| FR-07, AC-09, AC-10, AC-11 | `kb_structure.py`、`pipeline.py` | 缺字段 fail-closed；字段齐全可写 |
| FR-08, FR-09, FR-10, AC-12, AC-13, AC-14 | `draft.py`、`writeback.py` | 无损分页、完整覆盖映射、组件原子性 |
| FR-11, AC-15 | `pipeline.py`、`writeback.py` 提交前总检查 | 任一失败无部分正式页面/索引 |
| AC-16 | `tests/acceptance/test_phase1_loss_prevention.py` | 指定 Phase 1 验收命令全绿 |

## 宪法检查

- 最小改造：复用 S1–S6、现有运行目录、结构描述、归档目录和原子写入；不新增服务、数据库、后台任务或适配层。
- 可观察失败：校验失败、结构缺失、覆盖缺口和归档清理均输出明确报告，不以部分正式写入伪装成功。
- 确定性：指纹、片段位置、组件识别、分页和覆盖映射由本地输入和固定规则决定。
- 范围：明确排除联网复抓、人工复核产品流程、CAS/journal、双库、调度、阈值标定及 Phase 2/3/4 内容。
