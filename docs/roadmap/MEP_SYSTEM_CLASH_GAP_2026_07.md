---
title: MEP system-aware clash gap
status: open
tracking_id: MEP-CLASH-001
last_updated: "2026-08-01"
---

# MEP-CLASH-001 — system-aware clash remains open

## Current truth

AeroBIM has a generic IFC clash adapter and emits geometry results as
`FindingCategory.SPATIAL`. Product **MEP system-aware** coordination is **not delivered**
(RT-003 **OPEN**). Engineering foundation improved 2026-07-21 + **geometry honesty deepen
2026-08-01** (P2-02):

- Domain entities: `MepSystem`, `MepClashMatrix`, `MepClearanceRule`, `MepClashFinding`
  with provenance (system, discipline, system_type, source_ifc, element_guid,
  clearance_class, allowed/forbidden, priority, exception kinds:
  sleeve / insulation / same_system / intentional_containment);
- Matrix evaluation: allowed → no finding; forbidden → provenance finding;
  unclassified → `NOT_VERIFIED` (never confident ERROR);
- **Edge provenance:** `MepSystemGraph.edge_kinds` labels pairs as `co_presence`
  (cartesian systems in one IFC) or `connects` (`IfcRelConnects*`) — **neither is
  geometric clash** (aligned with IfcClash AABB≠intersection; buildingSMART clash UCM);
- Issue evidence stamps `edge_basis:…`, `claim_boundary:geometry_NOT_VERIFIED`, and
  `claim_boundary:exceptions_NOT_VERIFIED` when matrix rows declare exceptions;
- Analyze probe **hardcodes** `geometry_verified=False` — ERROR `AEROBIM-MEP-FORBIDDEN`
  unreachable without a future gated path;
- DI wires `UnconfiguredMepSystemGraphProvider` (probe → `capabilities.mep_system_clash=NOT_VERIFIED`);
  wiring ≠ capability;
- `SyntheticMepSystemGraphProvider` (`@sota-stub`) exists for unit tests only — tagged
  synthetic; analyze path still **NOT_VERIFIED**, never OK;
- no customer-approved routing/connectivity graph for duct/pipe/cable tray;
- no signed allowed-intersection/exclusion matrix loaded from customer memo
  (`samples/mep/clearance-matrix-template.json` remains **template only**);
- no insulation/maintenance clearance **measured** distance as product claim;
- no penetration/opening workflow;
- no MEP-specific labeled precision corpus (RT-001/003);
- **do not invent federated IFC as customer evidence**.

**World practice anchors (July 2026):** Solibri Clash Detection Matrix (hard + clearance +
same-system ignore); usBIM.clash / buildingSMART-certified federated IFC; IfcClash 0.8.x
(intersection / collision / clearance); BIMClash KIBIM 2025 (semantic severity after
geometry); MDPI Buildings 2026 AI clash review (detection mature, accountability open);
Jiang et al. EG-ICE 2025 (RL resolution assumes real geometry first). Plan:
[`P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md`](P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md).

**DI is wired** (fail-closed defaults):

| Port | Default adapter | Opt-in |
|------|-----------------|--------|
| `MepSystemGraphProvider` | `UnconfiguredMepSystemGraphProvider` | `SyntheticMepSystemGraphProvider` (**tests only**, `@sota-stub`) |
| `SystemClashPort` | `UnconfiguredSystemClash` | `IfcSystemAwareClash` when `AEROBIM_MEP_SYSTEM_CLASH_ENABLED` + `AEROBIM_MEP_SCOPE_MEMO_REF` |

`IfcSystemAwareClash` is an **advisory name-pair scaffold** (not geometric clearance delivery).
Analyze probe keeps `mep_system_clash` **NOT_VERIFIED** even if nodes exist
(including synthetic graphs).
Agent tool `detect_system_clash` returns step status **`degraded`**, never product `ok`.

Therefore the TZ row «MEP / system intersections» remains **missing / generic only**
until RT-003 customer federated IFC + signed scope memo + clearance matrix evidence.

## Contract scaffold

- `aerobim.domain.mep.MepSystemGraphProvider`
- `aerobim.domain.mep.evaluate_matrix_against_graph` / `evaluate_system_pair` / `edge_kind_for_pair`
- `aerobim.domain.tz_architecture_ports.SystemClashPort`
- Template: `samples/mep/clearance-matrix-template.json` (not auto-loaded as product)
- Tests: `test_p2_mep_geometry_honesty.py`, `test_p2_mep_analyze_integration.py`

## Claims Lock

Forbidden: «MEP clash delivered», `capabilities.mep_system_clash=OK`, flipping intake
`federated_mep_scope_with_signed_memo` without evidence, treating `connects` edges or
AABB/broadphase as verified geometry. Checkpoint **NO_GO**.
RT-003 remains **OPEN** — engineering honesty improved, product not verified.
