# Candidate acceptance boundary

This is a direction-stage acceptance draft, not an implementation specification.

## AC1 — visible bounded rethink

Every run record contains local risk signals, assigned risk class, selected path, and rethink round count. A fixture that activates a documented high-risk rule executes at most three rounds. It stops before the cap only when the normalized digest body is byte-identical to the immediately preceding completed round. A low- or medium-risk fixture executes exactly one round.

## AC2 — single writer

While a write for knowledge base K is active, a second write request for K fails before page mutation with `CONCURRENT_WRITER_NOT_ALLOWED`. No queue, scheduler, or background process is introduced.

## AC3 — forced-stop recovery

For stable run identity R and target page set P, force termination immediately after durable `prepare` and immediately after durable `commit`. The next run with R reads durable state and ends with exactly one committed completion and exactly P: no duplicated page completion and no missing page.

## AC4 — preserve existing rollback

Inject a caught write error after at least one page mutation in a multi-page batch. Every target page remains byte-identical to its pre-run content, and the failed recovery state is not committed. Durable state wraps existing atomic replacement, rollback, and reporting instead of replacing them.

## AC5 — evidence and risk visibility

The implementation shows a reproducible quality metric, cost per risk path, and a reversion threshold. Until measurements exist, run records state that rethink benefit is unproven. This is an accepted product risk, not a claim that quality insufficiency has already been measured.

## AC6 — exclusions

No acceptance claim covers concurrent writer success, CAS comparison or retry, silent queueing, scheduler/daemon behavior, model judging, external index sync, or more than three rounds.
