# Research: Phase 0 Knowledge Digest Plan

## Decision

Build-plan does not add new product scope. It converts the approved Phase 0 spec into a document-writing and implementation-order plan for a manual `digest(new_dir, kb_dir)` loop.

## Inputs Reviewed

- Upstream spec: `specs/kd-phase0-digest-spec/spec.md`
- Decision log: `tasks/kd-phase0-digest-spec/decision-log.md`
- Existing delivery document: `docs/plans/phase0-implementation-spec.md`

## Findings

1. The required surface is file-based: CLI parameters, two directory contracts, a KB structure file, per-stage JSONL/Markdown artifacts, and atomic Markdown writes.
2. The main design risk is information loss: truncation, format-based filtering, empty-shell sources entering provenance, unsupported claims, and half-written pages.
3. The plan should stay document-first: no scheduler, graph database, persistent queue, CAS/journal, two-phase commit, or human-review product flow.
4. The downstream implementation can be ordered into three stages: contract scaffolding, S1-S4 processing, S5-S6 writeback/provenance plus acceptance sample.

## Minimal Path

Use the existing filesystem and Markdown contract described by the spec. Add only the files and code needed for the manual CLI, stage outputs, queue files, run reports, and acceptance sample.
