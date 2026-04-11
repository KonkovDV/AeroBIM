---
title: "AeroBIM Documentation Map"
status: active
version: "0.1.0"
last_updated: "2026-04-08"
tags: [aerobim, documentation, navigation, reference]
---

# AeroBIM Documentation Map

## Purpose

This file is the local documentation router for `AeroBIM`.

Use it to find the current active documents quickly instead of treating the whole folder as a flat archive.

## Recommended Reading Order

1. `06-architecture-reference.md` — canonical architecture reference.
2. `02-microphoenix-extraction.md` — why the project extracts only a subset of MicroPhoenix.
3. `08-microphoenix-adoption-matrix.md` — exact keep/adapt/defer/reject decisions.
4. `09-implementation-and-verification-rails.md` — how work should be delivered and verified.
5. `04-atomic-backlog.md` — execution-ready backlog.
6. `03-openbim-landscape.md` — standards, tooling, and competitor frame.
7. `05-fact-check-audit.md` — evidence and corrected audit notes.
8. `07-project-skeleton.md` — current filesystem skeleton and placeholder surfaces.
9. `01-strategy-and-plan.md` — product thesis and phased plan.

## Document Modes

| File | Dominant mode | Purpose |
|---|---|---|
| `01-strategy-and-plan.md` | explanation | product thesis, phases, success criteria |
| `02-microphoenix-extraction.md` | explanation | extraction logic and architectural translation |
| `03-openbim-landscape.md` | reference + explanation | external standards, tools, and market frame |
| `04-atomic-backlog.md` | reference | executable task inventory |
| `05-fact-check-audit.md` | evidence | verified claims and corrected findings |
| `06-architecture-reference.md` | reference | canonical technical architecture |
| `07-project-skeleton.md` | reference | directory structure and placeholder policy |
| `08-microphoenix-adoption-matrix.md` | reference | exact extraction decisions from MicroPhoenix |
| `09-implementation-and-verification-rails.md` | how-to | operational build and verification discipline |

## Rules For Future Docs Work

- update the authority source before mirrors or summaries;
- preserve fact-check evidence separately from the active architectural reference;
- do not add speculative runtime claims without either repo proof or authoritative external evidence;
- keep frontend and Revit-plugin docs explicitly boundary-first until those runtimes exist.