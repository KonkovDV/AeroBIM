# Customer Pilot Backlog — Samolet Task 07

**Date:** 2026-07-21  
**Checkpoint:** `NO_GO` (RT-001 / RT-002 / RT-003)  
**Principle:** deterministic engine checks; AI assists only; evidence explains; expert decides disputes.

## Inventory (as of iteration 1)

| Bucket | Items |
|---|---|
| **Works (fixture-proven)** | Package analyze; IFC/IDS/cross-doc; `PackageOutcome` + `summary.passed` (ADR-001); intake fail-closed; provenance stamp/persist; BCF ZIP T1; HITL; ACL 404; SSRF guard; idempotent jobs; precision publishable gates (eng); SLA refuse-without-evidence; revision compare; **run manifest + reproducibility hash**; **golden baseline hash**; **stage timeout guard** |
| **Experimental** | OpenCDE BCF API; IfcSystemAwareClash probe; IFC KG advisory; compliance agent; OCR/raster extras |
| **Planned** | Profiling-driven perf (fan-out, caches, spatial index); POST-05 OIDC BFF; full federated MEP geometry |
| **Needs customer** | RT-001 corpus + κ/α; RT-002 approved norm pack; RT-003 federated MEP + matrix; CDE T2 import; customer SLA pack |
| **Not claimable** | >90% accuracy; ≤30 min customer SLA; native DWG; MEP delivered; calc correctness; CDE-ready BCF |

## Priority backlog

### P0 — runtime / evidence / security (engineering, no customer flip)

| ID | Task | Risk removed | Pilot req | Evidence | Test | Allows | Still forbids |
|---|---|---|---|---|---|---|---|
| P0-01 | `RunManifest` + reproducibility hash | Non-reproducible verdict drift | Repro by package/code/rules hash | `run_manifest.json` in evidence bundle | `test_run_manifest`, `test_golden_report` | Fixture reproducibility hash cite | Customer accuracy |
| P0-02 | Stage timeout guard | Runaway contour blocking SLA | Stage budgets in pilot protocol | `stage_timeout.py` + budgets in manifest | `test_stage_timeout` | Documented per-contour limits | Customer ≤30 min SLA |
| P0-03 | Golden report baseline pin | Silent regression on Shared-gate | Deterministic regression gate | Pinned hash in `test_golden_report` | same | Baseline stability claim | Product accuracy |
| P0-04 | Advisory tool registry scaffold | AI on sign-off path | Typed tool boundary | `ai_tool_registry.py` | `test_ai_tool_registry` | Advisory tool contract list | AI changes verdict |
| P0-05 | README / matrix drift | False "planned" claims | Honest capability map | Updated README + matrix | CI readme check | PackageOutcome available | — |
| P0-06 | Profiling trace (next) | Blind perf optimization | SLA measurement prep | `profile_package_trace.json` | TBD | Fixture timing breakdown | Customer SLA |

**P0 status (iteration 1):** P0-01..05 **DONE**; P0-06 pending profiling on representative pack.

### P0 iteration 2 (2026-07-21)

| ID | Task | Status |
|---|---|---|
| P0-06 | `profile_package_trace` CLI + `PackageTraceCollector` | **DONE** |
| P0-07 | MEP federated scope env + analyze wiring | **DONE** |
| P0-08 | Drawing sheet identity guard | **DONE** |
| P0-09 | Advisory tool trace rows in compliance agent | **DONE** |

**P0 status (iteration 2):** P0-06..09 **DONE**. Next: wire scope into pilot profile docs; 2D coordinate/regions; perf wave from trace evidence.

### P1 — customer pilot (blocked on intake)

| ID | Task | Blocker |
|---|---|---|
| P1-01 | Customer package via intake gate | RT-001/002 gates false |
| P1-02 | Approved norm/IDS pack hash lock | RT-002 |
| P1-03 | Dual adjudicator corpus + agreement artifact | RT-001 |
| P1-04 | Federated MEP scope manifest (customer paths) | RT-003 |
| P1-05 | Customer SLA measurement pack | customer SLA OPEN |
| P1-06 | BCF T2 CDE import screenshot + hash | RT-008 |

**P1-04 eng prep (iteration 1):** `samples/mep/federated-scope-template.json` + `load_federated_mep_scope()` — template stays `NOT_VERIFIED`.

### P2 — MEP / 2D improvements

| ID | Task | Status |
|---|---|---|
| P2-01 | Federated IFC graph builder (IfcSystem) | scaffold in `IfcSystemAwareClash` |
| P2-02 | Clearance matrix + BCF topic from MEP findings | domain in `mep.py` |
| P2-03 | PDF/OCR sheet identity + revision compare | partial |
| P2-04 | Annotation↔IFC matching + HITL escalation | partial |
| P2-05 | Coordinate system + regions | partial |

### P3 — VLM / agent / knowledge graph

| ID | Task | Status |
|---|---|---|
| P3-01 | Typed tool registry wiring to orchestrator | scaffold only |
| P3-02 | Full trace + replay store | planned |
| P3-03 | GraphRAG / IfcLLM product | **forbidden** |

## Definition of Done (customer pilot) — tracking

| Criterion | Status |
|---|---|
| Customer package via intake gate | **OPEN** |
| Approved norm/IDS pack hash | **OPEN** (RT-002) |
| Federated MEP scope or written exclusion | **PARTIAL** (template + fail-closed) |
| Dual expert adjudication | **OPEN** (RT-001) |
| Finding evidence provenance | **ENG DONE** |
| Capability failures block PASS | **ENG DONE** |
| Reproducible by hashes | **ENG DONE** (iteration 1) |
| Customer SLA measured | **OPEN** |
| BCF 2.1 CDE import | **NOT_VERIFIED** |
| Security review | **PARTIAL** (threat model) |
| Final report with κ/α, FN, FP, hours | **OPEN** |
| Claims lock clean | **YES** (NO_GO) |

## Iteration protocol

Before each task answer:

1. Risk removed  
2. Pilot requirement  
3. Evidence artifact  
4. Proof test  
5. Allowed public wording  
6. Still forbidden wording  

After each iteration publish: changed files, tests, measurements, blockers, capability matrix delta, pilot readiness status.

## Allowed verdict (pre-customer)

```
Engineering readiness: improved
Fixture readiness: GO
Customer sign-off: NO_GO
Pilot start: CONDITIONAL_GO after intake
Checkpoint: NO_GO
```
