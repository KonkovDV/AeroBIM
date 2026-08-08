---
title: "Sprint 3 Red Team audit"
date: 2026-08-07
status: audit_report
checkpoint: NO_GO
claim_boundary: fixture_only
---

# Sprint 3 Red Team audit — August 2026

**Scope:** Sprint 3 artifacts (customer data request, Kimi/Qwen comparison, outreach templates, scientific search, fixture corpus).  
**Checkpoint verdict:** **NO_GO** — RT-001/002/003 not closed with customer evidence.  
**Claims Lock SSOT:** [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md)

**Method:** Each row = claim under review → source → evidence → check → issue → severity → fix → residual risk.

---

## Audit matrix

| # | Claim | Source | Evidence | Check result | Issue | Severity | Fix | Residual risk |
|---|---|---|---|---|---|---|---|---|
| 1 | Fixture regex macro_f1 = 0.86 equals product accuracy | [`kimi-vs-qwen-2026-08.md`](../../docs/evidence/kimi-vs-qwen-2026-08.md), evaluator output | `samples/benchmarks/russian-aec-ground-truth.json` — requirements GT, 10 fixtures / 50 rows; `claim_level=fixture_only` | **FAIL** | Conflates requirements-extraction bench with customer precision | **HIGH** | Docs state GT ≠ expertise conclusions; forbid >90% in outreach + data request | Low if Claims Lock cited in all external comms |
| 2 | `issue_count` or finding tally implies accuracy | Runtime / report summaries | ADR-001 Shared-gate; Claims Lock forbids count-as-accuracy | **FAIL** | Stakeholders may read fewer issues as «better project» | **MEDIUM** | Outreach + audit explicitly separate counts from TP/FP precision | Medium without customer adjudication |
| 3 | Native DWG analysis supported / DWG-ready | Product hints, CAD capability | [`dwg-blocker-memo-2026-08.md`](../../docs/dwg-blocker-memo-2026-08.md); `EzdxfCadModelIngestor` `supported=False` for `.dwg` | **FAIL** | DWG-only packages fail closed; DXF is optional export only | **HIGH** | Pilot default IFC + PDF/A + DXF; outreach Claims Lock row | Low if DWG wording blocked |
| 4 | APS / ODA are project dependencies | Dependency manifests | [`DEPENDENCY_LICENSE_AUDIT_2026_07_31.md`](DEPENDENCY_LICENSE_AUDIT_2026_07_31.md); Sprint 3 license budget = 0 | **PASS (absent)** | None shipped — correct | **LOW** | Scientific search + DWG memo document paid path as deferred | Low — re-audit if deps change |
| 5 | LLM extraction can flip pass/fail | LLM adapters, hybrid docs | `test_red_team_signoff_remediation.py` advisory on/off same `summary.passed`; [`kimi-vs-qwen-2026-08.json`](../../docs/evidence/kimi-vs-qwen-2026-08.json) `advisory_only: true` | **PASS** | Correctly advisory-only | **LOW** | Canonical MD/JSON state cannot change `summary.passed` | Low if ADR-001 holds |
| 6 | FAILED CAD/OCR capability still yields `summary.passed=true` | Signoff profiles | Fail-closed production / samolet_pilot profiles | **PASS** | Fail-closed enforced | **LOW** | Red team row documents ADR-001 | Low |
| 7 | Expertise-conclusion customer corpus exists in repo | RT-001 closure | [`expertise-corpus-scan-2026-08.md`](../../docs/datasets/expertise-corpus-scan-2026-08.md) — no open pairs | **FAIL** | RT-001 blocked; only templates + empty IAA worksheets | **HIGH** | [`customer-data-request-2026-08.md`](../../docs/datasets/customer-data-request-2026-08.md) formalizes intake | **HIGH** until NDA pack + dual labels |
| 8 | Live Kimi/Qwen comparison executed | Sprint 3 LLM eval | [`kimi-vs-qwen-2026-08.json`](../../docs/evidence/kimi-vs-qwen-2026-08.json) `live_provider: false`, kimi/qwen `skipped` | **FAIL** | F1=0 is skip artifact, not measured LLM quality | **MEDIUM** | Canonical doc: NOT RUN; worth-it vs regex not established | **HIGH** until keys + re-run |
| 9 | Customer outreach sent / pilots agreed | Outreach docs | [`customer-outreach-sprint-3-2026-08.md`](../../docs/customer-outreach-sprint-3-2026-08.md) — templates only; tracker template empty | **PASS (honest)** | No false «customers interested» in git | **LOW** | Explicit «do not send from repo» | Medium ops drift if live sends unlogged |
| 10 | AeroBIM MIT tree includes GPL LibreDWG | License audit | [`dwg-blocker-memo-2026-08.md`](../../docs/dwg-blocker-memo-2026-08.md); DEPENDENCY_LICENSE_AUDIT | **PASS** | GPL not vendored | **LOW** | Scientific search + DWG memo restate incompatibility | Low |
| 11 | MIT preserved for product code (third-party disclosed) | Claims Lock | PyMuPDF AGPL/commercial dual; IfcOpenShell LGPL — inventory pointer | **PASS** | Correct qualified MIT wording | **LOW** | Outreach: «MIT for own code; third-party licenses apply» | Low |
| 12 | MEP federated clash delivered | RT-003 / capabilities | Claims Lock; ENG_PARTIAL scaffold | **FAIL** | MEP not delivered — must not claim in outreach | **HIGH** | Claims Lock row in outreach pack | Medium if demo over-reaches |
| 13 | BCF ZIP ⇒ CDE-ready integration | CDE gap audit | [`CDE_BCF_INTEGRATION_GAP_2026_07_31.md`](CDE_BCF_INTEGRATION_GAP_2026_07_31.md) | **FAIL** | Structural ZIP OK; import not proven | **MEDIUM** | Outreach + Claims Lock forbid CDE-ready | Medium until T2 evidence |
| 14 | Customer SLA ≤30 min for any compound | SLA docs | Fixture SLA `claim_level=fixture_only` only | **FAIL** | Fixture ms timing ≠ customer SLA | **HIGH** | Forbidden list in data request + outreach | Low if SLA wording blocked |
| 15 | Checkpoint GO / production-ready | Checkpoint process | RT-001/002/003 open; this audit | **FAIL** | Sprint 3 does not close checkpoint | **HIGH** | All Sprint 3 docs header `checkpoint: NO_GO` | **HIGH** until RT evidence |

---

## Summary counts

| Severity | Count |
|---|---|
| HIGH | 6 |
| MEDIUM | 4 |
| LOW | 5 |

**Rows audited:** 15 (minimum 12 required — met).

---

## Sprint 3 artifact cross-check

| Artifact | Claims Lock compliant | Notes |
|---|---|---|
| [`customer-data-request-2026-08.md`](../../docs/datasets/customer-data-request-2026-08.md) | ✅ | Formal RT-001 intake; forbids pre-GT claims |
| [`kimi-vs-qwen-2026-08.md`](../../docs/evidence/kimi-vs-qwen-2026-08.md) | ✅ | live_provider=false; advisory only |
| [`kimi-vs-qwen-2026-08.json`](../../docs/evidence/kimi-vs-qwen-2026-08.json) | ✅ | Machine mirror |
| [`customer-outreach-sprint-3-2026-08.md`](../../docs/customer-outreach-sprint-3-2026-08.md) | ✅ | Templates only; placeholders |
| [`SPRINT3_SCIENTIFIC_SEARCH_2026_08.md`](../../docs/research/SPRINT3_SCIENTIFIC_SEARCH_2026_08.md) | ✅ | No >90%; mechanical→AEC caveat |
| This audit | ✅ | Checkpoint **NO_GO** recorded |

---

## Required actions before Checkpoint GO

1. Execute RT-001 customer intake per [`customer-data-request-2026-08.md`](../../docs/datasets/customer-data-request-2026-08.md) with dual adjudication.
2. Re-run LLM eval with live providers when keys budgeted — update [`kimi-vs-qwen-2026-08.md`](../../docs/evidence/kimi-vs-qwen-2026-08.md).
3. Log live outreach in tracker — do not commit unverified outcomes to public git.
4. If native DWG required: legal + ODA/CADSoftTools decision — **not** Sprint 3 scope (budget 0).

---

## Residual risk statement

Sprint 3 delivers **honest fixture evidence and intake specifications only**. Product precision, LLM superiority over regex, DWG readiness, MEP delivery, CDE integration, and customer SLA remain **unproven**. Checkpoint stays **NO_GO** until customer ground truth and signed scope close RT-001/002/003.
