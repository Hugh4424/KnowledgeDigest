# Local independent review — 2026-08-10

Scope: current D-004 Phase 4 implementation, plan and task projection. This is a local read-only review, not a WorkflowHub provider verdict.

Findings and disposition:

- Fingerprint semantics were clarified: `source_hash_match` means audited source/selection/claim fingerprint consistency, not rereading external raw bytes; this remains explicit in decision/spec/evidence.
- Locator checks were tightened to require the current fixture footnote, `lines:N[-N]` locator syntax, non-empty target path, and no absolute/parent escape. Semantic entailment remains deferred to Task 2-C.
- Fixture source selection is now bound to the TopicIndex row's `source_members` and matching `evidence_refs`.
- Validator now rebuilds canonical input fingerprints for full inputs, reconciles frontmatter events with audit events exactly, checks audit `topic_id`, and rejects missing events even when input context is omitted.
- `stale_after` now requires a real ISO date; explicit valid freshness is projected and invalid dates fail closed. No freshness input still omits the field.
- Mutation policy was made explicit: content/source/locator/target/page-type/event changes make validation fail closed and preserve audit for diagnosis; the validator does not silently rewrite the current Bundle to degraded.
- Plan status, duplicate FR status rows, and Phase 4 routing were reconciled with the actual implementation.

Result: no unresolved implementation finding in this local review. Formal WorkflowHub review/receipt remains unavailable because the host dispatch returned `bundle sha256 mismatch: scripts/review-materials.mjs`.
