---
title: "AeroBIM Pre-Pilot Technical Gates 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, gates]
---

# Pre-Pilot Technical Gates

Run before customer-facing pilot week.

## Gate 1 — Deterministic replay

| Step | Pass criterion |
|---|---|
| Run pilot pack twice with same storage dir cleared between runs | Same `rule_id` set and issue count |
| Compare JSON exports | Structural equality on issues array (ignore `report_id`, `created_at`) |

## Gate 2 — Evidence rail

| Command | Pass criterion |
|---|---|
| `pytest tests -q` | All pass (isolated `.venv-pilot`) |
| `python -m aerobim.tools.export_runtime_baseline` | `verification.status` = `APPROVED` |
| CI `benchmark-smoke` | Three canonical packs + pilot manifest load |

## Gate 3 — BCF handoff

| Step | Pass criterion |
|---|---|
| Export BCF 2.1 from pilot report | Valid ZIP, `bcf.version` present |
| Import in coordination tool | Topics visible with messages |
| Engineer checklist | Documented TP/FP labels |

## Gate 4 — False-positive budget

| Control | Action |
|---|---|
| `ConflictKind` breakdown | Review `UNIT_MISMATCH` vs `HARD_CONFLICT` |
| Severity | Set `AEROBIM_CROSS_DOC_SEVERITY` per contractual strictness |
| Scope | Reject expansion beyond fire+structure family during pilot |

## Gate 5 — OpenRebar (if applicable)

| Control | Action |
|---|---|
| Digest endpoint | Matches CLI tool output |
| `enforced` mode | Critical/major classes block pass status when configured |

## Sign-off record

| Gate | Owner | Date | Status | Evidence link |
|---|---|---|---|---|
| 1 Deterministic replay | | | pending | `pytest tests/test_pilot_deterministic_replay.py` |
| 2 Evidence rail | | | pending | `pytest -q`, `export_runtime_baseline` |
| 3 BCF handoff | | | pending | BCF ZIP + coordination tool import |
| 4 FP budget policy | | | pending | `summarize_conflict_breakdown`, severity env |
| 5 OpenRebar (if in scope) | | | n/a | digest + enforced mode |

Pilot may start when gates 1–3 pass and gate 4 has an agreed operator policy. Gate 5 applies only when reinforcement is in pilot scope.

Automated helpers:

```bash
cd backend
python -m pytest tests/test_pilot_deterministic_replay.py -q
python -m aerobim.tools.export_runtime_baseline
python -m aerobim.tools.summarize_conflict_breakdown --pack ../samples/benchmarks/project-package-pilot-moscow-v1.json
```
