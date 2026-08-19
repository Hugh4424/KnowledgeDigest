# Task4 P1 repair: structured reader body and baseline mapping

## Goal

Repair the two defects that make the current real 89-source candidate unlike CompanyBrain:

1. compile source sections into reader-facing usage, procedure, boundary, diagnostic, FAQ, and table blocks;
2. establish a deterministic, unique, hash-bound CompanyBrain mapping artifact for batch comparison.

## Files and symbols

- `src/knowledge_digest/task4_reader_quality.py`: `_clean_content_line`, `_sections`, `_extract_content`, topic content merge, `_render_page`.
- `tests/acceptance/test_task4_full_compiler.py`: red/green body-structure acceptance tests.
- `scripts/` or `src/knowledge_digest/`: mapping generator only if the existing comparison contract has no reusable mapping seam.
- `config/`: mapping fixture only; never hardcode the 89 paths in renderer logic.

## Acceptance

- markdown tables remain tables with header/cell boundaries and source line claims remain traceable;
- reader pages expose edited sections, not a flat cleaned-source dump;
- diagnostic content is not fabricated by repeating procedure content;
- document directory, revision history, image URLs, and internal audit fields do not leak into Reader;
- unique CompanyBrain matches are machine-generated and bound to a frozen manifest/hash; ambiguous or missing matches remain explicit and cannot claim superiority;
- existing evaluator, fail-closed status, and 89-source coverage behavior remain intact.

## Non-goals

- no LLM/provider call;
- no manual per-page review queue;
- no change to the confirmed product decision/spec or formal release gates;
- no modification of CompanyBrain or the original 89 files.

## Test route

Feature route, `backend-testing`: focused acceptance tests first, then full aggregate after review.

## Stop condition

Stop with `not_released` if the empty fifth-byte source, missing baseline match, ambiguous mapping, page overflow, or any source/claim/navigation failure remains. A green unit test run alone does not prove the real 89 package is better than CompanyBrain.
