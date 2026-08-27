---
title: "AeroBIM Capability Claim Matrix 2026"
status: active
version: "1.4.1"
last_updated: "2026-08-28"
claim_boundary: "Sync with CLAIMS_LOCK. Checkpoint NO_GO until RT-001/002/003. Eng readiness ≠ customer GO."
---

# Capability × Claim Matrix (TechLab / Samolet)

Companion to [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md), eng freeze [`../audit/reports/CLAIMS_LOCK_2026_07_31.md`](../audit/reports/CLAIMS_LOCK_2026_07_31.md), and IUA [`quality/INTERPRETATION_USE_LEDGER_2026_08.md`](quality/INTERPRETATION_USE_LEDGER_2026_08.md).

API honesty surface: `GET /v1/system/capabilities` schema **1.3.0** (`direction_contracts`, `bcf_t2`, `mep_intake`).

## Four gap directions (honest statuses)

| Direction | Code readiness | Fixture | Customer | Status vocabulary |
|---|---|---|---|---|
| Native DWG | MISSING (`Ezdxf` fail-closed; ODA stub off analyze) | — | — | never `dwg_dxf=ok` |
| DXF | PARTIAL optional `[cad]` | fixture TEXT/MTEXT | not claimed | never = DWG support |
| DWG→PDF/IFC route | derived provenance helper | unit | external prep | `available_as_derived_input` ≠ `dwg_supported` |
| Core PDF | `pypdfium2`+`pdfminer` (LIC-001 Option B) | unit+integration | — | PyMuPDF = optional `pdf-agpl` only |
| Annotation↔IFC GUID | P2-04 presence via spatial index | wall-guid demo pin | not adjudicated | never invent GUID |
| Geometric hard clash | when ifcclash configured | fixture | — | ≠ full MEP |
| MEP system graph | `edge_kinds` + optional AABB | ENG_FIXTURE | BLOCKED | RT-003 OPEN; always `geometry_verified=False` |
| MEP system-aware rules | matrix schema + intake | template | BLOCKED_CUSTOMER_DATA | MEP-CLASH-001 |
| Calculation match | load/qty/cross-doc/OpenRebar + xlsx/docx declared-field SHA | fixture | — | сверка only; ≠ solver; PDF fragile |
| Cross-document consistency | Shared-gate / section-diff | fixture | NOT_MEASURED customer | Labeled separately from within-sheet OCR; open-bench L1 ≠ RT-001 |
| Calculation correctness | NOT_IMPLEMENTED | — | — | no solver; native `.lir` closed |
| IFC streaming / disk R-tree | DESIGNED_NOT_IMPLEMENTED | unit snapshot | — | does not raise 256 MiB analyze cap |
| BCF 2.1 / T1 | AVAILABLE | integration | — | structural ZIP |
| BCF T2 CDE import | NOT_VERIFIED | empty proof dir | needs sandbox | no CDE_READY |
| Offline | Docker image-track | eng smoke | — | bare-metal DEFERRED |

## Forbidden until customer evidence

| Claim | Blocker | Allowed substitute |
|---|---|---|
| Product accuracy >90% | RT-001 | Fixture macro_f1 only; cite pack + SHA |
| Customer SLA ≤30 min | RT-001 / SLA honesty | Fixture SLA `claim_level=fixture_only` |
| Approved **customer** acceptance profile | RT-002 | Official MOEXP IDS exist ([coverage](evidence/norm-pack-moexp-coverage-2026-08.md)); Samolet `customer_approved` pack still absent — RT-002 **OPEN** |
| MEP system clash delivered | RT-003 | `mep_system_clash=NOT_VERIFIED`; edge_kinds/AABB ≠ verified geometric clash — RT-003 **OPEN** |
| AABB / connects = verified geometric clash | — | Always `geometry_verified=False` on analyze probe |
| Native DWG analysis | — | НЕ РЕАЛИЗОВАНО (`native DWG parser is not implemented`) |
| Independent calc correctness | — | Сверка переданных результатов и источников, не расчётный решатель |
| BCF ready for CDE | RT-008 T2 | Structural ZIP **AVAILABLE**; CDE import **NOT_VERIFIED** ([ladder](architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md)); requires log+screenshot+hashes |
| Bare-metal offline-ready (any air-gap) | — | Docker image-track only; bare-metal **DEFERRED** |
| Entire product is MIT (no third-party disclosure) | — | MIT for AeroBIM code; PDF/IFC stack has own licenses (LIC-001 Option B) |
| Production-ready / external academic audit | — | Self-audit + NO_GO |
| Hybrid AI makes the public API safe for customer data / masking = anonymity | — | Route only *policy-eligible*; masking reduces disclosure, not anonymity; WP-02 advisory pre-gate ≠ verdict path / anonymity guarantee |
| Cloud Qwen 3.8-Max / Alibaba Model Studio in product | Contour + Claims Lock | Profile `public_qwen38_max` stays NOT_VERIFIED; never default |
| Samolet CONFIDENTIAL via Yandex Studio *cloud* | Hybrid classification | Studio cloud = PUBLIC/INTERNAL only; on-prem Studio or local for RESTRICTED |
| «Qwen 3.8 in product» without SBOM pin | Weights not in offline bundle | Local open-weight or Studio URI+version pin with evidence |
| Open-corpora binary match / timing = product accuracy | RT-001 | WP-06 regression/timing only; fixture n=7 + BSI IDS n=290 (CC BY-ND); never >90% |
| OIDC BFF / SSO ready | POST-05 production IdP | Phase 2 stubs + Phase 3 lab; `auth_bff.status=NOT_IMPLEMENTED` |
| УКЭП / trust chain verified | crypto adapter missing | Envelope presence/hash audit only; `trust_chain=not_verified` |
| Wilson interim planner output = publishable customer precision | RT-001 | WP-07 `demonstrates_interim_target_publishable=false`; protocol only |

## Allowed with evidence pointers

| Claim | Evidence |
|---|---|
| Deterministic IFC/IDS/cross-doc Shared-gate | pytest + ADR-001 |
| Fail-closed pilot/production sign-off | `capability_policy` + `test_rt_remediation_post` / P0 suite |
| Provenance required on persist | `finding_provenance` + tests |
| Cross-tenant ACL → 404 | ACL tests |
| SSRF guard on outbound JWKS/bSI/OpenCDE | `outbound_url.py` + tests |
| BCF 2.1/3.0 structural export | `audit/evidence/bcf-structural-handoff-2026-07-25.json` |
| HITL remark edit | frontend + review-events API |
| Extraction F1 on RU fixtures | `evaluate_extraction`; baseline JSON |
| Fixture reproducibility hash | `run_manifest.json` + `test_golden_report` |
| Hybrid AI routing + WP-02 advisory pre-gate | `domain/hybrid/*` + `HybridRouteGate` on Analyze advisory; OFF==ON; never sets `summary.passed` — [`HYBRID_AI_FINAL_REPORT`](../audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md) |
| Local Qwen advisory remark compose (KT#2 W1) | `private_qwen_local` + `OpenAICompatLlmProvider` + `compose_advisory_remark`; `ai_generated` + expert required; cloud Max NOT_VERIFIED — `QWEN_LOCAL_KT2_PLAN` |
| Yandex AI Studio grant path (KT#2 T2) | Same adapter; `private_yandex_ai_studio`; token caps; RF cloud for open corpora; on-prem for pilot — `YANDEX_AI_STUDIO_GRANT` |
| Runtime baseline complete (WP-01 / WP-R0) | `docs/evidence/runtime-baseline-latest.json` schema **1.4.0**; numeric `tests_passed` (backend+frontend); five `quality_gates=PASS`; `publishable` requires clean tree + CI attestation; CI `baseline-integrity` (`--check-publishable`) + `--check-readme` |
| Executable Claims Lock linter (WP-R10) | `scripts/lint_claims.py` (patterns from this matrix); CI blocking; `--matrix-guard` enforces Samolet-blocked rows ≠ `done` |
| Detached signature envelope (WP-03) | `qualified_signature` ENG_PARTIAL; trust_chain NOT_VERIFIED — never «УКЭП проверена» |
| Norm pack v2 eligibility (WP-04) | Schema 2.0.0 RASE + journal; RT-002 OPEN |
| Package completeness inventory (WP-05) | Soft opt-in; fixture-grade; no native DWG |
| Open corpora profiles (WP-06) | `samples/benchmarks/open-corpora/`; fixture n=7 + BSI IDS `regression-bsi` n=290 (CC BY-ND unmodified); CI smoke pins |
| OIDC BFF Phase 2 stubs (POST-05) | login/callback/logout + CSRF; Phase 3 lab behind `oidc_bff_phase3_ready`; status stays NOT_IMPLEMENTED |
| BCF T2 checklist verifier | `--checklist` dry-run; STATUS stays NOT_VERIFIED until real CDE evidence |
| VLM kimi smoke PUBLIC egress gate | `vlm_smoke_gate` before client; blocked → zero bytes |
| Quality measurement protocol (WP-07) | [`pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md); interim 0.60; never >90% |
| Core PDF via pypdfium2/pdfminer (LIC-001 Option B) | `test_dependency_license_gate.py` + `test_pdfium_region_cropper.py`; inventory + [`license-policy-2026.md`](license-policy-2026.md) |
| Annotation claimed-GUID presence (P2-04) | spatial-index lookup; wall-guid demo pin [`evidence/checkpoint2-evidence-bundle-latest.json`](evidence/checkpoint2-evidence-bundle-latest.json) |
| MEP edge provenance + AABB broadphase (eng) | `edge_kinds` + `AEROBIM_MEP_AABB_FILTER`; always `geometry_verified=False` — [`roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md`](capability-claim-matrix-2026.md) |
| Per-source check-coverage map (four presentation states) | `domain/check_coverage.py` + Hypothesis I-8; `tz_gaps`; HTML+PDF export coverage first page; frontend `CoverageMapPanel`; `GET /v1/reports/{id}/coverage` + `/export/pdf` |
| Native MS Office ingest (WP-R1) | `python-docx`+`openpyxl` core path in `docling_office_document_ingestor`; `office_ingest` capability; legacy `.doc`/`.xls` fail-closed — `test_office_native_ingest` |
| Advisory domain modules (drawing region quality/type/assessment, revision diff, norm applicability) | `domain/{region_quality,region_classifier,drawing_region_assessment,revision_diff,norm_applicability}.py` + tests; domain-pure, verdict-neutral (do NOT set summary.passed), fixture-only, NOT wired into ingestion/verdict; bad/unknown/ambiguous → escalate, never a silent OK/guess |

## Run manifest (iteration 2026-07-21)

Evidence bundles emit `run_manifest.json` with `reproducibility_hash` over deterministic engine findings + capability digest (excludes `report_id` / timestamps). Golden baseline hash pinned in `backend/tests/test_golden_report.py`. **Fixture only** — not customer accuracy.

`PackageOutcome` enum landed on `summary.outcome` (`pass` / `pass_with_warnings` / `review_required` / `blocked` / `failed`). `summary.passed` is derived only via `summary_passed_from_outcome` (true for PASS / PASS_WITH_WARNINGS). Evidence bundles prefer `summary.outcome` for `derived_outcome`.

| Reading | Signals |
|---|---|
| PASS | `summary.outcome=pass` + required caps OK |
| PASS_WITH_WARNINGS | `outcome=pass_with_warnings` (non-blocking WARNING findings) |
| BLOCKED | intake blocked or required cap not OK under hard profile (often `error_count=0`) |
| FAILED | deterministic ERROR findings / hard clash under clash_affects_pass |
| REVIEW_REQUIRED | HITL regions require review |

Checkpoint remains **NO_GO** until RT-001/002/003 customer evidence. `summary.passed` remains Shared-gate technical status — **not** Shared→Published.
