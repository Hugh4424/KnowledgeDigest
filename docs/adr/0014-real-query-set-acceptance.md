# Accept knowledge with a real query set instead of a self-certifying gate stack

Status: accepted (make-decision task6-effect-gap-and-architecture-reset, 2026-09-12)

KnowledgeDigest removes the self-certifying quality apparatus (quality
projections, five-dimension comparison atoms, SND certificate and verifier) and
accepts knowledge by running a fixed set of real product questions against the
published pages, comparing against a frozen CompanyBrain snapshot, and requiring
that every claim resolves to a source location or is explicitly marked as not
stated in the source.

## Context

The last release reported `120/120 KD_WIN`, a triple-digest certificate and
2,280 verified coordinate references, while the published pages contained zero
content tables out of 2,943 source table rows, left 87 of 99 pages unreachable
from the entry page, and pointed readers at two audit files that did not exist.
77.9% of the reported comparison atoms were mere non-regression, and every
strict-improvement atom rested on the comparison side being recorded as absent.

## Decision

- No self-assessment result may be used as evidence that the artifact is usable.
- Acceptance is a real query set: the same questions asked of the new pages and
  of a frozen CompanyBrain snapshot, judged per question, with "comparison side
  has no such content" recorded as uncovered rather than as a win.
- Every published conclusion carries a source location or an explicit
  "not stated in the source" marker; there is no percentage threshold and no
  conclusion without provenance.
- Cost is accepted at the current order of magnitude (~150 provider calls per
  run), but wall-clock, call count and token/cost must be recorded for both
  successful and failed runs.

## Consequences

- The project loses its automated green light; failures become visible as failed
  questions instead of a passing report.
- Judging requires a human-authored question set and a frozen comparison
  snapshot, which must be rebuilt whenever the comparison baseline changes.
