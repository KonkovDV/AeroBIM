---
title: "Red Team Hyperdeep Audit & Hardening Plan — 2026-07-18"
status: active
checkpoint: NO_GO
head: ad8e12d7fd28731ba6eb4bcfa9c677220ba01225
---

# Red Team Hyperdeep Plan (execute in order)

## Hard constraints (non-negotiable)

| # | Rule |
|---|------|
| 1 | Do **not** delete/archive/reopen/modify **PR #10** or **PR #11** |
| 2 | Do **not** rewrite history, force-push, filter-repo, gc, reset --hard, clean -fd |
| 3 | Do **not** inflate claims; fixture ≠ customer; DXF ≠ DWG; OCR ≠ human CV; BCF ZIP ≠ CDE |
| 4 | LLM/VLM/GraphRAG **never** on deterministic sign-off path |
| 5 | Prefer atomic patches: code + test + docs + verification command |
| 6 | RT-001/002/003 stay **EXTERNAL BLOCKER** until customer evidence |

## Baseline snapshot (pre-work)

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD | `ad8e12d` (2026-07-18) |
| Dirty tree | **clean** |
| Remote | `https://github.com/KonkovDV/AeroBIM` |
| Checkpoint | **NO_GO** (RT-001/002/003) |
| PR #10/#11 | **out of scope** (observation only if needed) |

## Phase map

| Phase | Goal | Exit criteria |
|-------|------|---------------|
| **0** | Read-only recon + risk register + false-pass map | Gates run; `RT-HYPER-*` register started; no code yet except report |
| **1** | Security & integrity blockers | ACL/path/upload/storage consistency gaps filed or patched with tests |
| **2** | Sign-off correctness (quantity/MEP/schema/raster/calc/profiles) | No known soft-pass for required contours; tests prove FAILED→block |
| **3** | Provenance & HITL events | Persistable finding contract; corrupt events visible; bbox validation |
| **4** | IFC/IDS/BCF | Unsupported facets fail-closed; T1≠T2 documented |
| **5** | Advisory isolation E2E | ON/OFF same deterministic set + passed |
| **6** | Jobs / concurrency / ops | Idempotency + stuck-running addressed or documented residual |
| **7** | CI / mutation resistance | Critical mutation killers in CI where feasible |
| **8** | Docs / Claims Lock sync | Status vocabulary only; **NO_GO** preserved |

## Priority attack paths (Phase 0→2 focus)

1. **False PASS** via quantity checker exception → WARNING  
2. **False PASS** via MEP probe soft NOT_VERIFIED when required  
3. **False PASS** via schema/BSI/OCR empty success under required profile  
4. Capability matrix drift (runtime vs static vs README)  
5. Storage orphan / non-atomic save  
6. Cross-tenant object access  
7. Advisory mutating deterministic findings (E2E)  

## Profile matrix (to implement / document)

| Profile | require_clash | clash_affects_pass | require_bsi | require_mep | quantity required | ACL |
|---------|---------------|--------------------|-------------|-------------|-------------------|-----|
| development | false | false | false | false | false | optional |
| fixture | false | false | false | false | false | off/dev |
| **samolet_pilot** | true | true | true | policy | policy | true |
| production | true | true | true | true | true | true |

## Deliverables per finding

`RT-HYPER-XXX` with severity, repro, false-PASS?, fix, regression test, residual risk, status.

## Final verdict rule

- Any open false-PASS path → **NO_GO**  
- Customer RT-001/002/003 open → checkpoint **NO_GO** even if engineering CONDITIONAL  
- Explicit confirmation: PR #10/#11 untouched; no destructive git  

## Execution order this session

1. Write this plan ✅  
2. Phase 0: run gates + map soft-pass hotspots  
3. Phase 2 first patches: quantity FAILED on exception; MEP exception→FAILED; Samolet profile object  
4. Tests + Claims Lock honesty if wording changes  
5. Interim report; continue remaining phases as capacity allows  
