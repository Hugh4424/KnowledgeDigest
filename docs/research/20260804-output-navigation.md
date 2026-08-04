# Task2 final9 output/navigation audit (2026-08-04)

## Scope and method

Read-only inspection of `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804` on 2026-08-04. I inspected the directory tree and the published Markdown, counted files/lines/metadata, resolved local Markdown links, and checked the `Home.md` navigation graph. No code, output, input corpus, or provider/model was changed or called.

## Output shape

The package root has three entries:

```text
README.md
company-kb/
comparison/
```

`README.md` points to `company-kb/Home.md` (line 3). `comparison/` contains `COMPARISON.md` and `COMPARISON.json` but is described only as inline code in the README (line 14), not a clickable link.

`company-kb/` contains the reader surface and operational evidence:

```text
company-kb/
  README.md  Home.md  kb.structure.md  .digest.lock
  indexes/    27 Markdown files
  pages/      120 Markdown topic-part files
  _queues/    2 Markdown queue files
  _digest/    2,084 files (92 run directories)
  _archive/  2,736 files (88 archived run directories)
```

Measured totals: 4,973 files and 1,179 directories below `company-kb`; `du -sh` is about 279 MB for the complete package. `_digest/` is about 237 MB (mostly `claim-history.jsonl`, 20.3 MB, and run evidence); `_archive/` is about 36 MB; current `pages/` is about 4.9 MB.

The 89-batch manifest (`_digest/batch-state.json`) records `batch_size: 1`, 89 batches, all `succeeded`; one batch has `attempt: 2`. The source index has 88 source rows: 56 `published`, 31 `needs-review`, and 1 `duplicate`. Its 123 target path references all resolve to existing files, but `target_paths` are plain table text, not Markdown links (`source-index.md` lines 9 onward).

## Reader navigation

The intended route is present and works:

```text
package README
  -> company-kb/Home.md
     -> six parent indexes (customers, engineering, operations, other, principles, products)
        -> category indexes
           -> topic pages
```

`Home.md` additionally links `indexes/pending.md` under “待复核”. There are 27 indexes total: 6 parent indexes plus 21 category indexes declared in `kb.structure.md`. Of those category indexes, only 8 contain topic links:

| Parent/category | Page files |
| --- | ---: |
| customers/customer-overview | 26 |
| engineering/architecture | 1 |
| engineering/development-practice | 1 |
| engineering/implementation | 18 |
| operations/management | 19 |
| principles/content-standard | 1 |
| products/product-capability | 51 |
| products/product-operations | 3 |

The remaining 13 category indexes are valid but empty (`business-principle`, `competitor`, `customer-case`, `delivery-standard`, `event`, `market-feedback`, `operations-troubleshooting`, `pending`, `people`, `product-boundary`, `product-overview`, `project`, `unclassified`). This explains why the “待归类” Home link opens an empty page even though `_queues/needs_review.md` has 31 provider-failure entries. The queue is documented in the package README but is not linked from Home or the category indexes.

Graph check over current (non-archive) Markdown: 148 files are reachable from `Home.md` (Home + all 27 indexes + all 120 pages); every page is exactly three local clicks from Home; 149 relative local links were checked and 0 were broken. The package-root README’s single local link also resolves. `_digest/`, `_queues/`, `kb.structure.md`, and `company-kb/README.md` are intentionally outside the Home graph (except `company-kb/README.md` is a separate entry point).

There are also 710 HTTP(S) links and 115 absolute `/wiki/...` links embedded in source evidence. These are external/source links, not local navigation targets; the absolute Confluence-style links cannot be resolved within the downloaded package.

## Page naming and structure

All 120 page files have the required managed header fields (`managed_by`, `digest_kind: topic`, `digest_topic_id`, `digest_published_path`, `digest_part`), all have an H1, and all are at or below the 300-line limit (maximum exactly 300 lines: `pages/products/product-capability/ios-c773e58c.md`). There are 86 distinct stable `digest_topic_id` values. Page-part distribution is 86 part-1 files, 24 part-2, 8 part-3, 1 part-4, and 1 part-5; 24 topics therefore span multiple files.

H1 titles are semantic: none is a raw `topic-<hash>` heading. However, 27/120 filenames still use the generic `topic-<hex>` form (21 distinct topics), and a further 24 use an 8-hex suffix (for example `ae-73c408bf.md`). Index labels and H1s are readable, but these path names remain opaque when a file is opened outside the index.

Representative good path/title pairs include:

```text
pages/products/product-capability/12-goinsight-dc.md       # 12. GoInsight DC部署方案
pages/products/product-capability/topic-d6d55101.md        # 创建设备报告
pages/operations/management/topic-3e249ded.md              # 指标详情页
pages/customers/customer-overview/emm.md                   # EMM客户端页面
```

## Findings

1. The primary reader path is usable: `Home -> parent -> category -> page` reaches all 120 current pages with no broken local links.
2. The output is structurally much clearer than a flat page dump, but the package still has many empty taxonomy pages and a large hidden operational surface; users should stay on Home/indexes/pages for reading.
3. “待复核” is not reader-complete: Home lands on an empty `pending.md`, while 31 provider-failure sources are only visible through `_queues/needs_review.md` and 31 `needs-review` source-index rows.
4. Source provenance is discoverable but not click-through: `_digest/source-index.md` stores existing target paths as plain text, so a reader must copy paths manually.
5. Semantic H1/index labels are present, yet 51/120 filenames retain hash material (27 generic topic hashes plus 24 hash-suffixed names), so path-level readability is only partial.

