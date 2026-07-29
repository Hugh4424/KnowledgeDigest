# Use adaptive hardening with a single writer

Status: deprecated

Phase 2.5 removed durable recovery state and reduced rethink to one round. Current behavior uses a CLI lock, archives originals before writing, accepts that an extreme failure may leave a partial batch, and recovers by rerunning.

Knowledge Digest will add crash-safe write recovery and adaptive rethink now. Explainable local content signals choose the path: low and medium risk remain single-pass; high risk may use at most three rethink rounds and stops early only when its normalized digest body is byte-identical to the immediately preceding completed round. The user explicitly accepted this direction despite the absence of measured Phase 0/1 quality insufficiency; quality benefit and cost are therefore accepted risks to validate in implementation. The release retains one writer per knowledge base and reuses existing atomic replacement and caught-error rollback, adding durable prepare/commit recovery state around it. Full concurrent-writer support, including CAS conflict handling, remains deferred.

## Considered Options

- Defer adaptive rethink until measured quality evidence exists. Rejected by the user's final B choice; it would delay the chosen content-driven improvement.
- Enable every hardening step for every run. Rejected because cost and latency would be uncontrolled.
- Keep the existing single-pass, process-local rollback only. Rejected because forced interruption has no durable recovery path.
- Support concurrent writers now. Deferred because no current concurrent operating requirement is established.

## Consequences

The command must make local risk signals, selected rethink path, round count, recovery state, and the quality-risk warning visible in the run record. A second writer to the same knowledge base is rejected with the `CONCURRENT_WRITER_NOT_ALLOWED` error in this release. Implementation must validate quality benefit and cost before treating the new path as proven. A later concurrency decision must define CAS conflicts and acceptance tests.
