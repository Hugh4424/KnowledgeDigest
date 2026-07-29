# Summary + Evidence 人工验收样本

日期：2026-07-28

样本来自本次真实语料 A/B 试验，先固定事实，再评估模型摘要。每条必须同时检查：摘要没有改变含义；摘要引用了对应 claim；Evidence 保留原文和 source fragment。

| ID | 来源 | 期望摘要 | 必须保留的限定 |
|---|---|---|---|
| G1 | goinsight-loss-report.md:76 | 同一批 Confluence 页面在 2026-03-29 至 2026-04-17 期间被重复抓取约15次。 | 时间范围、约15次 |
| G2 | goinsight-loss-report.md:102 | `select_detail_lines()` 每篇最多选12行细节，且最多引用3篇源文档。 | 12行、3篇 |
| G3 | goinsight-loss-report.md:113 | `usable_content_line()` 会丢弃以问号结尾的 FAQ 原始问题和疑问句。 | 问号规则、丢弃 |
| G4 | goinsight-loss-report.md:139 | 抓取失败但只剩 Confluence 外壳的文档仍可能进入来源索引，造成虚假可追溯性。 | 抓取失败、外壳、索引 |
| S1 | sleep-curator-report.md:79 | 索引同步完全依赖外部 `ov` CLI 子进程，当前没有 HTTP 等价路径。 | 100%、外部 CLI、无 HTTP |
| S2 | sleep-curator-report.md:80 | embedding 客户端复用 `ovmc/embedding.py`，默认读取 OpenViking 的 `ov.conf`，没有独立 embedding 层。 | 复用、默认配置、无独立层 |
| S3 | sleep-curator-report.md:81 | LLM 协议兼容 OpenAI，但容错逻辑针对 DeepSeek 特征调整，换 provider 不保证行为一致。 | 协议、DeepSeek、换 provider |
| O1 | ov_find_maxstore_retrieval_report.md:70 | `ov find` 默认查全库，会把 memory、resource、skill 一起打分。 | 默认全库、三类范围 |
| O2 | ov_find_maxstore_retrieval_report.md:72 | 限定 maxstore 应使用 `viking://resources/maxstore/` 并指定 `--context-type resource`。 | URI、context type |
| O3 | ov_find_maxstore_retrieval_report.md:74 | 验证时 maxstore 已完成998条 embedding，仍有511条排队；overview/abstract 落后不影响 Level 2 命中。 | 998、511、Level 2 |

## 判定规则

- 事实保留：10/10 Evidence claim 与原文 fragment 精确对应。
- 摘要正确：10/10 不新增事实、不改变数字/范围/因果、不丢失“可能/默认/仍有”等限定。
- 引用正确：10/10 summary item 的 claim fingerprint 和 source URI 正确。
- 可读性：至少 8/10 摘要比原始逐字堆叠更短且更易读；否则结论为“安全但无收益”。
- 任一事实或溯源失败，结论不得进入正式试用；即使其余样本通过也一样。
