# Write KnowledgeDigest pages into the existing semantic layer

Status: accepted (make-decision task6-effect-gap-and-architecture-reset, 2026-09-12)

KnowledgeDigest stops emitting a self-contained bundle format and instead writes
pages into the user's existing semantic knowledge layer
(`/Users/Hugh/Hugh/Knowledge/CompanyBrain`), reusing that layer's frontmatter
contract, directory/naming rules and `[[wikilink]]` cross-links, so the
retrieval layer (`gbrain`) and downstream skills/agents can consume the pages
without a conversion step. One topic has exactly one producer: KnowledgeDigest
takes over that topic from the legacy `tools/synthesize_*` scripts only after a
read-only side-by-side comparison shows no regression.

## Context

The previous release produced 99 pages in its own layout with its own
`page_type`/`digest_*` metadata and relative Markdown links. The semantic layer
already consumes a different contract: `type` (open vocabulary),
`page_model: source|derived|curated`, `tier`, `trust`, `source_status`,
`quality_status`, derived `scope`/`product`/`section`, and `[[wikilink]]`. The
contract's single executor is `tools/apply_formal_knowledge_metadata.py`, whose
`page_model_for()` classifies any page carrying a `generated_by` value as
`derived`; `normalize_product_note_names.py` protects only `manual_only: true` /
`page_model: curated` pages and otherwise overwrites a same-named target before
unlinking the source.

## Decision

- KnowledgeDigest output is semantic-layer content, not a parallel bundle.
- The layer's frontmatter contract, naming rules and link style are the
  authority; KnowledgeDigest conforms to them.
- Only one producer may own a given topic path. KnowledgeDigest replaces the
  legacy per-product synthesis scripts for the topics it covers, after a
  read-only comparison; until that switch is registered in the automation's
  rules, the automation must not be pointed at KnowledgeDigest output.
- Exactly one new page-level field may be introduced for provenance, and it must
  be registered in the layer's metadata authority; its literal name and value
  shape are fixed in build-spec.

## Consequences

- The stalled daily automation becomes a live hazard rather than a neutral
  neighbour: when restored without the producer registry above, it may rename or
  delete KnowledgeDigest pages.
- Traceability now depends on one registered field plus in-page evidence blocks,
  so field-less legacy consumers keep working.
