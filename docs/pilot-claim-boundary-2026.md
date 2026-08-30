---
title: "AeroBIM Pilot Claim Boundary 2026"
status: active
version: "1.13.8"
last_updated: "2026-08-30"
tags: [aerobim, pilot, claims, evidence]
---

# AeroBIM Pilot Claim Boundary

This document separates **verified repository evidence** from **roadmap intent** for pilot and accelerator communications.

**Формула стадии (дословно):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет независимого размеченного корпуса, двух разметчиков, профиля приёмки (публичные IDS экспертизы — измерение; подпись Самолёта — внедрение) и подтверждения импорта в СОД.

**Checkpoint:** **`NO_GO`**. RT-001 / RT-002 / RT-003 OPEN. Form 5/5 ≠ Checkpoint GO. Дословная формула речи: [`demo/KT2_JURY_FAQ_2026_08_12.md`](demo/KT2_JURY_FAQ_2026_08_12.md). Blockers: [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md).

**Stakeholder distribution:** share [`docs.md`](docs.md) (jury memo) + [`partners/TECHLAB_TASK_07_READINESS_2026.md`](partners/TECHLAB_TASK_07_READINESS_2026.md) at kickoff; map: [`TIER0_INDEX.md`](TIER0_INDEX.md).  
**Индекс ТЗ:** [`tz/README.md`](tz/README.md).  
**Запрещённые формулировки:** [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) · датированная заморозка [`../audit/reports/CLAIMS_LOCK_2026_07_31.md`](../audit/reports/CLAIMS_LOCK_2026_07_31.md).

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
| Multi-**source** project-package analysis (IFC+PDF+drawings+IDS) | `POST /v1/analyze/project-package`, benchmark manifests |
| Vision endpoint accepts images | Grant smoke HTTP 200; **open-bench** AECV counting on Yandex Qwen measured (macro exact-match 0.4325, `open_bench_only`) — **not** product / RT-001 accuracy |
| Fail-closed required clash / raster zero-yield / provenance persist | P0 tests; Claims Lock |
| Object ACL on report artifacts | API principal + `tenant_id` |
| BCF 2.1/3.0 ZIP export — **structural T1** | `audit/evidence/bcf-structural-handoff-2026-07-25.json` |
| Browser review shell (3D + 2D evidence) | Frontend vitest **57** passed (CI pin `docs/evidence/runtime-baseline-latest.json`, `attested_by=ci`, backend commit `fc1f03838cb6`); `run_live_review_smoke` |
| OpenRebar provenance digest (**сверка**, not correctness) | Digest endpoint + `claim_labels` |
| ISO 19650-lite context fields on reports | Optional request/report fields (Shared-gate metadata, not CDE) |
| Extraction quality metrics (RU **fixtures**) | `evaluate_extraction`; fixture macro_f1 ≠ product accuracy |
| Package SLA on **fixture** pack (schema 1.2, `fixture_only`) | `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json` |
| System honesty surface | `GET /v1/system/capabilities` |
| Explicit report capabilities | `capabilities.{clash,ids,unit_scale,ifc_schema,norm_rule_packs,section_pairing,dwg_dxf,mep_system_clash,…}` ∈ ok/skipped/failed/not_verified; **FAILED blocks `summary.passed`** |
| Shared-gate `summary.passed` ownership | ADR-001: deterministic inputs + EvidenceAssembler writer; AI/OCR cannot flip; ≠ Shared→Published |
| Production / pilot sign-off fail-closed | Non-dev defaults `production` profile; soft clash env flags ignored under pilot/production |
| Cross-tenant ACL | Deny → **404**; object enumeration avoided |
| Outbound SSRF guard | JWKS / bSI / OpenCDE URL validation |
| Infra failure honesty (RT-C) | Unexpected exceptions in quantity / load / MEP probe → capability **FAILED** + traceback log (not soft WARNING/NOT_VERIFIED) |
| Mixed CAD package honesty (RT-D) | Unparsed `.dwg` in package with successful `.dxf` → `capabilities.dwg_dxf=FAILED` (DXF success must not mask DWG) |
| Advisory isolation (RT-E / RT-017) | Same non-empty package: advisory ON vs OFF → identical deterministic findings + identical `summary.passed`; only advisory remarks/warnings may differ |
| HITL §12 visual distinction | Advisory candidate vs confirmed finding, low-confidence cue, `review_required` outcome — visually distinct + vitest; text XSS prevented by React (no `dangerouslySetInnerHTML`); preview MIME allowlist (`api.ts`) |
| Fail-closed Shared-gate (2026-07-28) | Verdict single-source (`summary_passed_from_outcome`); advisory OFF==ON re-confirmed; OIDC validator build fail-closed without `assert` |
| Remark storey / axis from IFC index | `IfcSpatialIndex` containment (`IfcBuildingStorey`) and `IfcGridAxis.AxisTag` when the GUID hits; missing is explicit in the template; **not** OCR / LLM text |
| Non-dev auth fail-closed (RT-F) | `AEROBIM_ENV != development` + empty bearer + no OIDC → Settings/bootstrap refuse start |
| RT-001 protocol readiness (engineering) | Customer labels template + `dual_independent` method + agreement-template + runbook `--agreement-json`; **publishable still HOLD** without customer corpus |
| RT-002 schema↔loader parity | `customer_approved`/`approved` require full `approval` object in JSON Schema (ref-only rejected) |
| RT-003 MEP scaffold honesty | Agent `detect_system_clash` → `degraded`; gap doc matches DI wiring; product MEP still HOLD |
| Norm rule packs fail-closed (P0.2) | Requested/configured pack load error → `capabilities.norm_rule_packs=failed` → `summary.passed=false`; packs not requested → `skipped` (does not block) |
| PrecisionClaim publish gate (R1/R4) | Typed claim; render withheld unless `corpus_kind=customer` and ≥2 adjudicators |
| Runtime baseline metrics (R5) | `python -m aerobim.tools.export_runtime_baseline --run-gates --require-clean-tree` — numeric `tests_passed`, `publishable: true` only on clean tree; see `docs/evidence/runtime-baseline-latest.json` |
| Claims Lock CI linter (WP-R10) | `python scripts/lint_claims.py` + `--matrix-guard` — machine-checkable forbidden claims |
| Internal self-audit naming (R2) | Self assessments must not be labeled external/independent |
| Four contours | ingestion / deterministic_validation / ai_advisory / evidence_reporting — AI cannot mutate `passed`; Analyze UC coordinates contour orchestrators (RT-A) |
| I9 IFC KG port wiring | Domain port + DI + `query_ifc_kg` + fixture `evaluate_ifc_qa` — **advisory scaffold only** |
| JSON norm / rule-pack loader | `NormRulePackLoader` + residential AR reference template (synthetic-template only) |
| Deterministic PD↔RD section pairing scaffold | `SectionDiffAnalyzer` on normalized section JSON (one discipline pair) |
| Detection precision harness (exact TP/FP/FN) | `aerobim-evaluate-detection-precision` + synthetic contract fixture + protocol gate |
| Typical-errors catalog scaffold ≥20 patterns | `samples/benchmarks/samolet-typical-errors-catalog.json` + mapping tool; 28.08: 2 acceptance checklists detected in owner pack (counts only) — **not ingested**, `customer_confirmed_patterns` stays 0, catalog not customer-accepted |
| Schema-valid IFC pre-gate available | `BasicIfcSchemaValidator` + `capabilities.ifc_schema` |
| IDS document audit before model check | `XmlIdsDocumentAuditor` + `AEROBIM-IDS-AUDIT` |
| BCF API 3.0 topic push (OpenCDE) | `POST .../export/bcf-api/push` with hub Bearer token |
| ISO 19650-lite CDE state on reports | `iso19650` block on public report JSON |
| OIDC JWT alongside static bearer | `AEROBIM_OIDC_*` + enterprise `PyJWT` |
| Static API bearer scope (KT#2 honesty) | Shared `AEROBIM_API_BEARER_TOKEN` is **pilot transport auth only** — may authenticate uploads/reads; **must not** create expert HITL accept/reject/sign events (`is_service_token` denied). Expert verdicts require OIDC (or equivalent) principal with reviewer/admin role under pilot/production profiles |
| HITL reviewer-role gate profile boundary (N-49) | `enforce_hitl_reviewer_auth` / `require_hitl_reviewer_roles` are **on only** for `signoff_profile` ∈ `{samolet_pilot, production}`. Development / fixture / default demo profiles do **not** require reviewer roles (static bearer still blocked). Do not demo role model under a non-pilot profile and claim the gate is live |
| Optional bSI / local schema certificate id | `schema_validation_request_id` + `capabilities.ifc_schema.external_ref` |
| Postgres/filesystem filtered report index | `GET /v1/reports?project=&discipline=&passed=` |
| Revit thin-client deep-link helper | `clients/revit-plugin/scripts/export_and_open_report.py` + UI `?report=` |
| HITL review events / KPI | `POST/GET .../review-events`, `GET .../review-kpi` |
| LOIN information levels on issues | `loin_information_level` ∈ geometry/alphanumeric/documentation |
| Spatial predicates separate from IDS | `FindingCategory.SPATIAL` + `SPATIAL-*` issues from clash results |
| EN structured extraction corpus | `english-aec-ground-truth.json` (macro F1 1.0 on structured fixtures) |
| Ablation / benchmark snapshot | `docs/evidence/benchmark-report-2026-05-21.md` |
| TZ Response Pack (architecture/build/presentation TBD fills) | [`docs/tz/README.md`](tz/README.md) |
| Multipart document upload | `POST /v1/uploads` → storage-relative path |
| EN remark templates | `AEROBIM_REMARK_LOCALE=en` + `TemplateRemarkGenerator` |
| Remarks panel HITL edit | Frontend remark editor → `POST .../review-events` (`edited_remark` / `accepted` / `rejected`) |
| Hybrid AI routing + WP-02 advisory pre-gate (eng) | `HybridRouteGate` mandatory before Analyze advisory observations; domain-pure, verdict-neutral (OFF==ON), fail-closed; never sets `summary.passed` |
| Detached signature envelope (WP-03) | Presence/hash/roles; `qualified_signature` ENG_PARTIAL; trust_chain always NOT_VERIFIED |
| Norm pack v2 eligibility (WP-04) | Schema 2.0.0 RASE + `execution_mode` + expert journal; fixture ≠ customer pack (RT-002 OPEN) |
| Package completeness inventory (WP-05) | Soft opt-in inventory checks; DWG native read not implemented; fixture-grade only |
| Open corpora profiles (WP-06) | 3 pinned profiles; honest regression n=7; regression/timing only — not product accuracy |
| Quality measurement protocol (WP-07) | Wilson P/R + sample-size planner; interim confirmed-finding target 0.60; never >90% |
| IFC+IDS evidence layer | This file — scope freeze; not 10D/Tangl replacement; Checkpoint **NO_GO** |
| Core PDF via pypdfium2/pdfminer (LIC-001 Option B) | Production PDF path; PyMuPDF optional `pdf-agpl` only — not a court opinion |
| Annotation claimed-GUID → `ifc_guid` (P2-04) | Presence confirm via spatial index only; wall-guid demo evidence pin |
| MEP edge provenance + AABB broadphase (eng) | `edge_kinds` + optional AABB; always `geometry_verified=False`; capability stays `NOT_VERIFIED` |
| Docker offline image-track | `offline_bundle` smoke; bare-metal **DEFERRED** |

## Planned (do not claim as deployed)

| Item | Status |
|---|---|
| Optional raster/PDF drawing path (OCR baseline) | `RasterDrawingAnalyzer` port — deterministic today |
| Non-deterministic text extraction training | Not in pilot sign-off path |
| Full OIDC multi-tenant auth | OIDC JWT validation available; full SSO/BFF still post-pilot |
| arq/Redis async queue | Redis job store **required** outside development; in-memory is dev/test only; arq workers still post-pilot |
| BCF API / OpenCDE integration | Topic push foundation live; **CDE import T2 NOT_VERIFIED**; target CDE identified 28.08 at address level (10D contour, session-gated — contents not read); closure path via public Swagger API + developer demo license on synthetic data is engineering evidence, not customer registry proof; full hub sync post-pilot |
| Live bSI Validation Service submit in pilot | Local cert / mocked client tested; live hub needs credentials |
| LLM IDS drafting assist | Stub only — **advisory, never in sign-off path** |
| True computer vision for drawings | Not implemented; OCR baseline ≠ CV |
| Native DWG as product-ready CAD | Still missing / fail-closed; DXF optional `[cad]` EntityGraph never claims `dwg_dxf=OK` |
| Native RVT / NWD | Same class as DWG; fail-closed; IFC 2x3/4/4x3 is the ingest path ([`tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md`](tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md)). ODA Sustaining ≠ BimRv ([`quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md`](quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md)) |
| Fixture AABB P/R = 1.0 at n=6 as a jury exhibit | Wilson 95% lower ≈ 0.61 (`wilson_interval(6, 6)`); stop-list KT#3 item 28 |
| Space-efficiency numeric KPI | Coverage map: not implemented; owner scope OA-14 OPEN |
| 5–10 packs/day | Customer-stated 25.08; not a measured SLA; `benchmark-thresholds.json` `publishable_sla=false` |
| Analyze default 1.5 GB SPF `open(.ifc)` | Ingest + RocksDB under stated Samolet caps; `AEROBIM_MAX_IFC_BYTES` stays **256 MiB**; WASM **256 MiB** |
| IFC streaming / disk R-tree | **Designed, not implemented**; JSON sidecar of `IfcSpatialIndex` ≠ disk R-tree |
| Published clash/inconsistency accuracy >90% | Not measured; do not claim until adjudication |
| Synthetic precision fixture scores as product accuracy | Harness-only (`4 TP / 2 FP / 2 FN` contract); not customer evidence |
| Customer-approved residential norm pack | Reference template only; approval metadata required before sign-off |
| System-aware MEP clash (routing/clearances) | Explicit gap `MEP-CLASH-001`; edge_kinds/AABB ≠ verified geometric clash; RT-003 OPEN |
| Bare-metal offline without Docker | DEFERRED; Docker track only |
| IfcLLM / GraphRAG multi-hop IFC QA | **Not shipped** — I9 remains advisory scaffold; stub/relational fixture ≠ product KG |
| Production rollout / confirmed revenue | Requires customer documents outside repo |
| Hybrid AI PUBLIC VLM egress + PrivacyGuard salt-on-egress | WP-02 advisory pre-gate landed on Analyze; PUBLIC VLM / mask-on-egress still residual (masking ≠ anonymity) |

## Non-claims (explicit boundaries)

1. AeroBIM is **decision-support** for engineering QA, not a licensed-engineer replacement.
2. AeroBIM does **not** assert full regulatory code compliance across all document types.
3. AeroBIM does **not** claim to outperform Solibri globally — only a bounded open pilot path.
4. Non-deterministic text extraction is **not** used for pilot sign-off; deterministic regex path meets F1 gates in CI.
5. Optional LLM **IDS assist** (if enabled later) is **advisory only** and must never affect `summary.passed` without human-in-the-loop.
6. TZ wording «точность >90%» is an **evaluation target**, not a verified product claim, until precision/recall is published from a labeled customer corpus.
7. AeroBIM does **not** claim that OCR, CV, or VLMs “read drawings like a licensed engineer” (see Claims Lock / this claim boundary).
8. AeroBIM does **not** claim Experiment B coverage percentages (e.g. KR **≈16.7%** of n=24 open-source remarks) as product detection rate on a customer corpus — they are **coverage-map** measurements with explicit out-of-scope classes; see [`evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md`](evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md).
9. AeroBIM does **not** claim IfcLLM / GraphRAG product capability. I9 is an **advisory scaffold** (port + allowlisted query + fixture QA); multi-hop GraphRAG is unshipped.
10. AeroBIM does **not** claim Hybrid AI is in the verdict path, nor that masking guarantees anonymity — WP-02 wires `HybridRouteGate` as an **advisory pre-gate** only (verdict-neutral, OFF==ON; blocked → no advisory observation).
11. AeroBIM does **not** replace 10D, Tangl, Renga, CDE, or the expert. First sell is a white-box IFC+IDS evidence layer; Checkpoint **NO_GO** until RT-001/002/003.
12. The SPb GAU CGE profile (`samples/profiles/spb-cge/`) is a published rule set (OFFICIAL_PUBLISHED), not a customer-signed acceptance profile. It does **not** close RT-001 or RT-002 and is not an expertise verdict.
13. AeroBIM does **not** SPF-open a 1.5 GB IFC and does **not** treat 1.5 GB as WASM capability, and does **not** treat «5–10 packs/day» as a published SLA.
14. After the 25.08 questionnaire, AeroBIM does **not** say the customer sent no data. The channel is received; a hashed pack is **not** in git; RT-001 stays OPEN. HTTPS / closed-cloud storage is a **stated** target — browser OIDC BFF remains `NOT_IMPLEMENTED`.
15. AeroBIM does **not** treat xlsx/docx declared-field **MATCH** as `calculation_correctness` or a LIRA solver. Native `.lir` is not parsed. PDF table compare stays **fragile**.
16. AeroBIM does **not** treat the IFC streaming / disk R-tree **design** as shipped, and does **not** raise the default **SPF** analyze cap from **256 MiB** because ingest allows 1.5 GB (that path is RocksDB).
17. AeroBIM does **not** treat HTTP upload of `.lir`/`.spr` as a silent skip or a solver path. The closed reason is explicit; ZIP members are rejected the same way as native Autodesk.
18. AeroBIM does **not** treat a JSON dump of `IfcSpatialIndex` as a disk R-tree or a streaming parser, and does **not** wire that dump into analyze.
19. The two numeric TZ criteria (clash recall >90%, pack-check time) are **not customer-confirmed**: the 25.08 answers document never mentions 90%, SLA, or time. AeroBIM neither claims them nor accepts them as agreed until a measurement protocol (golden remark set, corpus size, time endpoints) is answered in writing.
20. The internal-standards and BIM-regulations list was **issued** on 25.08 (two links inside answer 1.2.1 to internal CDE project folders); the norm-pack blocker is **access to the issued material**, not missing data — the ask is to publish the two folders the same way as the dataset. Direct CDE API integration is **not** a customer requirement (п. 2.2.2: file import/export via web UI suffices); it stays an optional differentiator.
21. Typical-node checks are **not** IFC-ready: п. 1.2.3 places the node library as PDF/DWG in the same closed 1.2.1 folders; native DWG stays unread. Cloud is allowed (п. 3.1.1); the requirement is **per-project isolation** of stored data, not on-prem deploy and not “HTTPS equals isolation”. Horizontal scale is an architecture point for later, **not** an MVP deliverable and **not** a load figure at defense (п. 3.2.2).
22. The depersonalization + NDA ask to organizers is **the customer's own clause** (п. 3.1.2), not extra caution from the team. AeroBIM does **not** treat the delivered channel as a depersonalized NDA pack.
23. AeroBIM is an **engineering-compare engine** with a measurement protocol, not a documentation platform and not a replacement for the customer's CDE or BIM-data stack. Version overlay of RD packs is **not** a differentiator (the customer already ships it). TR-67 is spec-volume vs drawing/BIM, **not** model-to-estimate quantities.
24. Benefit speech uses expert-hours per pack, share of remarks caught before production issue, and re-entry count — **not** «innovation» and **not** a multiple of EBITDA. The citation linter (`lint_citation_twins`) is shown as source discipline (fabricated DOI / same-article year twins), not as product accuracy.
25. Catalog questionnaire answers, demo video frames, and slides are **publication** (same gate as git). AeroBIM does **not** treat machine-readable information requirements or RD version overlay as differentiators, and does **not** transfer a competitor's published figure as our metric. Self-assessment against GOST R 72514-2026 (ISO/IEC 42005:2025) is **not** a certification. Mapping onto GOST R 72515-2026 (ISO/IEC 12792:2025) is **not** a conformity declaration.
26. Attributed TechLab **selection** weights (K1=40 / prize floor 50 / arithmetic **mean**) are **not** a predicted AeroBIM score. Application roster is the K1 object; oral advisors are not. MinTsifry bill 166424 is **not** in-force law.
27. Regulation Appendix 3 (final criteria) is **not in git**. B1–B5 in the scoring module are an owner briefing, not that appendix. Final aggregation in the order is a **sum**. Pytest and the fixture SLA pin are **not** Partner validation metrics. Empty A1–A8 hours are required until a partner baseline exists. The vitrine heading 07 is **not** Appendix 4 task №6 (commission №7); do not fight the organizer site.
28. The criterion→git evidence map and the national AI GOST stack are **findability**, not a predicted prize-clearing total. Mapping onto GOST R ISO/IEC 42001-2024 is **not** a certified AI management system.
29. i.moscow/pilot (city grant, legal entity, TRL-ish 6) is **not** the TechLab paid-pilot prize. The K1 role-matrix template in git has empty person cells; the scored roster is the i.moscow application.
30. Ten named people are **not** required for K1 (LETI: 1–10; two competency classes). GOST R 58048 self-assessment is **TRL 4 (lab)**, not TRL 5 and not an independent readiness exam. System A K3 is partner-fit, **not** System B B2 metrics.
31. Russian BIM TAM (GidMarket 10.1 bn RUB, 2022) is **not** AeroBIM SAM. A published analog −72.1% labor cut is **not** our effect. PNST 841-2023 mapping is **not** a SQuaRE certificate. Another MIK product’s «≥500M market» packaging is **not** this TechLab K4.
32. The 16+36.6=52.6 band identity is **not** a predicted AeroBIM total. The public task-page sponsor quote is **not** the attested commission chair. SPbPU 25.1 bn RUB by 2030 is **not** our revenue. The i.moscow paste file is **not** a scored roster.
33. Partner 1H2026 IFRS (revenue −31 %, loss 22.3 bn RUB) is **context**, not an AeroBIM saving. Stand-alone RAS +31 % revenue is **not** group IFRS. K4 does **not** ask CAPEX.
34. Four catalog cards are **not** all applicants. Neighbor-task «46 teams» is a different Partner. Peer catalog claims (15 pilots, 600+ norms, live customer prototype) are **not** audited public fact.
35. Publishable CI counts come only from `docs/evidence/runtime-baseline-latest.json`. Historical blocker-file figures (SHA `019962141606`) are a prior pin, not the current SSOT.
36. Native DWG/RVT/NWD are **not implemented**. Default IFC **SPF** cap stays **256 MiB**. 1.5 GB is ingest + RocksDB analyze, not SPF RAM and not WASM. Experiment B KR headline is **≈16.7 %** (4/24); **≈8.3 %** is the Task-3 waypoint, not the current detected share.

## Reproducibility baseline

```bash
cd backend
python -m venv .venv-pilot
source .venv-pilot/bin/activate   # POSIX
.venv-pilot\Scripts\activate      # Windows
pip install -e ".[dev,raster]"
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
python -m aerobim.tools.evaluate_detection_precision \
  --labels ../samples/benchmarks/detection-precision/labels-synthetic.json \
  --detections ../samples/benchmarks/detection-precision/detections-synthetic.json \
  --min-precision 0.6 --min-recall 0.6 --min-f1 0.6
python -m aerobim.tools.export_runtime_baseline --run-gates --require-clean-tree --require-complete
```

Use an **isolated** virtual environment under `AeroBIM/backend/.venv-pilot`, not the monorepo root `.venv`.

## Sync surfaces

Keep aligned with:

- [partners/TECHLAB_SAMOLET_APPLICATION_2026.md](partners/TECHLAB_SAMOLET_APPLICATION_2026.md)
- [README.md](../README.md) Scientific Reporting Standard section
- [roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md](capability-claim-matrix-2026.md)
- roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md
- [capability-claim-matrix-2026.md](capability-claim-matrix-2026.md)
- [architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md](architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) — architecture SSOT
- [architecture/ADR-001-verdict-ownership-2026.md](architecture/ADR-001-verdict-ownership-2026.md) — `summary.passed` ownership
- [../audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md](../audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md) — Hybrid AI routing foundation (P0/P1, verdict-neutral)
- [../samples/benchmarks/detection-precision/](../samples/benchmarks/detection-precision/) — precision harness fixtures
- [../audit/reports/CLAIMS_LOCK_2026_07_17.md](../audit/reports/CLAIMS_LOCK_2026_07_17.md) — allowed / forbidden wording
- [../audit/reports/CLAIMS_LOCK_2026_07_31.md](../audit/reports/CLAIMS_LOCK_2026_07_31.md) — eng freeze
