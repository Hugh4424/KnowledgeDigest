# Use an explicit Agent-only reader gate for Task 2-C

Status: proposed (pending final make-decision confirmation)

Task 2-C uses an Agent-only reader gate for its frozen small corpus because the user explicitly accepted replacing the independent-human requirement. The Agent reads only the Reader Package, while `agent_assisted=true`, `review_mode=agent_only`, and `gate_actor=agent` make the exception explicit; this does not create `human_reviewed`, `verified`, a trust tier, or a `released` package. The choice is limited to Task 2-C and carries the risk of model self-validation, so the scorecard, prompt, model, seed, evidence, and failures must be replayable.
