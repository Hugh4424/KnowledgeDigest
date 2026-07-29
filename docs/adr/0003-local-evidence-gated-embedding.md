# Gate local embedding adoption on corpus evidence

Knowledge Digest sends company Confluence text only to a local OpenAI-compatible embedding service. Its own JSON configuration is the authority for the local base URL, model, expected dimension, and calibration-artifact path; secrets stay in environment variables, and agentmemory/OpenViking configuration is never reused. Embedding becomes the default only when a versioned calibration artifact binds the local model, vector dimension, isolated corpus, user-confirmed gold labels, calibrated thresholds, and an independent holdout result with no new false matches, at least one strict improvement over Jaccard, and no regression elsewhere. If the gate fails, the tool and `not_adopted` evidence are delivered while Jaccard remains active.

## Consequences

Successful vectors may be cached across retries, but one digest run never mixes embedding and Jaccard scores. If embedding fails, that run restarts S2 with Jaccard and records the fallback. External embedding APIs, vector databases, agentmemory integration, production-index replacement, and scheduling remain outside Phase 4.
