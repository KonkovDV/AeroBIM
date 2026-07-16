---
title: MEP system-aware clash gap
status: open
tracking_id: MEP-CLASH-001
last_updated: "2026-07-16"
---

# MEP-CLASH-001 — system-aware clash remains open

## Current truth

AeroBIM has a generic IFC clash adapter and emits geometry results as
`FindingCategory.SPATIAL`. It does **not** currently provide Solibri-depth
system-aware MEP coordination:

- no routing/connectivity graph for duct/pipe/cable tray systems;
- no customer-approved allowed-intersection/exclusion matrix;
- no insulation/maintenance clearance semantics per system;
- no penetration/opening workflow;
- no MEP-specific labeled precision corpus.

Therefore the TZ row «MEP / system intersections» remains **missing / generic
only**, not `partial-done`.

## Contract scaffold (2026-07-16)

Domain contracts landed (no runtime analyze wiring yet):

- `aerobim.domain.mep.MepSystemGraphProvider`
- `aerobim.domain.mep.AllowedIntersectionMatrix`
- `UnconfiguredMepSystemGraphProvider` — fail-closed until customer corpus

**Blocked on:** federated MEP IFC with systems + signed scope memo from Samolet.
Do not implement graph/matrix adapters against synthetic-only models for sign-off.

## Acceptance criteria for closure

1. Customer supplies at least one federated MEP IFC with systems and known
   collisions/non-collisions.
2. Scope memo defines entities, system classes, exclusions, clearances and units.
3. New spatial predicates remain separate from IDS alphanumeric facets.
4. Adapter failure is explicit in `capabilities.clash`; no empty-success fallback.
5. Tests cover connectivity, insulation, openings, allowed crossings and unit
   normalization.
6. Detection run is adjudicated by ≥2 engineers with
   [`DETECTION_PRECISION_PROTOCOL_2026.md`](../evaluation/DETECTION_PRECISION_PROTOCOL_2026.md).
7. BCF output is imported into the customer CDE and visually checked.

## Non-goal

The milestone does not claim replacement of Solibri/Navisworks or a full MEP
coordination suite.
