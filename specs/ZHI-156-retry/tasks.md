# 防丢失机制完整版与溯源层加固：任务清单

## T001：知识库结构契约和 fail-closed 前置检查

- 影响区域：`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/pipeline.py`。
- 行动：在现有 frontmatter 解析基础上返回结构契约、缺失字段和补全建议；要求 `why_field` 与 `version_field` 为非空声明。非 dry-run 在 S1/S5 前记录检查结果，`allow_official_write=false` 时停止正式写入。
- 覆盖：FR-07、FR-11、AC-09、AC-10、AC-11、AC-15。
- 依赖：无。
- 验证：分别构造缺 Why、缺版本、字段齐全三种结构文件；前两种没有新增正式页面，错误说明缺失字段和补全方式。
- 并行：可与 T002 并行。

## T002：本地来源快照和校验状态

- 影响区域：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/provenance.py`、`src/knowledge_digest/pipeline.py`。
- 行动：为每个本次输入来源建立含地址、捕获时间、内容指纹、校验结论、原因和校验时间的快照；空壳、失败、无正文、不一致来源进入失败快照和诊断，只有通过项成为可处理 RawItem。
- 覆盖：FR-01、FR-02、FR-04、AC-01、AC-02、AC-05。
- 依赖：无。
- 验证：混合本地样本不触发网络访问；失败快照有原因，最终可处理项不含失败 URI。
- 并行：可与 T001 并行；T003、T006 依赖本任务。

## T003：Claim 溯源、版本关系和失败保留

- 影响区域：`src/knowledge_digest/faithfulness.py`、`src/knowledge_digest/draft.py`、`src/knowledge_digest/provenance.py`。
- 行动：从原文行生成 `fragment_locator`，计算基于来源地址和规范化原文的 `claim_fingerprint`，绑定 `content_fingerprint` 与校验状态；来源内容变化时建立 `supersedes`/`superseded_by`；把不支持或移除的 claim 变成带原因、原文快照和来源信息的记录，失败来源关联的既有 claim 标为待复核而不删除。
- 覆盖：FR-03、FR-04、FR-05、AC-03、AC-04、AC-05、AC-06。
- 依赖：T002。
- 验证：每个最终 claim 有四个必需溯源字段；两次本地运行能证明新旧版本关系；失败后旧记录仍可读。
- 并行：与 T004 可并行；T006 依赖本任务。

## T004：归档记录、90 天保留和受限清理

- 影响区域：`src/knowledge_digest/writeback.py`、`src/knowledge_digest/provenance.py`、`src/knowledge_digest/pipeline.py`。
- 行动：复用声明的 archive 根和原子写入，为校验、替换、移除生成含完整正文/快照、原因、时间、关系和 `retain_content_until` 的归档记录；每次非 dry-run 在正式处理后清理过期完整内容，只保留长期溯源元数据。
- 覆盖：FR-05、FR-06、AC-06、AC-07、AC-08。
- 依赖：T002。
- 验证：未到期归档可核对恢复；模拟过期后正文/快照删除但指纹、定位、状态、关系和原因仍存在；空原因拒绝归档。
- 并行：与 T003 可并行；T006 依赖本任务。

## T005：超长文档无损组件重组和覆盖映射

- 影响区域：`src/knowledge_digest/draft.py`、`src/knowledge_digest/writeback.py`。
- 行动：使用现有 `DigestSettings.max_lines`（默认 300，可由 `max_doc_lines`/`--max-doc-lines` 覆盖）作为唯一阈值；按标题块、FAQ 完整问答、错误码、参数、代码块及紧邻解释识别连续组件；按原始顺序贪心分页，生成页面清单、split suggestion 和输入片段/claim 到输出页范围的覆盖映射。单组件不可拆时允许超阈并记录原因，映射不完整时返回失败而非部分结果。
- 覆盖：FR-08、FR-09、FR-10、AC-12、AC-13、AC-14。
- 依赖：T003。
- 验证：混合长文的 FAQ、错误码、参数和代码解释未被拆开；每个输入片段/claim 有映射；正文完整且输出顺序稳定。
- 并行：与 T004 可并行；T006 依赖本任务。

## T006：正式写入总校验、来源索引和报告汇总

- 影响区域：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/provenance.py`。
- 行动：在调用原子写入前汇总结构许可、来源二次校验和覆盖映射，任一失败时只留下诊断/待复核/归档，不产生或覆盖正式页面和来源索引。通过时从结构化 claim 记录渲染可追溯来源，过滤未验证 URI，并把来源过滤、结构检查、待复核、归档清理和 split 结果写入运行报告。
- 覆盖：FR-02、FR-07、FR-10、FR-11、AC-02、AC-03、AC-09、AC-10、AC-11、AC-15。
- 依赖：T001、T003、T004、T005。
- 验证：对每个前置失败类型断言正式 KB 内容和来源索引未改变；成功路径的报告完整且来源均为已验证快照。
- 并行：不可并行；是后续验收前置。

## T007：Phase 1 混合验收簇和 Phase 0 回归

- 影响区域：新增 `tests/acceptance/test_phase1_loss_prevention.py`，必要时新增同目录专用夹具；保留 `tests/acceptance/test_phase0_digest.py`。
- 行动：按 AC-01 至 AC-16 建立本地测试簇，覆盖失败/空壳来源、高密度页、长文组件、版本变化、替换/移除、90 天清理、结构缺失和原子边界；不使用网络或外部服务。
- 覆盖：AC-01 至 AC-16。
- 依赖：T001、T002、T003、T004、T005、T006。
- 验证：`python -m pytest tests/acceptance/test_phase1_loss_prevention.py -q` 全绿；`python -m pytest -q` 全绿。
- 并行：测试骨架可在 T001–T005 后期并行编写；最终断言在 T006 后收口。

## 交付顺序

`T001 + T002` → `T003 + T004` → `T005` → `T006` → `T007`。

实现必须保持手动、本地、单知识库运行边界；不得新增 Phase 2/3/4 的联网复抓、调度、人工复核流程、CAS/journal、双库适配或阈值标定能力。
