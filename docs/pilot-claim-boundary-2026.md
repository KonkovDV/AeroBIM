---
title: "AeroBIM Pilot Claim Boundary 2026"
status: active
version: "1.3.0"
last_updated: "2026-07-17"
tags: [aerobim, pilot, claims, evidence]
---

# AeroBIM Pilot Claim Boundary

This document separates **verified repository evidence** from **roadmap intent** for pilot and accelerator communications.

**Stakeholder distribution:** share with [`pilot-start-package-2026.md`](pilot-start-package-2026.md) at pilot kickoff.  
**TZ preparation SSOT:** [`tz/README.md`](tz/README.md).  
**Forbidden wording SSOT:** [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md).  
**Checkpoint:** **`NO_GO`** until RT-001/002/003 close ([`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md)).

## TZ MVP scope (honest framing)

| Scope | In MVP sign-off | Outside sign-off |
|-------|-----------------|------------------|
| Deterministic IFC/IDS/cross-doc/clash + OCR baseline + template remarks + HITL | Yes (fixture-verified; customer pack TBD) | — |
| Multipart upload + remarks UI edit (P0) | Target for TZ demo | — |
| CV layout models, LLM remarks/IDS, DWG entity CAD | — | Advisory / Phase 2+ |
| “AI reads drawings like a human” / unsupervised VLM drawing literacy | — | **Out of pilot acceptance** |
| Clash / inconsistency **>90%** accuracy | — | Only after labeled corpus + ≥2 adjudicators + κ/α |

## Verified (may be claimed with evidence)

| Claim | Evidence source |
|---|---|
| Deterministic IFC + IDS + cross-document validation | `pytest` suite, benchmark packs |
| Multimodal project-package analysis | `POST /v1/analyze/project-package`, benchmark manifests |
| Fail-closed required clash / raster zero-yield / provenance persist | P0 tests; Claims Lock |
| Object ACL on report artifacts | API principal + `tenant_id` |
| BCF 2.1/3.0 ZIP export — **structural T1** | `audit/evidence/bcf-structural-handoff-2026-07-17.json` |
| Browser review shell (3D + 2D evidence) | Frontend vitest **21** passed; `run_live_review_smoke` |
| OpenRebar provenance digest (**сверка**, not correctness) | Digest endpoint + `claim_labels` |
| ISO 19650-lite context fields on reports | Optional request/report fields (Shared-gate metadata, not CDE) |
| Extraction quality metrics (RU **fixtures**) | `evaluate_extraction`; fixture macro_f1 ≠ product accuracy |
| Package SLA on **fixture** pack (schema 1.2, `fixture_only`) | `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json` |
| System honesty surface | `GET /v1/system/capabilities` |
| Explicit report capabilities | `capabilities.{clash,ids,unit_scale,ifc_schema,norm_rule_packs,section_pairing,dwg_dxf,mep_system_clash,…}` ∈ ok/skipped/failed/not_verified; **FAILED blocks `summary.passed`** |
| Infra failure honesty (RT-C) | Unexpected exceptions in quantity / load / MEP probe → capability **FAILED** + traceback log (not soft WARNING/NOT_VERIFIED) |
| Mixed CAD package honesty (RT-D) | Unparsed `.dwg` in package with successful `.dxf` → `capabilities.dwg_dxf=FAILED` (DXF success must not mask DWG) |
| Advisory isolation (RT-E / RT-017) | Same non-empty package: advisory ON vs OFF → identical deterministic findings + identical `summary.passed`; only advisory remarks/warnings may differ |
| Non-dev auth fail-closed (RT-F) | `AEROBIM_ENV != development` + empty bearer + no OIDC → Settings/bootstrap refuse start |
| RT-001 protocol readiness (engineering) | Customer labels template + `dual_independent` method + agreement-template + runbook `--agreement-json`; **publishable still HOLD** without customer corpus |
| RT-002 schema↔loader parity | `customer_approved`/`approved` require full `approval` object in JSON Schema (ref-only rejected) |
| RT-003 MEP scaffold honesty | Agent `detect_system_clash` → `degraded`; gap doc matches DI wiring; product MEP still HOLD |
| Norm rule packs fail-closed (P0.2) | Requested/configured pack load error → `capabilities.norm_rule_packs=failed` → `summary.passed=false`; packs not requested → `skipped` (does not block) |
| PrecisionClaim publish gate (R1/R4) | Typed claim; render withheld unless `corpus_kind=customer` and ≥2 adjudicators |
| Runtime baseline metrics (R5) | `python -m aerobim.tools.export_runtime_baseline` — LOC/tests/F1 not hand-authored |
| Internal self-audit naming (R2) | Self assessments must not be labeled external/independent |
| Four contours | ingestion / deterministic_validation / ai_advisory / evidence_reporting — AI cannot mutate `passed`; Analyze UC coordinates contour orchestrators (RT-A) |
| I9 IFC KG port wiring | Domain port + DI + `query_ifc_kg` + fixture `evaluate_ifc_qa` — **advisory scaffold only** |
| JSON norm / rule-pack loader | `NormRulePackLoader` + residential AR reference template (synthetic-template only) |
| Deterministic PD↔RD section pairing scaffold | `SectionDiffAnalyzer` on normalized section JSON (one discipline pair) |
| Detection precision harness (exact TP/FP/FN) | `aerobim-evaluate-detection-precision` + synthetic contract fixture + protocol gate |
| Typical-errors catalog scaffold ≥20 patterns | `samples/benchmarks/samolet-typical-errors-catalog.json` + mapping tool |
| Schema-valid IFC pre-gate available | `BasicIfcSchemaValidator` + `capabilities.ifc_schema` |
| IDS document audit before model check | `XmlIdsDocumentAuditor` + `AEROBIM-IDS-AUDIT` |
| BCF API 3.0 topic push (OpenCDE) | `POST .../export/bcf-api/push` with hub Bearer token |
| ISO 19650-lite CDE state on reports | `iso19650` block on public report JSON |
| OIDC JWT alongside static bearer | `AEROBIM_OIDC_*` + enterprise `PyJWT` |
| Optional bSI / local schema certificate id | `schema_validation_request_id` + `capabilities.ifc_schema.external_ref` |
| Postgres/filesystem filtered report index | `GET /v1/reports?project=&discipline=&passed=` |
| Revit thin-client deep-link helper | `clients/revit-plugin/scripts/export_and_open_report.py` + UI `?report=` |
| HITL review events / KPI | `POST/GET .../review-events`, `GET .../review-kpi` |
| LOIN information levels on issues | `loin_information_level` ∈ geometry/alphanumeric/documentation |
| Spatial predicates separate from IDS | `FindingCategory.SPATIAL` + `SPATIAL-*` issues from clash results |
| EN structured extraction corpus | `english-aec-ground-truth.json` (macro F1 1.0 on structured fixtures) |
| Ablation paper table | `docs/evidence/ablation-study-paper-table-2026.md` |
| TZ Response Pack (architecture/build/presentation TBD fills) | [`docs/tz/README.md`](tz/README.md) |
| Multipart document upload | `POST /v1/uploads` → storage-relative path |
| EN remark templates | `AEROBIM_REMARK_LOCALE=en` + `TemplateRemarkGenerator` |
| Remarks panel HITL edit | Frontend remark editor → `POST .../review-events` (`edited_remark`) |

## Planned (do not claim as deployed)

| Item | Status |
|---|---|
| Optional raster/PDF drawing path (OCR baseline) | `RasterDrawingAnalyzer` port — deterministic today |
| Non-deterministic text extraction training | Not in pilot sign-off path |
| Full OIDC multi-tenant auth | OIDC JWT validation available; full SSO/BFF still post-pilot |
| arq/Redis async queue | Redis job store available when `AEROBIM_REDIS_URL` set; arq workers still post-pilot |
| BCF API / OpenCDE integration | Topic push foundation live; **CDE import T2 NOT_VERIFIED**; full hub sync post-pilot |
| Live bSI Validation Service submit in pilot | Local cert / mocked client tested; live hub needs credentials |
| LLM IDS drafting assist | Stub only — **advisory, never in sign-off path** |
| True computer vision for drawings | Not implemented; OCR baseline ≠ CV |
| Native DWG as product-ready CAD | Still missing / fail-closed; DXF optional `[cad]` EntityGraph never claims `dwg_dxf=OK` |
| Published clash/inconsistency accuracy >90% | Not measured; do not claim until adjudication |
| Synthetic precision fixture scores as product accuracy | Harness-only (`4 TP / 2 FP / 2 FN` contract); not customer evidence |
| Customer-approved residential norm pack | Reference template only; approval metadata required before sign-off |
| System-aware MEP clash (routing/clearances) | Explicit gap `MEP-CLASH-001`; generic clash only |
| IfcLLM / GraphRAG multi-hop IFC QA | **Not shipped** — I9 remains advisory scaffold; stub/relational fixture ≠ product KG |
| Production rollout / confirmed revenue | Requires customer documents outside repo |

## Non-claims (explicit boundaries)

1. AeroBIM is **decision-support** for engineering QA, not a licensed-engineer replacement.
2. AeroBIM does **not** assert full regulatory code compliance across all document types.
3. AeroBIM does **not** claim to outperform Solibri globally — only a bounded open pilot path.
4. Non-deterministic text extraction is **not** used for pilot sign-off; deterministic regex path meets F1 gates in CI.
5. Optional LLM **IDS assist** (if enabled later) is **advisory only** and must never affect `summary.passed` without human-in-the-loop.
6. TZ wording «точность >90%» is an **evaluation target**, not a verified product claim, until precision/recall is published from a labeled customer corpus.
7. AeroBIM does **not** claim that OCR, CV, or VLMs “read drawings like a licensed engineer”. See [evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
9. AeroBIM does **not** claim IfcLLM / GraphRAG product capability. I9 is an **advisory scaffold** (port + allowlisted query + fixture QA); multi-hop GraphRAG is unshipped.

## Reproducibility baseline

```bash
cd backend
python -m venv .venv-pilot
.venv-pilot\Scripts\activate   # Windows
pip install -e ".[dev,raster]"
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
python -m aerobim.tools.evaluate_detection_precision \
  --labels ../samples/benchmarks/detection-precision/labels-synthetic.json \
  --detections ../samples/benchmarks/detection-precision/detections-synthetic.json \
  --min-precision 0.6 --min-recall 0.6 --min-f1 0.6
python -m aerobim.tools.export_runtime_baseline
```

Use an **isolated** virtual environment under `AeroBIM/backend/.venv-pilot`, not the monorepo root `.venv`.

## Sync surfaces

Keep aligned with:

- [partners/TECHLAB_SAMOLET_APPLICATION_2026.md](partners/TECHLAB_SAMOLET_APPLICATION_2026.md)
- [README.md](../README.md) Scientific Reporting Standard section
- [rule-packs/README.md](rule-packs/README.md)
- [section-pairing/README.md](section-pairing/README.md)
- [evaluation/DETECTION_PRECISION_PROTOCOL_2026.md](evaluation/DETECTION_PRECISION_PROTOCOL_2026.md)
- [roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md](roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md)
- [evidence/EXTERNAL_STANDARDS_CHECK_2026_07_10.md](evidence/EXTERNAL_STANDARDS_CHECK_2026_07_10.md)
- [architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md](architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md) — literature map (not product claims)
- [architecture/EXECUTION_PLAN_I8_I9_2026_07.md](architecture/EXECUTION_PLAN_I8_I9_2026_07.md) — planned advisory waves (no GO)
- [../audit/reports/CLAIMS_LOCK_2026_07_17.md](../audit/reports/CLAIMS_LOCK_2026_07_17.md) — allowed / forbidden wording
