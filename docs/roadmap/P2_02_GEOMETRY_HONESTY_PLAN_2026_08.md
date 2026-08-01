# P2-02 Geometry Honesty Deepen — Plan (2026-08-01)

**Status:** executing  
**Checkpoint:** `NO_GO` (RT-003 remains OPEN)  
**Claim boundary:** eng deepen only — never MEP delivered / never `mep_system_clash=OK`

## External evidence (July 2026)

| Source | Takeaway for AeroBIM |
|--------|----------------------|
| buildingSMART UCM clash use-case | Clash = geometric collision under **rules + tolerances**; matrix defines which discipline pairs are tested; humans confirm |
| Solibri Clash Detection Matrix | Hard intersection + volume tolerance; **ignore same system / same layer**; soft clearance separate |
| usBIM.clash (buildingSMART-certified) | Hard / clearance / workflow clash; federated IFC; BCF export |
| IfcClash / IfcOpenShell 0.8.x (2025–2026) | Modes: intersection, collision, clearance; AABB/BVH **broadphase ≠ true clash** (OSArch 2026) |
| BIMClash / KIBIM 2025 | Semantic KG classifies type/severity after geometry — co-presence alone insufficient |
| MDPI Buildings 2026 AI clash review | Detection mature; filtering/resolution/accountability still open; black-box not deployable for professional coordination |
| Jiang et al. EG-ICE 2025 (TUM/Strathclyde) | RL resolves geometric conflicts after rule-based checker — still assumes real geometry first |

**Industry consensus we encode:** co-presence ≠ connection ≠ geometric clash; matrix + clearance ≠ product MEP clash until signed customer matrix + measured geometry.

## Gaps closed this cycle

| ID | Change | Still NOT claimed |
|----|--------|-------------------|
| G1 | Label graph edges `co_presence` vs `connects` (IfcRelConnects*) | Not geometry verified |
| G2 | Stamp `edge_basis:` on MEP issue evidence | Not Solibri-class clash |
| G3 | Honor `exception_kinds` as **advisory demotion** when geometry unverified | Exceptions not validated |
| G4 | Guardrail tests: analyze path never `geometry_verified=True`; ENG_FIXTURE never FORBIDDEN ERROR | — |
| G5 | Docs + research pointers in gap roadmap | RT-003 OPEN |

## Explicitly out of scope

- Wiring IfcClash / BVH as product capability
- Setting `geometry_verified=True`
- Flipping `mep_system_clash` to OK
- Closing RT-003

## Acceptance

1. Federated ENG_FIXTURE graph exposes `edge_kinds` (at least `co_presence`)
2. Issues include `claim_boundary:geometry_NOT_VERIFIED` and `edge_basis:…`
3. Exception kinds on forbidden rows → message notes exceptions unverified; severity stays WARNING
4. Focused tests green; Claims Lock unchanged on forbidden phrases
