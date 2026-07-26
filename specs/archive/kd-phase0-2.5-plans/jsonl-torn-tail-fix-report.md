# append_jsonl torn-tail fix (BLOCKER, pi/k3 round 4)

## Problem
`append_jsonl` in `src/knowledge_digest/jsonl.py` detected a torn tail (file not
ending in `\n`, i.e. a half-written line from a crashed prior write) and sealed
it by prepending `"\n"` to the new payload. This converted a torn *last* line
(which `read_jsonl` tolerates and skips) into a permanent *middle* line, which
`read_jsonl` always treats as real corruption and raises `ValidationError` on.
Since ledgers are append-only and never rewritten, this corrupted line would
persist forever and every subsequent run would crash at the same place —
non-self-healing.

## Fix
Changed `append_jsonl` (lines ~84-98) to `os.ftruncate` the descriptor back to
the last `\n` boundary when a torn tail is detected, discarding the incomplete
line entirely, then appending the new payload normally. This mirrors
`read_jsonl`'s own tolerance semantics: the torn last line is treated as if it
never happened.

```python
if os.lseek(descriptor, 0, os.SEEK_END) > 0:
    existing = path.read_bytes()
    if not existing.endswith(b"\n"):
        truncate_at = existing.rfind(b"\n") + 1
        os.ftruncate(descriptor, truncate_at)
_write_all(descriptor, payload.encode("utf-8"))
os.fsync(descriptor)
```

fsync/lock ordering unchanged: truncate happens before `_write_all`, and the
single `os.fsync(descriptor)` after the write still covers both the truncation
and the new payload (truncate + write + fsync all occur while holding the same
open descriptor, before `os.close` in the `finally` block).

## Tests changed
File: `tests/acceptance/test_phase2_5_append_only_durability.py`

1. `test_truncated_trailing_line_does_not_destroy_earlier_records` — updated.
   Previously asserted that after appending past a torn tail, a *second*
   `read_jsonl` call raises `ValidationError` (asserting the old bug's
   behavior as correct). Now asserts the ledger has exactly 3 clean lines
   (`a`, `b`, `c`) and no residual corruption.
2. `test_torn_tail_is_discarded_not_sealed_so_the_ledger_self_heals` — new.
   Simulates a crash mid-write (half-written record with no trailing `\n`),
   appends a new record, and asserts:
   - `read_jsonl` returns exactly `["a", "b", "c"]` with no `ValidationError`.
   - The torn record's partial text (`"half-writ"`) is not present anywhere
     in the file.
   - The file still ends with `\n`.

## Mutation verification
Manually reverted the `ftruncate` fix back to the old `payload = "\n" + payload`
seal behavior (kept everything else, including the descriptor-open logic and
error paths, unchanged) and reran:

```
uv run pytest tests/acceptance/test_phase2_5_append_only_durability.py -q
```

Result: 2 failed, 8 passed — both the updated existing test and the new test
failed with `ValidationError: invalid JSONL at line 3: Unterminated string
starting at`, confirming they actually catch the regression rather than being
vacuously true. Restored the ftruncate fix afterward.

## Final verification
```
uv run pytest tests/ -q
```
Result: `131 passed` (130 baseline + 1 new test), no regressions.

## Files touched
- `src/knowledge_digest/jsonl.py` (append_jsonl body)
- `tests/acceptance/test_phase2_5_append_only_durability.py` (1 test updated,
  1 test added)

当时按任务指示未单独 commit；已随 Phase 2.5 closeout 合入 `c075570`。
