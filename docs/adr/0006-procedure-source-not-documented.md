# Allow an audited source-gap state for procedure exceptions

Status: proposed (pending Task 2-B make-decision confirmation)

## Context

`procedure_or_rule` keeps a fixed `exceptions` section, but a frozen source may
contain no explicit exception trigger, handling step, branch, or recovery rule.
The current fail-closed contract would degrade the whole page. That protects
against invented claims, but it also hides other evidence-backed procedure
content. The reader must not confuse “the source did not document this” with
“the product has no exceptions.”

## Decision

- Keep `exceptions` as a required section.
- Permit the canonical section state `source_not_documented` only after a
  deterministic audit proves that the frozen source lacks explicit exception
  rules. Bind the state to the source URI, content fingerprint, and audit
  version/evidence.
- Do not create a domain Claim or generic placeholder sentence from that state.
  The exception-specific question remains `not_answerable`.
- If all other required sections and existing machine gates pass, the page may
  be `published`, enter the Reader candidate set, and count toward
  `procedure_or_rule` page-type coverage. This does not mean the exception
  question was answered.
- Ambiguous source wording, incomplete audit, provider mapping failure,
  attribution failure, or any other missing required evidence remains
  `degraded`/`not_released`.

## Scope and consequences

This is the single allowed Task 2-B body/section contract revision. It changes
only the `procedure_or_rule.exceptions` section state and its answerability
interpretation. It does not lower the six-concept threshold, the three-page-type
requirement, source attribution, fact-preservation gates, reader-quality scope,
or Task 3 release rules.

The compiler needs a replayable audit result and stable reader wording. A broad
or weak audit would turn a source gap into a false pass, so the implementation
must fail closed whenever the audit cannot prove the exact condition.

## Rejected alternatives

- Keep every missing `exceptions` section degraded: safest, but discards
  otherwise usable, evidence-backed procedure content.
- Make `exceptions` optional: hides a fixed question and breaks page-shape
  comparability.
- Treat “缺点” or another topic’s error text as exceptions: creates an
  unsupported cross-topic claim.
