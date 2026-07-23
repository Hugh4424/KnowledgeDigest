# Retain local source originals for 90 days

Knowledge Digest processes manually supplied local source snapshots and does not re-fetch external pages. It retains each complete source original and linked archive content for 90 days to support recent investigation and rollback, then deletes the original while preserving long-lived trace records, including the source address, fingerprint, fragment locator, validation time, status, and change reason. This deliberately balances recovery capability against lasting storage, privacy, and copyright exposure.

## Considered Options

- Retain complete originals indefinitely. Rejected because exposure and storage risk compound over time.
- Retain only metadata from the start. Rejected because recent loss investigations and rollback need the original material.

## Consequences

After 90 days, a claim remains traceable but its complete historical source text cannot be reconstructed. Cleanup occurs during a later manual run; no scheduler is added.
