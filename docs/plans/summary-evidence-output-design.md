# Summary + Evidence 输出契约

## 目标

让 LLM 负责“压缩表达”，让系统负责“完整留证”。正式页顶部提供可读摘要，所有源 claim 仍进入 Evidence 区和 S6 provenance；摘要不能替代证据。

## 输出形态

S4 草稿增加一个可拒绝的 `summary` 字段：

```json
{
  "summary": {
    "status": "validated",
    "segments": [
      {
        "summary_id": "summary-1",
        "text": "一句可读的归纳。",
        "supports": [
          {"target_path": "pages/digest/draft-1.md", "claim_fingerprint": "..."}
        ]
      }
    ]
  },
  "claims": [],
  "coverage_mapping": []
}
```

`claims` 和 `coverage_mapping` 仍必须覆盖全部输入；`summary.segments[].supports` 只允许引用输入 claim fingerprint，不得引用不存在的 claim。摘要不通过校验时，整簇降级为“无摘要、保留完整证据”。

S4 将 `final_body` 组装为：

```markdown
## Summary

- 摘要句。[evidence: summary-1]

## Evidence

- 原始 claim 1
- 原始 claim 2
```

Evidence 由已验证的 claims 确定性生成，不能由模型删减或改写。现有 `## Provenance` 继续由 S5/S6 维护。第一版不要求模型生成跨批全局摘要；每批摘要先合并，冲突或引用不完整时回退。

批次调用使用有界并发：`llm_batch_concurrency` 默认 `4`，仅并行执行互不依赖的 provider batch；结果按 `batch_index` 原序合并。任一 batch 失败仍使整份 draft 走完整 Evidence fallback；并发只缩短等待，不改变事实、coverage、faithfulness、S5 或 S6 门禁。provider 限流时可将该配置降为 `1` 或 `2`。

## 门禁

1. Evidence 的 claim 数、fingerprint 多重集、source lineage、coverage、结构行和 faithfulness 与现有门禁完全一致。
2. 每个 summary segment 至少有一个 `supports`；每个 support 必须存在于本簇 claims 和 coverage_mapping。
3. `supports` 不能引用被标为 unsupported 或失败来源的 claim。
4. Summary 文本不能为空；摘要长度只作为质量指标，不作为唯一通过条件。
5. 任一摘要绑定失败，summary 标为 `rejected`，但 Evidence 继续保留；Evidence 失败才沿用整簇回退。

## 质量指标

- `evidence_retention_ratio`：必须为 `1.0`。
- `summary_reference_coverage`：摘要引用的 claim 是否全部存在，必须为 `1.0`。
- `summary_compression_ratio`：Summary 字符数 / 输入有效字符数，先记录，不先拍硬阈值。
- 人工 `summary_fidelity`：10 条标注样本逐条判定；出现新增事实、方向性错误或关键条件丢失即失败。

## 最小实施顺序

1. 先锁定 10 条人工样本和期望摘要。
2. 扩展 provider JSON schema、S4 聚合和回退门禁。
3. 只用离线固定 generator 验证门禁，再用 qwen 做一次真实 A/B。
4. 只有人工摘要 10/10、Evidence 10/10、S6 完整且重放稳定，才考虑扩大样本。

## 明确不做

- 不删除或折叠正式 Evidence 内容。
- 不把摘要引用当作 provenance 的替代品。
- 不用“coverage=1”推断摘要正确；摘要正确性必须单独人工验收。
- 不在本阶段同时更换 S3 相似度算法或 provider 路由。
