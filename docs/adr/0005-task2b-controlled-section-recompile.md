# Use dependency-checked section recompilation for Task 2-B updates

Status: proposed (pending Task 2-B make-decision confirmation)

Task 2-B updates normally recompile only sections whose source, claim, version,
or structural dependencies changed. A section may be reused only when its full
dependency set and attribution are proven unchanged. If the impact cannot be
proved, the compiler recompiles the whole page. If that recompilation fails,
the page becomes `degraded` and the previous formal Reader page is not
overwritten.

## Context

The user selected section-level incremental updates to avoid unnecessary page
churn, while explicitly requiring an impact assessment so an old section does
not retain an outdated statement. The existing project already separates
Reader pages from Audit/Archive and uses page-level `published`/`degraded`
states, so a failed update must remain visible without replacing the last
formal page.

## Decision

- Every compiled section records its source, claim, version, structure, and
  related-section dependencies.
- A changed dependency invalidates the section and the transitive dependency
  closure.
- Uncertainty expands the affected set to the whole page; it never silently
  reuses the old section.
- A failed page recompile writes only degraded/audit evidence and preserves the
  previous formal Reader output.
- This ADR applies only to the Task 2-B body compiler; it does not add a
  general dependency engine or permanent candidate queue.

## Considered alternatives

- Recompile the whole page for every source change: safer but causes avoidable
  provider cost and reader-visible churn.
- Keep unaffected-looking sections when impact is uncertain: cheaper but can
  leave stale or internally inconsistent content.
- Keep old Reader content and put every update in Audit: safe but updates do
  not become usable without an unplanned manual workflow.

## Consequences

The compiler and validator must maintain a replayable dependency record and a
clear conservative fallback. The normal case has lower churn; the uncertain
case has higher provider cost. Failures remain explicit as `degraded` and the
delivery remains `not_released`.
