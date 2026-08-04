# Task2 final9 产物溯源与完整性审计（2026-08-04）

## 审计边界

只读检查 `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb` 的最终知识库及 `_digest` 运行证据；未改代码、未改产物、未调用外部模型。重点是来源覆盖、Claim 定位/状态、失败批恢复、重复记录、归档膨胀和质量门是否把“流程完成”误报成“知识质量完成”。

## 结论

这份产物不能按“88 个来源全部完成发布”验收。

- `source-index.md` 只有 88 条来源记录，但批次和快照实际涉及 89 个来源路径；`emm for android /AE - AirViewer厂商管理.md` 有快照/批次记录，却没有进入来源索引，且快照明确为 `source has no body`。
- 失败并非少量边缘情况：30 个来源进入 `pending-review`，至少 4,756 条 Claim 明确标为 `provider_failure=true`、`validation_status=failed`、`retry_next_batch_run`。`claim-history.jsonl` 中失败状态行共 4,904 条，和 pending 文件还差 148 条，两个溯源账本没有完全对齐。
- 运行级状态过于乐观：89 个批次都写成 `succeeded`，90 个报告写成 `official_write.status=written`；但所有报告的 `quality.status` 都为空，`benefit_status` 都是 `unmeasured`。这只能证明写回流程运行过，不能证明内容质量、来源覆盖或失败补偿已经完成。
- 归档和重放记录有明显膨胀/重复：2,736 个归档文件对应 120 个当前主题页；快照 178 行只对应 89 个唯一来源；Claim 历史 18,724 行只有 18,277 个唯一 `claim_id`；`duplicates.jsonl` 的同一关系重复写了两次。

## 1. 来源覆盖与快照

证据文件：

- `company-kb/_digest/source-index.md`：88 条 `confluence://` 来源记录。
- `company-kb/_digest/batch-state.json`：89 个 batch，`batch_size=1`；89 个 `source_paths` 均唯一；88 个 batch 是第 1 次尝试，1 个 batch 是第 2 次尝试；所有 batch `status=succeeded`、`error=null`。
- `company-kb/_digest/source-snapshots.jsonl`：178 行、89 个唯一 `source_uri`、88 个唯一内容指纹；同一来源快照行重复出现（通常两行完全相同）。

唯一覆盖缺口是：

```text
confluence://company/emm for android /AE - AirViewer厂商管理.md
```

该来源在快照中出现两次，`validation_status=failed`，`validation_reason=source has no body`，但不在 `source-index.md` 的 88 条记录中。它不是“已发布但没有链接”，而是来源清单、快照、批次三者边界不一致，必须在验收中单独列为未完成/不可发布来源。

## 2. Claim、定位与状态

证据文件：`company-kb/_digest/claim-history.jsonl`、`company-kb/_digest/pending-review.jsonl`。

| 指标 | 数值 | 说明 |
| --- | ---: | --- |
| Claim 历史行 | 18,724 | 含成功和失败历史 |
| 唯一 `claim_id` | 18,277 | 比行数少 447 行，存在重复写入 |
| 唯一 Claim 指纹 | 7,796 | 一个指纹对应多条历史/来源记录 |
| `verified` 行 | 13,820 | `validation_status=passed` |
| `pending_review` 行 | 4,904 | `provider_failure=true` 的历史行 |
| pending-review 文件行 | 4,756 | 30 个唯一来源，全部待重试 |
| Claim 历史唯一来源 | 87 | 与 88 条 source-index 不一致 |

每条成功 Claim 都带有 `source_uri`、`content_fingerprint`、`fragment_locator`、`target_path`、`source_snapshot_ref`；失败 Claim 也保留了同一组定位字段并明确写出失败原因。这说明“字段存在”基本成立，但账本之间的数量不闭合：`claim-history.jsonl` 的 4,904 条失败历史并不等于 `pending-review.jsonl` 的 4,756 条当前待审记录，不能只看某一个文件宣布失败补偿已完成。

代表性失败样本位于：

```text
_digest/runs/run-9dd4a6afbd59447dadf77dbf425ab4b6/report.json
```

其中 `emm for android /EMM客户端页面.md` 的 Claim 记录包含 `provider request failed (deadline exceeded after 30s)`，目标为 `pages/customers/customer-overview/emm.md`，状态为 `pending_review`；这类记录应继续保持“待重试”，不能计入已验证知识。

## 3. 重复、重放与归档膨胀

### 来源重复

`_digest/source-snapshots.jsonl` 的 178 行对应 89 个唯一来源，重复快照使用相同的 `snapshot_id` 和内容指纹。若这是重试/重放，应该在账本中有明确的 attempt/重放关系；目前只是重复行，增加审计噪声，也容易被下游统计成两份来源。

### 全局重复关系重复写入

`_digest/duplicates.jsonl` 只有 2 行，但两行逐字段相同，均指向：

```text
canonical: confluence://company/merchant system/Dashboard_MerchantPortal.md
duplicate: confluence://company/merchant system/Dashboard_ResellerPortal.md
content_hash: 61f416abeb33660ff339446ca3e54a549636c94b32a593e8890b765d02c1d54e
```

因此“有重复来源记录”这个事实成立，但计数为 2 会把同一重复关系算两次；该文件不是幂等的。

### Claim 历史重复

18,724 行仅有 18,277 个唯一 `claim_id`，至少 447 行是重复 Claim 历史。重复记录本身并不等于内容丢失，但会使“Claim 总数、失败率、来源覆盖、重试成本”均被高估，必须以稳定身份（来源 + 指纹 + 定位）去重后再统计。

### 归档量

当前知识库有 120 个 `pages` 文件、27 个 `indexes` 文件、92 个运行报告目录，但 `_archive` 下已有 2,736 个文件；仅按主题页粗算约 22.8 个归档文件/当前页。归档包含导航和分页快照，不能直接判定为数据错误，但当前没有在审计报告中给出保留策略、清理结果或“归档增长是否预期”的解释，属于明显的可维护性风险。

## 4. 代表性当前页与路径证据

来源索引和 Claim 历史指向的代表性页面包括：

- `pages/products/product-capability/app-management-global-system.md`（另有 `.part-002.md`、`.part-003.md`）；成功运行报告为 `run-3378b44858414362b071106571b2a2ab`。
- `pages/products/product-capability/topic-d6d55101.md` 及两个分页；来源 `GoInsight/创建设备报告.md` 在 source-index 中明确列出三段路径。
- `pages/products/product-capability/topic-b4ca0df3.md` 及 `.part-002.md`；来源 `GoInsight/新建迁移任务.md` 明确列出两段路径。
- `pages/engineering/implementation/uptrillion.md` 及 `.part-002.md`、`.part-003.md`、`.part-004.md`；Claim 历史中单页/分页出现大量待审记录。
- `pages/customers/customer-overview/emm.md`；该页承接 EMM Android 失败批的待审 Claim，不能按普通已验证页阅读。

这些页面路径、`target_path` 和 `source_snapshot_ref` 在 Claim 记录中可追溯；但只要页面仍承接 `pending_review` Claim，就必须在读者入口或页头显式显示“待重试/未验证”，否则读者会把失败草稿当成正式知识。

## 5. 质量门误报

### “批次成功”掩盖 provider 失败

`batch-state.json` 将 89 个 batch 全部记为 `succeeded`，而失败 Claim 的 `retry_status` 仍为 `retry_next_batch_run`。这两个状态并不矛盾：它只能代表 batch 外壳完成，不能代表 provider 调用、Claim 验证和正式发布完成。当前报告没有把二者分成两个独立门禁。

### “写回成功”掩盖未完成知识

92 份 `report.json` 中：90 份 `official_write.status=written`，1 份为 `pending`，1 份为 dry-run；但全体报告的 `quality.status` 为空、`benefit_status=unmeasured`。因此 `written` 被下游误读为“最终质量通过”，而实际至少有 30 个来源等待重试、一个无正文来源未进入索引、且失败账本行数不闭合。

### 机械门禁没有覆盖读者质量

页面/Claim 的结构字段存在，并不证明分类、语义标题、重复控制和内容完整性成立。当前报告未提供“每个来源均有最终 target”“失败 Claim 不出现在正式导航”“source-index 与 snapshots/batch manifest 一致”“duplicate ledger 幂等”等可审计门禁结果；因此不能以 `make check` 或单次 `official_write=written` 代替最终产物验收。

## 6. 验收判定与最小补救

当前判定：**溯源字段大体存在，但来源覆盖、失败补偿、重复账本和质量门均未闭合；最终产物不应标记为完整验收通过。**

下一次重跑/复核至少应输出并分别判定：

1. `batch-state.sources`、`source-snapshots`、`source-index` 三方来源集合差异；无正文来源必须显式 `failed/unpublished`。
2. 以 `(source_uri, content_fingerprint, fragment_locator)` 去重后的 Claim 总数、失败数和待审数；解释 4,904 vs 4,756 的差异。
3. `duplicates.jsonl` 的幂等性（同一关系只能一行）及重复来源是否继承 canonical target。
4. provider 调用成功、Claim 验证、正式写回、语义/读者质量四个独立状态；`written` 不得覆盖 `quality=unmeasured` 或 `pending_review`。
5. 归档文件数、保留周期和清理结果，避免每次单来源批处理持续累积不可读的历史快照。
