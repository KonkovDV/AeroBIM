<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "AeroBIM Project Status Audit 2026"
status: active
version: "1.1.0"
last_updated: "2026-08-01"
claim_boundary: "Self-audit. Checkpoint NO_GO until RT-001/002/003. Fixture evidence ≠ customer value. Eng readiness ≠ Checkpoint GO."
---

# PROJECT STATUS AUDIT — AeroBIM (2026-07-19)

**Author relationship:** self  
**Checkpoint:** **`NO_GO`** ([CRITICAL_BLOCKERS](../audit/reports/CRITICAL_BLOCKERS.md))  
**Claims SSOT:** [CLAIMS_LOCK](../audit/reports/CLAIMS_LOCK_2026_07_17.md) · eng freeze [CLAIMS_LOCK_2026_07_31](../audit/reports/CLAIMS_LOCK_2026_07_31.md) · [pilot-claim-boundary](pilot-claim-boundary-2026.md) · [ADR-001](architecture/ADR-001-verdict-ownership-2026.md) · [ENGINEERING_STATUS_2026_08](ENGINEERING_STATUS_2026_08.md)

> **Refresh 2026-08-01:** eng remediations landed on `main` (HEAD `8f02baf`): LIC-001 Option B (core PDF `pypdfium2`+`pdfminer`; PyMuPDF `pdf-agpl` only); OCR-aware EI; public CC BY IFC samples; **P2-04** claimed-GUID → `ifc_guid` only after spatial-index presence; **P2-02** `edge_kinds` + optional AABB broadphase (`geometry_verified=False`); Docker offline track VERIFIED / bare-metal **DEFERRED**. Checkpoint remains **NO_GO** (RT-001/002/003 OPEN). See [ENGINEERING_STATUS_2026_08](ENGINEERING_STATUS_2026_08.md).
>
> **Refresh 2026-08-02:** P0 TechLab eng package WP-01…08 landed under Claims Lock — [`ENGINEERING_STATUS_2026_08`](ENGINEERING_STATUS_2026_08.md) · Red Team [`quality/RED_TEAM_P0_ROLLUP_2026_08_02.md`](quality/RED_TEAM_P0_ROLLUP_2026_08_02.md). Актуальные гейты/метрики — [runtime baseline](evidence/runtime-baseline-latest.json). Hybrid AI: WP-02 advisory pre-gate on Analyze (verdict-neutral, OFF==ON). Цифры в §1 ниже — исторический снимок 2026-07-19/20 (не переписываю). Checkpoint **NO_GO**.

## 1. Gate runs (this audit)

| Gate | Result | Evidence class |
|------|--------|----------------|
| `ruff format --check src tests` | **PASS** (249 files) | runtime |
| `ruff check src tests` | **PASS** | runtime |
| `mypy src` | **PASS** (151 files) | runtime |
| `pytest tests -q` | **662 passed, 4 skipped** (local 2026-07-20 Red Team remediation) | test |
| `evaluate_extraction --min-macro-f1 0.70` | **PASS** (macro_f1≈0.86 on RU fixtures) | benchmark/fixture |
| Frontend vitest | **25 passed** (main CI `frontend` job) | test |
| Docker smoke | **NOT_RUN** in this session | needs env |
| Live review smoke | **NOT_RUN** in this session | needs env |

Baseline snapshot: [`evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json) — src≈22808 LOC, tests≈14562 LOC, 581+ test functions (export tool; collect shows 654).

## 2. Inventory (confirmed by code)

| Area | Path / fact | Status class |
|------|-------------|--------------|
| Entry / DI | `backend` FastAPI + `bootstrap_container` | confirmed code |
| Contours | INGESTION → DETERMINISTIC → AI_ADVISORY → EVIDENCE | confirmed code + ADR-001 |
| Ports / adapters | Domain Protocol ports + infra adapters via Tokens | confirmed code |
| Project-package API | `POST /v1/analyze/project-package` | confirmed code + tests |
| Capabilities honesty | `CapabilityState`: ok/skipped/failed/missing/not_verified/not_implemented | confirmed code |
| Sign-off profiles | development/fixture/samolet_pilot/production; non-dev→production default | confirmed code + tests |
| Shared-gate | `summary.passed` bool; AI/OCR cannot flip | confirmed code + tests |
| Hybrid AI foundation + WP-02 advisory pre-gate | `HybridRouteGate` on Analyze advisory; verdict-neutral (OFF==ON); never sets `summary.passed` | confirmed code + tests |
| BCF export | 2.1 stable, 3.0 experimental structural | confirmed code + T1 JSON |
| CDE import | STATUS NOT_VERIFIED | needs customer |
| Frontend | review shell 3D+2D+HITL remarks | confirmed code + vitest |
| Samples | `samples/benchmarks/*`, IFC/IDS fixtures | confirmed code |
| Public docs | TechLab jury pack only (`docs/TIER0_INDEX.md`) | confirmed docs |
| Operator dumps | `.local/engineering-docs/` gitignored | confirmed hygiene |

## 3. Capability evidence matrix (audit vocabulary)

Legend: **code** · **test** · **runtime** · **benchmark** · **README-only** · **planned** · **broken** · **needs_customer**

| Capability | Verdict | Notes |
|---|---|---|
| IFC property/quantity (2x3/4/4x3) | code+test+benchmark | Fixture corpus; not product accuracy |
| IDS 1.0 | code+test | Fail-closed when requested misconfigured |
| Cross-document contradictions | code+test | ConflictKind subset |
| Drawing annotation ↔ IFC | code+test | P2-04: claimed GUID → `ifc_guid` only after spatial-index presence; OCR optional-extra |
| Core PDF (pypdfium2/pdfminer) | code+test | LIC-001 Option B; PyMuPDF optional `pdf-agpl` only |
| Clash (IfcClash) | code+test | Optional extra; pilot/production require_clash |
| MEP system-aware clash | needs_customer + eng foundation | ENG_PARTIAL: edge_kinds + AABB broadphase; always `geometry_verified=False`; RT-003 OPEN |
| Offline Docker image-track | code+test (eng) | VERIFIED; bare-metal DEFERRED |
| Native DWG | broken/not claimed | Honesty never OK as product DWG |
| DXF EntityGraph | code+test (optional `[cad]`) | Partial; never masks DWG failure |
| Calculation **сверка** | code+test | Correctness NOT_IMPLEMENTED |
| Independent calc solver | planned / not claimed | — |
| Norm rule packs | code+test synthetic; full approval contract | Customer-approved pack needs_customer (RT-002 OPEN) |
| Extraction F1 (RU) | benchmark fixture | ≠ product accuracy (RT-001) |
| Precision >90% | needs_customer | **FORBIDDEN** until dual adjudication |
| Package SLA ≤30 min | benchmark fixture_only | Customer SLA needs_customer |
| BCF ZIP structural | code+test+runtime artifact | CDE import needs_customer |
| BCF API push | code scaffold | Hub-dependent; not CDE proof |
| HTML/JSON reports | code+test | — |
| Provenance finding_id/evidence_refs | code+test | Persist reject if missing |
| Object ACL | code+test | Cross-tenant **404** |
| SSRF outbound guard | code+test | JWKS/bSI/OpenCDE |
| HITL remark edit | code+test | Does not flip Shared-gate alone |
| Evidence bundle CLI | code+test | `export_evidence_bundle` + fixture pack |
| Hybrid AI + WP-02 advisory pre-gate | code+test | Gate before Analyze advisory observations; OFF==ON for `summary.passed`; masking ≠ anonymity |
| Package multi-status enum | planned (Wave2) | Today: derive from `passed`+capabilities |

## 4. README drift (must not claim)

- «290+ tests» — outdated; use collect/baseline.
- Production-ready / full MEP / DWG-ready / CDE-ready BCF / calc correctness / >90% — **forbidden** without evidence.
- Soft clash under pilot/production — **not** allowed (profile forces fail-closed).

## 5. Three risks / three next steps

**Risks:** (1) Shared-gate misread as Published; (2) fixture metrics sold as Samolet value; (3) pilot without reproducible evidence bundle.

**Next:** (1) claim matrix + pilot protocol (this wave); (2) `export_evidence_bundle` + gap tests; (3) customer intake for RT-001/002/003 (external).

## 6. Derived package outcome

`summary.outcome` (`PackageOutcome`) is the package reading; `summary.passed` is derived from it.

| Expert reading | Runtime signals |
|---|---|
| PASS | `outcome=pass` and required capabilities OK |
| PASS_WITH_WARNINGS | `outcome=pass_with_warnings` |
| BLOCKED | intake blocked or required capability SKIPPED/FAILED/NOT_VERIFIED under pilot/production |
| FAILED | deterministic ERROR findings / hard clash blocks |
| REVIEW_REQUIRED | HITL regions require review |

Do **not** invent PASS when any mandatory check did not complete successfully. Checkpoint **NO_GO** until RT-001/002/003.
