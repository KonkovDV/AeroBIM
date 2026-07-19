---
title: MEP system-aware clash gap
status: open
tracking_id: MEP-CLASH-001
last_updated: "2026-07-19"
---

# MEP-CLASH-001 — system-aware clash remains open

## Current truth

AeroBIM has a generic IFC clash adapter and emits geometry results as
`FindingCategory.SPATIAL`. Product **MEP system-aware** coordination is **not delivered**:

- DI wires `UnconfiguredMepSystemGraphProvider` (probe → `capabilities.mep_system_clash=NOT_VERIFIED`); wiring ≠ capability;
- no customer-approved routing/connectivity graph for duct/pipe/cable tray;
- no signed allowed-intersection/exclusion matrix loaded from customer memo;
- no insulation/maintenance clearance semantics per system as product claim;
- no penetration/opening workflow;
- no MEP-specific labeled precision corpus (RT-001/003).

**DI is wired** (fail-closed defaults):

| Port | Default adapter | Opt-in |
|------|-----------------|--------|
| `MepSystemGraphProvider` | `UnconfiguredMepSystemGraphProvider` | — |
| `SystemClashPort` | `UnconfiguredSystemClash` | `IfcSystemAwareClash` when `AEROBIM_MEP_SYSTEM_CLASH_ENABLED` + `AEROBIM_MEP_SCOPE_MEMO_REF` |

`IfcSystemAwareClash` is an **advisory name-pair scaffold** (not geometric clearance delivery).
Analyze probe keeps `mep_system_clash` **NOT_VERIFIED** even if nodes exist.
Agent tool `detect_system_clash` returns step status **`degraded`**, never product `ok`.

Therefore the TZ row «MEP / system intersections» remains **missing / generic only**
until RT-003 customer federated IFC + signed scope memo + clearance matrix evidence.

## Contract scaffold

- `aerobim.domain.mep.MepSystemGraphProvider`
- `aerobim.domain.tz_architecture_ports.SystemClashPort`
- Template: `samples/mep/clearance-matrix-template.json` (not auto-loaded as product)

## Claims Lock

Forbidden: «MEP clash delivered», `capabilities.mep_system_clash=OK`, flipping intake
`federated_mep_scope_with_signed_memo` without evidence. Checkpoint **NO_GO**.
