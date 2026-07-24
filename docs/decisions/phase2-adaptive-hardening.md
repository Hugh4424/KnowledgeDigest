# Phase 2 adaptive hardening decision log

## Goal and status

Final user choice: **B — add dynamic rethink now**. This direction adds
content-driven rethink, crash-safe recovery, and one-writer admission. It does
not add concurrent-writer success, CAS retry, a scheduler, daemon, model judge,
or external index integration.

## Round 1 — problem and operating model

**Starting queue:** use quality hardening and write safety together; default
model; dynamic source; interruption recovery.

1. The user chose both quality hardening and write safety.
2. The user rejected fixed default-off and default-on, writing: “需要动态智能开关，根据内容智能判断”. The queue moved to local-vs-model decision.
3. The user chose explainable local rules with hard limits over model judging.
4. The user chose automatic recovery with no duplicate processing and no lost
   pages.

**Conclusion:** use content-driven local rules and durable recovery, not a fixed
manual switch or a model judge.

## Round 2 — bounds and conflicts

**Starting queue:** rethink limit; conflict behavior; acceptance boundary.

1. The user chose at most three rounds for high-risk content.
2. The user chose a bounded future CAS retry, then retained record on repeated
   conflict.

**Conclusion:** quality cost is bounded; any future conflict process is bounded.

## Round 3 — current writer model and final choice

**Starting queue:** current concurrency need; review findings; final scope.

1. Direction review found no evidence of current same-knowledge-base concurrent
   writes. The user chose one writer now and possible concurrency later.
2. Detail review recorded no measured Phase 0/1 quality insufficiency. The
   recovery-first candidate therefore deferred rethink.
3. The final decision card offered recovery-first, dynamic rethink now, or no
   hardening. The user replied exactly `B`, selecting dynamic rethink now with
   its stated risk.

**Conclusion:** user B supersedes the recovery-first deferment. The lack of
measured quality benefit is an accepted risk, not hidden or treated as proof.

## Decisions

### D1 — activate explainable local risk routing

- **Source:** user: “需要动态智能开关，根据内容智能判断”; user selected A for
  explainable local rules; final user answer `B`.
- **Facts and constraints:** available local signals include similarity tier,
  `new`/`revise`/`merge`, target-page count, content size/density, and coverage
  risk. There is no model judge.
- **Logic:** user rejects fixed defaults -> local signals control cost -> route
  must be visible -> local risk classification.
- **Choice and reason:** classify low, medium, and high risk using explicit
  local rules. Record signals and chosen path for every run.
- **Impact:** generation routing and run record; no new external interface.
- **Consequences and risks:** rules can miss semantic complexity or add calls.
- **Rejected alternatives:** fixed on/off, model judge, mixed judge, separate
  experimental command; each either loses automatic coverage or adds unknown cost.
- **Unresolved items:** later spec defines numeric thresholds and fixtures.
- **Supersedes:** recovery-first D1 deferment.

### D2 — high-risk rethink, maximum three rounds

- **Source:** user selected A for maximum three rounds; final user answer `B`.
- **Facts and constraints:** no measured Phase 0/1 quality shortfall exists;
  additional rounds increase latency and model cost.
- **Logic:** user accepts the stated risk -> only high risk gets extra work ->
  hard cap prevents unbounded cost -> maximum three rounds.
- **Choice and reason:** high-risk content may run up to three rethink rounds.
  Stop early only when normalized body equals the immediately preceding completed
  round byte-for-byte.
- **Impact:** generation loop, run record, and quality/cost tests.
- **Consequences and risks:** benefit is unproven; low-value extra calls remain
  possible. This is an explicit accepted risk, not an evidence claim.
- **Rejected alternatives:** defer until evidence, two/four rounds, unlimited
  rounds, unconditional multi-round generation.
- **Unresolved items:** implementation validates benefit, cost, and rule quality.
- **Supersedes:** recovery-first D2 future-only constraint.

### D3 — one writer per knowledge base

- **Source:** user selected C: concurrency may be needed later, one writer now.
- **Facts and constraints:** no current concurrent-writer requirement exists;
  current writeback has no CAS conflict implementation.
- **Logic:** no demonstrated concurrency need -> avoid a second write system ->
  reject a second current writer.
- **Choice and reason:** second writer fails before mutation with
  `CONCURRENT_WRITER_NOT_ALLOWED`; do not silently queue it.
- **Impact:** local admission and error reporting.
- **Consequences and risks:** same knowledge base cannot run in parallel.
- **Rejected alternatives:** concurrent success, silent queueing, unlimited retry.
- **Unresolved items:** future CAS values, one retry, and conflict tests.
- **Supersedes:** Round 2 CAS retry for this release.

### D4 — durable recovery reusing existing writeback

- **Source:** user selected automatic recovery; existing writeback inspection.
- **Facts and constraints:** current atomic replacement and caught-error rollback
  do not cover a forced process stop; no durable progress record exists.
- **Logic:** forced stop bypasses rollback -> preserve existing write path -> add
  minimum durable state around mutation -> safe rerun.
- **Choice and reason:** write durable `prepare` and `commit` state around the
  existing writeback path. Stable run identity permits resume or safe redo.
- **Impact:** local recovery state, restart behavior, and fault tests.
- **Consequences and risks:** state or identity errors can block recovery.
- **Rejected alternatives:** process-local rollback only, manual recovery, full
  distributed transaction.
- **Unresolved items:** later spec defines state location, schema, identity.
- **Supersedes:** atomic replacement as sufficient kill/restart protection.

### D5 — explicit deferrals and accepted risk

- **Source:** direction review, detail review, and final user answer `B`.
- **Facts and constraints:** no measured quality shortfall and no current
  concurrent-writer need. User selected dynamic rethink after seeing this risk.
- **Logic:** user authorizes bounded quality experiment -> keep its limit ->
  defer unrelated distributed and operational scope.
- **Choice and reason:** accept unproven rethink benefit/cost as a tracked risk.
  Defer concurrent success, CAS compare/retry, scheduler/daemon, external sync,
  model judge, and more than three rounds.
- **Impact:** implementation must show risk signals, round count, quality result,
  and cost; no concurrency system is introduced.
- **Consequences and risks:** the chosen rethink path can cost more without
  sufficient benefit; future parallel work remains blocked.
- **Rejected alternatives:** treating recovery as concurrent-writer support;
  hiding the absent quality evidence; unlimited automatic escalation.
- **Unresolved items:** success metric and alert/reversion threshold belong to
  the later spec.
- **Supersedes:** recovery-first D5 classifier/rethink deferral.

## Documentation and grill results

- **CONTEXT:** no change. No domain term or relationship changed.
- **ADR judgement:** hard to reverse — yes; surprising without context — yes;
  genuine quality/cost/reliability trade-off — yes. ADR 0002 is required.
- **Authority:** ADR 0002. The earlier Phase 2 plan is historical baseline.
- **Conflict handling:** historical quality-evidence gate conflicts with final
  user B. The decision preserves the evidence gap as D2/D5 accepted risk and
  requires implementation validation; it does not present the gap as resolved.
- **Exit checks:** no new external interface; implementation names deferred;
  second writer rejection and forced-stop recovery are explicit; D5 exclusions
  are frozen.
- **Verification so far:** `git diff --check` passes. No implementation,
  runtime, quality, or fault-injection evidence exists yet.

## Remaining risk

Dynamic rethink may not improve quality enough to justify its cost. Later work
must define its metric, thresholds, fixtures, and a reversion threshold. Final
user B explicitly accepts this decision-stage risk.
