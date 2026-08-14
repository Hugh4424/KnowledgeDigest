# Use summary confirmation instead of full manual reader review for Task 3

Status: accepted (confirmed in Task 3 make-decision)

Task 3 keeps the package-level `released` / `not_released` distinction, but does not require a person to read every generated page, answer every reader question, or inspect the source chain. The full fixed reader question set remains automated. A person only confirms that the automated result summary is complete, understandable, and has no explicit blocking failure.

## Decision

- Machine hard gates remain required for source, Claim, structure, completeness, integrity, and failure isolation.
- The full Task 3 reader question set remains an automated gate: at least 15/17 positive first hits and 0/3 negative false hits.
- Non-blocking warnings remain visible in the summary and Audit record but do not prevent `released`.
- The human action is **summary confirmation**, not content review. It must not create `human_reviewed`, `verified`, or a human content trust tier.
- Missing, malformed, incomplete, contradictory, or failed automatic results remain blocking and keep the package `not_released`.
- Task 3 includes a minimal confirmation fact bound to the run: the summary was complete and decidable, no hard failure remained, and the confirmation actor/time were recorded. Only the serialized field name and storage path are deferred.
- Task 3 includes the minimum hard-failure / warning / undecidable classification and display. Cosmetic presentation details may be deferred; unknown or unclassifiable signals are hard failures.

## Alternatives rejected

- Full manual reader review: too expensive for the user and does not scale to the 89-source package.
- No human action at all: simpler, but removes the last check that the automated run actually completed and is interpretable.
- Case-by-case warning decisions: flexible but inconsistent and recreates a manual review queue.

## Consequences and risks

This makes release materially easier: the user checks one summary instead of the knowledge content. It also means `released` no longer implies that a person read the正文. Automated reader evaluation, deterministic provenance checks, hard failure classification, and visible warnings must therefore remain replayable and fail closed.

The exact serialized field and receipt shape for summary confirmation are downstream material decisions. They must preserve the domain distinction above and cannot reuse `human_reviewed`.
