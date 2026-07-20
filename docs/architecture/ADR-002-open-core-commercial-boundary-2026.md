---
title: "ADR-002 — Open-core commercial boundary"
status: proposed
date: 2026-07-21
last_updated: "2026-07-21"
---

# ADR-002: Open-core commercial boundary

## Context

AeroBIM is currently MIT-licensed (`LICENSE`). Pilot packaging needs a clear
**commercial boundary** so open engineering artifacts stay usable while
customer-facing products (hosted CDE connectors, managed adjudication, SLA
ops) can be monetized later — **without changing the LICENSE in this ADR**.

Checkpoint remains **NO_GO**; this ADR does not authorize product accuracy,
customer SLA, or CDE-ready claims.

## Decision

1. **Keep MIT for the current public repository** until a separate, explicit
   license change is approved by maintainers (out of scope here).
2. Draw an **open-core line** by capability class, not by file count:

| Open-core (intended public / OSS) | Commercial / pilot premium (candidates) |
|---|---|
| Deterministic Shared-gate engines (IFC/IDS/cross-doc) | Managed customer adjudication + precision ops |
| Honesty surfaces + claim gates | Hosted CDE import ops (T2+) with SLAs |
| Structural BCF ZIP export (T0/T1) | Production OIDC BFF / SSO packaging (POST-05) |
| Fixture benchmarks + harnesses | Customer package SLA measurement service |
| Architecture ADRs / threat model docs | On-prem enterprise support + federated MEP packs |

3. **Do not** invent dual-license headers, proprietary stubs, or LICENSE edits
   in the same change as this ADR.
4. Future license moves (e.g. dual Apache-2.0 / commercial, BSL, or AGPL for
   network components) require a **new** ADR + explicit maintainer approval.

## Options considered

| Option | Pros | Risks |
|---|---|---|
| **A. Stay MIT-only (status quo)** | Max adoption; simple | Harder to fund T2+ ops |
| **B. Open-core boundary ADR (this)** | Clear intent; no license churn | Boundary drift if not enforced in claims |
| **C. Immediate dual-license** | Faster monetization | Contributor CLA / LICENSE change blast radius |
| **D. Full proprietary fork** | Control | Kills community + trust; conflicts with pilot honesty |

**Chosen:** B — document the boundary now; defer LICENSE change.

## Consequences

- Public docs and claim locks must keep commercial candidates in the
  “not claimed / NOT_VERIFIED” language until evidenced.
- Contributors continue under MIT until a dedicated license ADR lands.
- Product packaging may reference this ADR for scope splits; it is **not** a
  contract and **not** a claim of delivered commercial features.
