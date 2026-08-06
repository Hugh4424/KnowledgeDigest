---
roots: [pages, _archive, _queues]
why_field: why
version_field: version
taxonomy_version: 1.0.0
taxonomy_owner: KnowledgeDigest maintainers
taxonomy_change_policy: SemVer; maintainers edit kb.structure.md
publication_home: Home.md
publication_index_root: indexes
publication_source_index: _digest/source-index.md
publication_categories:
  - id: pending
    title: 待归类
    topic_dir: pages/pending
    parent_id: other
topic_axis_enabled: true
topic_axis_root: pages/topics
---
<!-- KnowledgeDigest:ProductGazetteer -->
```json
{
  "entries": [
    {
      "aliases": ["AT"],
      "canonical": "Atlas",
      "kind": "product",
      "object_intents": ["billing"],
      "owner": "team-a",
      "reason": "controlled",
      "source_refs": ["fixture:1"],
      "status": "canonical"
    },
    {
      "aliases": ["Pay"],
      "canonical": "Checkout",
      "kind": "module",
      "object_intents": ["billing"],
      "owner": "team-a",
      "reason": "controlled",
      "source_refs": ["fixture:1"],
      "status": "canonical"
    },
    {
      "aliases": [],
      "canonical": "Candidate Product",
      "kind": "product",
      "object_intents": [],
      "owner": "",
      "reason": "needs confirmation",
      "source_refs": [],
      "status": "candidate"
    },
    {
      "aliases": [],
      "canonical": "Beacon",
      "kind": "product",
      "object_intents": ["export"],
      "owner": "team-b",
      "reason": "controlled",
      "source_refs": ["fixture:2"],
      "status": "canonical"
    },
    {
      "aliases": [],
      "canonical": "Reports",
      "kind": "module",
      "object_intents": ["export"],
      "owner": "team-b",
      "reason": "controlled",
      "source_refs": ["fixture:2"],
      "status": "canonical"
    }
  ],
  "match_order": ["canonical", "alias", "parent_path", "h1_title", "candidate"],
  "owner": "KnowledgeDigest maintainers",
  "schema_version": "1.0.0"
}
```
