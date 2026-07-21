# Customer Pilot Backlog — Samolet Task 07

**Date:** 2026-07-21  
**Checkpoint:** `NO_GO` (RT-001 / RT-002 / RT-003)  
**Principle:** deterministic engine checks; AI assists only; evidence explains; expert decides disputes.

## Inventory (as of P2b)

| Bucket | Items |
|---|---|
| **Works (fixture-proven)** | Package analyze; IFC/IDS/cross-doc; `PackageOutcome`; intake fail-closed; provenance; BCF ZIP T1 + MEP topics; HITL; ACL 404; SSRF; jobs; precision/SLA gates (eng); revision merge; run manifest; golden hash; stage timeout; **IFC parse cache + spatial index**; **annotation↔IFC links persisted**; **federated IfcSystem graph + clearance matrix eval (fixture)** |
| **Experimental** | OpenCDE BCF API; IfcSystemAwareClash probe; IFC KG advisory; compliance agent tool traces |
| **Planned** | POST-05 OIDC BFF; full federated MEP **geometry** intersection |
| **Needs customer** | RT-001 corpus + κ/α; RT-002 approved norm pack; RT-003 federated MEP + signed matrix; CDE T2; customer SLA pack |
| **Not claimable** | >90% accuracy; ≤30 min customer SLA; native DWG; MEP delivered; calc correctness; CDE-ready BCF |

## Priority backlog

### P0 — runtime / evidence / security — **DONE** (iterations 1–2)

P0-01..09 complete (run manifest, timeouts, golden, tool registry scaffold, profile trace, MEP scope env, sheet identity, agent traces).

## Red Team remediation (2026-07-21)

| ID | Finding | Fix |
|---|---|---|
| RT-P2-001 | Path jail escape on federated/matrix paths | `resolve_repo_relative_path` |
| RT-P2-002 | Co-presence → invented ERROR | `geometry_verified=False` demotes to WARNING |
| RT-P2-003 | Template matrix → ERROR | `AEROBIM-MEP-TEMPLATE` WARNING only |
| RT-P2-004 | BCF Clash inflation | Template/unclassified → `Comment` + claim_boundary |
| RT-P2-005 | Self-attested VERIFIED | Requires expert_signoff + memo; fixture=`ENG_FIXTURE` |
| RT-P2-006 | Dead `validate_invocation` | Called before every agent tool handler |
| RT-P2-007 | Invented IFC guids | `ifc_guid=None`; `claimed_guid:` evidence only |
| RT-P2-008 | Soft matrix skip | Missing matrix on ENG/VERIFIED → ERROR + FAILED |
| RT-P2-009 | `synthetic=False` on fixtures | eng_fixture → `synthetic=True` |
| RT-P2-010 | `authoritative` default True | Reconstruct default **False** |
| RT-P2-011 | Test theater | Inverted asserts |
| RT-P2-012 | False DONE labels | Relabeled **ENG_PARTIAL** below |

### P2 status after remediation

| ID | Task | Status |
|---|---|---|
| P2-01 | IFC parse session + spatial index | **ENG_DONE** |
| P2-02 | Federated graph + matrix + BCF honesty | **ENG_PARTIAL** (geometry NOT_VERIFIED; RT-003 OPEN) |
| P2-03 | Sheet identity + drift | **ENG_DONE** (OCR title-block still partial) |
| P2-04 | Annotation↔IFC matching | **ENG_PARTIAL** (candidates only; no verified guid) |
| P2-05 | Pilot env runbook + ENG_FIXTURE scope | **ENG_DONE** |
| P2-06 | Registry allowlist + validate_invocation | **ENG_DONE** |

**Evidence:** `docs/evidence/package-profile-trace-latest.json`; `samples/mep/hvac-sprinkler-systems.ifc`; `samples/mep/federated-scope-verified-fixture.json` (`ENG_FIXTURE`); `docs/pilot/SAMOLET_PILOT_ENV_RUNBOOK_2026_07.md`.

### P2 — MEP / 2D / perf (engineering)

| ID | Task | Status |
|---|---|---|
| P2-01 | IFC parse session + spatial index + cache stats | **ENG_DONE** |
| P2-02 | Federated IfcSystem graph + clearance matrix + BCF honesty | **ENG_PARTIAL** |
| P2-03 | Sheet identity + annotation sheet drift | **ENG_DONE** |
| P2-04 | Annotation↔IFC matching + report persistence | **ENG_PARTIAL** |
| P2-05 | `SAMOLET_PILOT_ENV_RUNBOOK` + ENG_FIXTURE scope | **ENG_DONE** |
| P2-06 | AI tool registry = agent allowlist + validate_invocation | **ENG_DONE** |

| ID | Task | Blocker |
|---|---|---|
| P1-01 | Customer package via intake gate | RT-001/002 gates false |
| P1-02 | Approved norm/IDS pack hash lock | RT-002 |
| P1-03 | Dual adjudicator corpus + agreement artifact | RT-001 |
| P1-04 | Federated MEP scope manifest (customer paths) | RT-003 |
| P1-05 | Customer SLA measurement pack | customer SLA OPEN |
| P1-06 | BCF T2 CDE import screenshot + hash | RT-008 |

**P1-04 eng prep:** template + verified **fixture** scope + matrix eval — still not customer evidence.

### P3 — VLM / agent / knowledge graph

| ID | Task | Status |
|---|---|---|
| P3-01 | Typed tool registry wiring to orchestrator | **ENG_DONE** (`validate_invocation` + allowlist) |
| P3-02 | Full trace + replay store | partial (`tool_traces` on report) |
| P3-03 | GraphRAG / IfcLLM product | **forbidden** |

## Definition of Done (customer pilot) — tracking

| Criterion | Status |
|---|---|
| Customer package via intake gate | **OPEN** |
| Approved norm/IDS pack hash | **OPEN** (RT-002) |
| Federated MEP scope or written exclusion | **PARTIAL** (fixture VERIFIED eng + fail-closed; customer OPEN) |
| Dual expert adjudication | **OPEN** (RT-001) |
| Finding evidence provenance | **ENG DONE** |
| Capability failures block PASS | **ENG DONE** |
| Reproducible by hashes | **ENG DONE** |
| Customer SLA measured | **OPEN** |
| BCF 2.1 CDE import | **NOT_VERIFIED** |
| Security review | **PARTIAL** (threat model) |
| Final report with κ/α, FN, FP, hours | **OPEN** |
| Claims lock clean | **YES** (NO_GO) |

## Iteration protocol

Before each task answer: risk removed → pilot requirement → evidence → proof test → allowed wording → forbidden wording.

## Allowed verdict (pre-customer)

```
Engineering readiness: improved
Fixture readiness: GO
Customer sign-off: NO_GO
Pilot start: CONDITIONAL_GO after intake
Checkpoint: NO_GO
```
