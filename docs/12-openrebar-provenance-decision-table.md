---
title: "OpenRebar Provenance Escalation Decision Table"
status: active
version: "1.0.0"
last_updated: "2026-04-19"
tags: [aerobim, openrebar, provenance, escalation, operations]
---

# OpenRebar Provenance Escalation Decision Table

## Purpose

This document defines how AeroBIM handles OpenRebar provenance warnings in:

- `advisory` mode
- `enforced` mode

Source of truth for implementation:

- `backend/src/aerobim/application/use_cases/analyze_project_package.py`

## Policy Summary

- `advisory`: keep provenance findings as warnings.
- `enforced`: escalate only `critical` and `major` classes to errors.
- `minor` findings remain warnings even in `enforced` mode.

## Rule Classification

| Rule ID | Class | Advisory Mode | Enforced Mode | Operator Interpretation |
|---|---|---|---|---|
| `OPENREBAR-CONTRACT` | critical | warning | error | Contract mismatch breaks trust boundary; block report as failed in enforced mode. |
| `OPENREBAR-PROVENANCE-DIGEST` | critical | warning | error | Digest mismatch indicates stale or substituted source; treat as blocking in enforced mode. |
| `OPENREBAR-PROVENANCE-REFERENCE-MISSING` | critical | warning | error | Missing reference digest disables stale-detection; enforce strict traceability in enforced mode. |
| `OPENREBAR-OPT-FALLBACK` | major | warning | error | Fallback optimizer path may degrade optimization guarantees; fail in enforced mode. |
| `OPENREBAR-OPT-STRATEGY` | major | warning | error | Non-HiGHS strategy weakens expected optimization profile; fail in enforced mode. |
| `OPENREBAR-WASTE-METRIC-MISSING` | major | warning | error | Missing waste metric blocks threshold governance; fail in enforced mode. |
| `OPENREBAR-WASTE-THRESHOLD` | major | warning | error | Waste exceeds configured threshold; fail in enforced mode. |
| `OPENREBAR-PROJECT-CODE` | minor | warning | warning | Project naming mismatch is important but non-blocking unless operator escalates manually. |

## Operational Notes

1. `enforced` mode is intended for release-readiness and contract-sensitive runs.
2. `advisory` mode is intended for iterative analysis and issue triage.
3. If repeated `minor` mismatches appear, operator should escalate by process policy, not by automatic severity rewriting.
