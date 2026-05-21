---
title: "AeroBIM Post-Pilot Fork 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, pilot, roadmap]
---

# Post-Pilot Fork

Decision tree after the 8–12 week pilot completes.

Use the filled template in [`post-pilot-go-no-go-memo-2026.md`](post-pilot-go-no-go-memo-2026.md) before choosing a branch.

**November 2026 decision:** select exactly one primary branch (A, B, or C). Branch B may run in parallel with a narrow A tranche only if funding explicitly requires both.

## Go / no-go inputs

| Signal | Go indicator | No-go indicator |
|---|---|---|
| KPI: confirmed findings | ≥ 60% TP on scope | FP flood, engineers ignore BCF |
| KPI: review time | Measurable savings | No baseline or no savings |
| Technical | Gates 1–3 stable | Evidence rail regressions |
| Commercial | Customer wants annual path | Procurement blocks open stack |

## Branch A — Enterprise product (customer wants rollout)

Priority order:

1. **B.1** Postgres + MinIO completion ([docs/14-enterprise-storage-foundation.md](14-enterprise-storage-foundation.md))
2. **B.3** OIDC/JWT for multi-user tenants
3. **C.1** Typed `Quantity` to cut `UNIT_MISMATCH` noise
4. **Wave 4** Revit thin client after BCF roundtrip is routine

Defer: non-deterministic drawing sign-off, SHACL primary validation, event sourcing.

## Branch B — Research / publication (academic partnership)

Priority order:

1. **C.4/C.5** Publication-grade benchmark report
2. **C.3** bSDD term normalization
3. **FT path** only after extraction F1 ≥ 0.70 enforced in CI

Defer: enterprise storage unless funding requires it.

## Branch C — Pause / pivot

Triggers:

- Pilot KPIs not met after scope adjustment
- Incumbent procurement wins without technical engagement

Actions:

- Archive pilot artifacts and KPI memo
- Keep deterministic kernel and benchmark packs as open evidence
- Do not expand non-deterministic drawing or enterprise scope without new sponsor

## Explicit non-goals (all branches)

- Multi-service orchestration platform (out of product scope)
- Full CDE replacement
- Autonomous engineering sign-off
