# CRITICAL BLOCKERS — Samolet Checkpoint

**Operational freeze SHA (historical, 2026-07-21):** `f2615e7` (eng F–L: precision gates, SLA claim gate, BCF ladder, revision compare, threat model, open-core ADR). Do **not** treat this SHA as HEAD or as the publishable metrics pin. Refresh when claiming metrics — current publishable counts are [`docs/evidence/runtime-baseline-latest.json`](../../docs/evidence/runtime-baseline-latest.json) (`attested_by=ci`, commit `90a809351ca4c2c4999f781b6f34092551fa0aef`, 2026-08-28T05:51:14Z): backend **2639** passed / **2658** collected / 19 skipped / 0 failed; frontend **57**.  
**Historical Red Team freeze:** `c0c4b2b` / `8efbef8` — see `CLAIMS_LOCK_2026_07_17.md` (pre-remediation narrative; do not treat defect prose below CLOSED tables as current).  
Severity key: BLOCKER / CRITICAL / HIGH / MEDIUM / LOW.

**Checkpoint verdict:** still **`NO_GO`**. Engineering remediations do **not** close customer sign-off. Remaining honest gaps: **RT-001** (no public «RF PD + expertise conclusion» pairs; rules exist), **RT-002a** CLOSED regulatory (public MOEXP/AGR/SPb IDS + `pack_hash`, city as publisher) / **RT-002b** OPEN (no Samolet-signed profile), **RT-003** (public duplex IfcClash RUN; `mep_system_clash` NOT_VERIFIED; not MEP delivered). Never write undifferentiated «RT-002 CLOSED». Do not write «нет утверждённого нормативного пакета».

**Reclassification (v4):** N-18 CLOSED 2026-08-09 (attestation cannot be forged locally). Current engineering surface: [`docs/capability-claim-matrix-2026.md`](../../docs/capability-claim-matrix-2026.md).

## Open engineering/legal blockers (2026-07-31 audit)

| ID | Severity | Status | Summary |
|---|---|---|---|
| N-18 | **P0** | **CLOSED 2026-08-09** (WP-A1b) | CLI `--attested-by ci` allowed local forgery of publishability. Fix: attestation derived only from `GITHUB_ACTIONS` env; flag removed; `test_attestation_cannot_be_forged_locally`. |

| ID | Severity | Status | Summary |
|---|---|---|---|
| LIC-001 | HIGH | **ENGINEERING_CLEARED_FOR_CORE_PDF** (Option B owner-selected 2026-07-31) | Production PDF path: `pypdfium2` + `pdfminer.six` (+ Pillow). PyMuPDF optional `pdf-agpl` only; absent from runtime lock/Docker. Residual: do not reintroduce AGPL into runtime without owner decision; not a court opinion. Gate: `test_dependency_license_gate.py` + `test_pdfium_region_cropper.py`. |

## Engineering readiness improved (2026-07-21 F–L)

| Track | Eng status | Customer evidence |
|---|---|---|
| P2-04 Annotation↔IFC | **ENG_DONE** (claimed GUID presence vs spatial index; not adjudicated) | RT-001 **OPEN** |
| F Precision publishable gates | Hardened (held-out + FN + κ/α) | RT-001 **OPEN** |
| G ≤30 min SLA claim gate | Schema 1.3.0 refuse without pack/machine/caps | Customer SLA **OPEN** |
| H BCF T0–T4 | Ladder formalized; T2 template empty | RT-008 T2 **NOT_VERIFIED** |
| I Revision finding compare | Domain + export helper | No customer revision packs |
| J HITL | **DONE** (skipped further UX) | — |
| K Threat model | Doc + inventory tests | POST-05 residual |
| L Open-core ADR | ADR-002 proposed | LICENSE unchanged (MIT) |

## Closed in RTATOM Wave A1 + A2 (2026-07-20)

| ID | Status | Notes |
|---|---|---|
| RTATOM-H01 | **CLOSED** | FS IFC/drawing tenant prefix assert |
| RTATOM-I05 | **CLOSED** | `safe_storage_token` collision-resistant encoding |
| RTATOM-G01/D02 | **CLOSED** | Hard clash flip from `policy.clash_affects_pass` only |
| RTATOM-H04/I06 | **CLOSED** | HITL `previous_state` SSOT from event store |
| RTATOM-H05/I07 | **CLOSED** | Norm-pack `proposed_by` bound to principal |
| RTATOM-G04 | **CLOSED** | Evidence HTML uses enforced pass |
| RTATOM-G11 | **CLOSED** | Report content hash verify on get |
| RTATOM-I01 | **CLOSED** | S3 endpoint re-assert |
| RTATOM-I02 | **CLOSED** | Quota corrupt fail-closed |
| RTATOM-I03 | **CLOSED** | PDF thread timeout |
| RTATOM-I04 | **CLOSED** | `:` reject in uploads |
| RTATOM-G03 | **CLOSED** | Cancel discard/tombstone |
| RTATOM-H02/H03 | **CLOSED** | List reports tenant-scoped even under soft ACL-off |
| RTATOM-G02/G05/G07/G08 | **PARTIAL** | Soft `authoritative=false`; hard cross-doc ERROR + openrebar enforced |
| RTATOM-I09/I10/I11/I14/I20 | **PARTIAL** | Datastore URL SSRF; quota release; BCF `inspect_zip`; baked pilot quotas; PG fail-closed |
| RTATOM-F02/F05/F07 | **PARTIAL** | Client bearer inject removed; preview Blob MIME allowlist; WASM IFC 256 MiB |
| RTATOM A2.5 / RT-POST-09 hashes | **CLOSED*** | `--require-hashes` + `--generate-hashes` locks; CI/Docker wire-up; pinned `pip==25.2` / `uv==0.8.22`. *Residual: unhashed pip/uv bootstrap wheels. |
| RTATOM A3 hygiene | **PARTIAL→A3 CLOSED*** | CSP/nosniff/Referrer/XFO; NFKC tokens; JWKS↔issuer host bind; ZIP stream inspect; `open_storage_file` on report JSON + IFC/drawing FileResponse re-jail; **ElementTree caps** (`xml_limits` + defusedxml); **S3/Local stream get caps** (`max_get_bytes`). *Residual: production OIDC BFF remains **DESIGNED / NOT_IMPLEMENTED**; Phase 3 is lab-only (`oidc_bff_phase3_ready`). |

Still open for checkpoint: remaining RT-001 (RF corpus), RT-002 (Samolet profile), RT-003 (unmeasured federated MEP). Residual: production OIDC BFF (**DESIGNED / NOT_IMPLEMENTED**; Phase 3 lab path landed — default still 501 / `auth_bff=NOT_IMPLEMENTED`). Eng surface: [`docs/capability-claim-matrix-2026.md`](../../docs/capability-claim-matrix-2026.md).

## Closed in post-remediation wave (2026-07-19)

| ID | Status | Evidence |
|---|---|---|
| RT-POST-01 | **CLOSED** | Non-dev `AEROBIM_ENV` → default `signoff_profile=production`; Docker/compose bake; soft clash flags ignored under pilot/production |
| RT-POST-02 | **CLOSED** | Cross-tenant ACL → **404** (not 403); `tests/test_rt_remediation_post.py` + ACL suite |
| RT-POST-03 | **CLOSED** | `outbound_url.py` SSRF guard on JWKS / bSI / OpenCDE |
| RT-POST-04 | **CLOSED** | OIDC tenant only from `AEROBIM_OIDC_TENANT_CLAIM` (default `tenant_id`) |
| RT-POST-06/07 | **CLOSED** | Pilot/production: `unit_scale` default NOT_VERIFIED; SKIPPED calc/qty block pass |
| RT-POST-08 | **CLOSED** | Upload response omits `object_key` |
| RT-POST-09 | **CLOSED*** | Actions SHA-pinned; hashed locks (`--generate-hashes`); CI/Docker `--require-hashes`; pinned pip 25.2 + uv 0.8.22; lock drift with hashes. *Residual: floating pip/uv bootstrap before pin. |
| RT-POST-10/11 | **CLOSED** | `html.escape(quote=True)`; ZIP rejects `..` / absolute members |

Still open for checkpoint: remaining RT-001 / RT-002 / RT-003 as rewritten 2026-08-14 (open data vs honest leftover). Residual: production OIDC BFF **DESIGNED / NOT_IMPLEMENTED** (POST-05; Vite loopback inject remains dev-only).

## Closed in remediation commit (2026-07-17)

| ID | Status | Evidence |
|---|---|---|
| RT-004 | **CLOSED** | `require_clash` → SKIPPED clash ⇒ FAILED + `passed=false`; `tests/test_p0_remediation_fail_closed.py` |
| RT-005 | **CLOSED** | `AuthPrincipal` + `principal_may_access_report` on report/IFC/preview/export/review; ACL tests in P0 suite |
| RT-006 | **CLOSED** | `frontend` vitest in main CI (`frontend` job: `npm ci` + `npm test` + `npm run build`) |
| RT-007 | **CLOSED** | `finding_id` / `evidence_refs` / `source_id` stamped + persist reject; provenance helpers |
| RT-013 | **CLOSED** | one-sided empty revision ⇒ conflict; drawings in identity collection |
| RT-014 | **CLOSED** | raster requested+analyzer+zero annotations ⇒ FAILED; bSI ERROR under `require_bsi_schema` |
| RT-015 | **CLOSED** | Postgres→FS fallback only in `dev`; non-dev re-raises |
| RT-009 | **CLOSED** | this remediation commit freezes prior dirty seams + P0 |

Still open for checkpoint: **RT-001, RT-002, RT-003** (customer/MEP blocked).  
Evidence wave (2026-07-17): RT-008 **PARTIAL** (structural T1); RT-010/011/012 honesty closed for fixture/API surface; CDE import + customer SLA still open.  
Architecture SSOT: `docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md` · ADR-001 verdict ownership.

## Closed in evidence wave (2026-07-17)

| ID | Status | Evidence |
|---|---|---|
| RT-008 | **PARTIAL** | T1 structural evidenced; T0–T4 ladder formalized; `cde_import=NOT_VERIFIED` |
| RT-010 | **CLOSED** | `claim_labels` on reinforcement-digest + `calculation_correctness=NOT_IMPLEMENTED` |
| RT-011 | **CLOSED** | `GET /v1/system/capabilities` + ReportCapabilities honesty fields |
| RT-012 | **CLOSED** (fixture honesty) | schema 1.3.0 claim gate in `measure_package_sla`; customer SLA still НЕ ДОКАЗАНО |

---

## Historical defect narratives (archived)

> **Authority:** CLOSED tables above are authoritative. Sections below preserve pre-fix reproduction notes for audit trail only. **Do not treat “BLOCKER” / “CRITICAL” headings in this archive as open items** unless the ID is listed under “Still open for checkpoint” and absent from CLOSED tables.

---

### RT-001 — Customer accuracy / RF expertise corpus not evidenced
- **Severity:** BLOCKER  
- **Category:** Claims / Evaluation  
- **Rewritten 2026-08-14:** three public corpora were available and unused for a product false-pass number: AEC-Bench ([arXiv:2603.29199](https://arxiv.org/abs/2603.29199), Apache 2.0), IFC-Bench V2 (TUM GNI, CC BY 4.0), GNI BIM Dataset ([Zenodo 10.5281/zenodo.19722012](https://doi.org/10.5281/zenodo.19722012), CC BY 4.0). Attribution: [`docs/DATASETS.md`](../../docs/DATASETS.md). GPLv3 IFC from IFC-Bench stays **out** of this MIT tree.  
- **Still true:** there is **no** public corpus «российский комплект ПД + фактическое заключение экспертизы». Fixture F1 is not product accuracy. Historical engineering note (2026-07 / rewritten 2026-08-14): «656 pytest ≠ false-pass rate» ([arXiv:2607.29058](https://arxiv.org/abs/2607.29058)) — that count is **not** the current CI pin. Publishable backend tests_passed on the runtime baseline is **2639** (`90a809351ca4`, 28.08.2026, `attested_by=ci`). MinStroy XSD **01.07 / 01.01** plus survey-assignment / geological-report **01.00** are vendored (zip folders for PZ/ZnP still `dev_`); that is intake format, not a remark corpus. Construction-stage XSDs from the 07.08.2026 news were **not** on the 14.08 catalog scrape.  
- **Expected before any product accuracy claim:** customer or RF-expertise corpus + ≥2 adjudicators + κ/α + held-out + FN tracked  
- **Product HOLD — RT-001 still OPEN** for that RF/customer corpus only. Open benches ≠ RT-001 closed.
- **Addendum 25.08.2026:** customer indicated a private data channel. That is not a hashed pack in git. `customer_package_in_samples_customer` stays false. RT-001 stays OPEN.

### RT-002 — Samolet-signed acceptance profile absent (public examination IDS exist)
- **Severity:** BLOCKER (customer sign-off)  
- **Category:** Norms  
- **«Нет утверждённого нормативного пакета» is false.** GAU MO «Мособлгосэкспертиза» published IDS + IFC4 mappings on [TIM / BIM](https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/). Also public: Москомэкспертиза МКЭ-ОД/19-39 (ред. 10.10.2024), МКЭ-ОД/24-178 (25.12.2024), Moscow AGR CIM requirements, Glavgosexpertiza IM recommendations, «Требования к ИМ ОКС, Часть 1» ред. 4.0 (clash-absence section), SPb CGE element→IFC tables, СП 333 / 331, ГОСТ Р 10.*, ПНСТ 909-2024. Pack + engine coverage: `samples/ids/moexp/` · [`docs/evidence/norm-pack-moexp-coverage-2026-08.md`](../../docs/evidence/norm-pack-moexp-coverage-2026-08.md).  
- **Still true (two different deficits):** no Samolet **model corpus**, and no Samolet-signed `customer_approved` acceptance profile (`approval` object + `pack_hash` + jurisdiction + per-rule clause).  
- **Addendum 24.08.2026 10:45:** measurement profile = public examination IDS (RT-002a, city/MOEXP as publisher). Samolet signature is “deployed at the customer” (RT-002b), not “measured against live norms”. `closes_rt002` (customer) stays **false**. Do not unfreeze the CUT `moscow_agr` DI port.
- **Product HOLD — RT-002 still OPEN as a customer blocker** until signed Samolet profile. Public MOEXP IDS do not invent Samolet evidence.
- **Addendum 24.08.2026 (SPb GAU CGE profile):** `samples/profiles/spb-cge/` indexes the published CGE IDS 1.0 pack (`samples/ids/spbexp/`). Provenance `OFFICIAL_PUBLISHED`. `signed_by_customer=false`. Does **not** close RT-001 or RT-002 (RT-002b remains Samolet-signed acceptance). Fail-closed load; not an expertise verdict.

### RT-003 — Federated MEP not measured (public models exist)
- **Severity:** BLOCKER (if claimed) / CRITICAL (gap honesty)  
- **Category:** MEP / Clash  
- **Rewritten 2026-08-14:** multidisciplinary IFC is public in IFC-Bench V2 (`west_riverside_hospital` CC BY 3.0; `sixty5` / `dental_clinic` / `duplex` / `wbdg_office` CC BY 4.0; `digital_hub` MIT). IfcClash is an optional extra. OSArch: naive 7-discipline federation ~44k elements can OOM (~30 GB); bbox pre-broadphase is required before quoting runtime. Fixture «~0.5 s» must not go to the tracker as product SLA.
- **Inventory (not clash):** hashed entity counts on duplex/mep + HVAC fixture + Digital Hub + West Riverside IFC4 — [`docs/evidence/federated-mep-inventory-2026-08.md`](../../docs/evidence/federated-mep-inventory-2026-08.md) · `content_sha256=d875af14f1f177ac27d64fd12ac9d700b635190ca9b2c80e8971ab017ec54c0b`.
- **Geometric clash (not MEP delivered):** planted federated IfcClash (walls; IfcPipeSegment vs IfcWall) under `docs/evidence/federated-clash-planted-2026-08.json`. Public IFC-Bench duplex ARC vs MEP IfcClash **RUN, 837 hits** under `docs/evidence/federated-clash-duplex-2026-08.json`. Clearance extra-method rehearsal on `clash-clearance-gap-{a,b}.ifc` (HVAC fixture unused: no tessellated geometry). Clash→our BCF export is **file ingest** (`cde_import=NOT_VERIFIED`). Engine rehearsal, **not** customer federated IFC, **not** signed scope, **not** coordinator BCF gold. `closes_rt003` stays false.
- **Still true:** `UnconfiguredMepSystemGraphProvider` stays `NOT_VERIFIED`. Synthetic stub is never OK.
- **Normative hook:** «Требования к отсутствию коллизий» in digital building-model requirements ed. 4.0.
- **Product HOLD — RT-003 still OPEN** until customer federated IFC + signed scope + verified geometry. Inventory, planted clash, and public duplex clash ≠ delivered.  

### RT-004 — Clash SKIPPED does not block pass
- **СТАТУС: ЗАКРЫТО (remediation 2026-07-17)** — `require_clash` → SKIPPED clash ⇒ FAILED + `passed=false`  
 
- **Severity (historical defect prose below):** CRITICAL — do not treat as open  
- **Category:** Capability honesty / False pass risk  
- **Exact file:** `application/use_cases/analyze_project_package.py::_run_clash_detection`, `application/services/signoff_policy.py`  
- **Observed (pre-fix):** missing optional clash stack → `CapabilityState.SKIPPED` → empty results → pass allowed  
- **Expected:** For Samolet packages requiring clash, missing engine must be FAILED or explicit policy gate  
- **Reproduction:** run analyze without `ifcclash` installed; inspect `capabilities.clash`  
- **Impact (pre-fix):** Green report without geometric coordination work  
- **Fix applied:** Profile flag `require_clash=true` for pilot packages; SKIPPED→FAILED under that profile  
- **Verification:** `tests/test_p0_remediation_fail_closed.py`  

### RT-005 — No tenant / object isolation
- **СТАТУС: ЗАКРЫТО (remediation 2026-07-17)** — `AuthPrincipal` + `principal_may_access_report`; ACL 404 post-wave  
 
- **Severity (historical defect prose below):** BLOCKER (security) — do not treat as open  
- **Category:** API security  
- **Exact file:** `presentation/http/api.py` (`/v1/reports/{report_id}/source/ifc`, drawing preview, BCF export)  
- **Observed (pre-fix):** Auth is shared bearer/OIDC; authorization is not project/tenant scoped; report UUID knowledge grants artifact access  
- **Expected:** object-level ACL / tenant binding  
- **Reproduction (pre-fix):** authenticate with valid token; GET another report’s IFC by ID  
- **Impact (pre-fix):** data leakage across projects in shared deployment  
- **Fix applied:** bind reports to tenant/project; authorize before artifact fetch; cross-tenant → 404  
- **Verification:** ACL suite + `tests/test_rt_remediation_post.py`  

### RT-006 — Frontend tests failing
- **СТАТУС: ЗАКРЫТО (remediation 2026-07-17)** — frontend vitest in main CI  
 
- **Severity (historical defect prose below):** CRITICAL — do not treat as open  
- **Category:** Reproducibility / Review UX  
- **Exact file:** `frontend/src/App.test.tsx`  
- **Observed (pre-fix):** `npm test` exit 1; 3 failures in review-shell smoke / filters / 2d panel  
- **Expected:** green review shell tests in clean env  
- **Reproduction:** `cd frontend && npm test`  
- **Impact (pre-fix):** HITL review path not proven  
- **Fix applied:** UI contract assertions; CI `frontend` job (`npm ci` + `npm test` + `npm run build`)  
- **Verification:** vitest green in CI (see runtime baseline frontend.tests_passed)  

### RT-007 — Finding contract incomplete vs auditor mandate
- **СТАТУС: ЗАКРЫТО (remediation 2026-07-17)** — `finding_id` / `evidence_refs` / `source_id` stamp + persist reject  
 
- **Severity (historical defect prose below):** CRITICAL — do not treat as open  
- **Category:** Domain contracts / Provenance  
- **Exact file:** `domain/models.py::ValidationIssue`, `domain/architecture.py::EvidenceRef`  
- **Observed (pre-fix):** Missing mandatory `finding_id`, `source_refs`, `evidence_refs`, `capability`, `document_identity` on findings; `EvidenceRef` exists but is not enforced on issues  
- **Expected:** every finding bindable to source+rule+evidence  
- **Impact (pre-fix):** report can lose provenance; weak audit trail for Samolet  
- **Fix applied:** extend ValidationIssue; reject persist without evidence  
- **Verification:** contract / provenance tests  

### RT-008 — BCF interoperability not evidenced beyond unit ZIP
- **СТАТУС: PARTIAL** (T1 structural ZIP evidenced; T2 CDE import **NOT_VERIFIED**)  
- **Severity:** HIGH (CRITICAL if BCF claimed “ready for CDE”)  
- **Category:** Reporting  
- **Exact file:** `infrastructure/adapters/bcf_report_exporter.py`, dirty `bcf_consumers.py`  
- **Observed:** Export ZIP + in-repo dual consumers/tests; **no** saved independent CDE import artifact  
- **Expected:** structural + consumer import evidence under `audit/evidence/`  
- **Impact:** handoff claim fails if marketed as CDE-ready  
- **Fix:** export sample → import in external tool → save screenshot/log hash  
- **Verification:** evidence file referenced from matrix  

### RT-009 — Dirty tree / uncommitted seams treated as shipped
- **СТАТУС: ЗАКРЫТО (remediation freeze 2026-07-17)** — subsequent commits on clean tree  
 
- **Severity (historical defect prose below):** HIGH — do not treat as open  
- **Category:** Release integrity  
- **Exact file:** git status vs SHA `c0c4b2b` (historical)  
- **Observed (pre-fix):** DocumentIdentity extension, revision-merge guard, idempotency, BCF consumers uncommitted  
- **Expected:** checkpoint evaluates committed artifacts only, or explicitly freezes dirty tree  
- **Impact (pre-fix):** false readiness if demo uses local dirty code  
- **Fix applied:** commit atomic slices; re-baseline  
- **Verification:** public `main` CI green; Claims Lock freeze SHAs documented above  

### RT-010 — Independent calculation verification absent
- **СТАТУС: ЗАКРЫТО (honesty surface, 2026-07-17)** — `claim_labels` + `calculation_correctness=NOT_IMPLEMENTED`; независимая проверка calc **по-прежнему НЕ РЕАЛИЗОВАНА** (это не GO по calc).  
- **Severity (historical prose):** HIGH — do not quote as open defect; see CLOSED table above  
- **Category:** Calculation / TZ  
- **Observed:** digest + numeric cross-compare / OpenRebar path  
- **Expected:** separate “correctness verification” only with control formula/solver identity  
- **Allowed wording:** сверка результатов PARTIAL; независимая проверка НЕ РЕАЛИЗОВАНО  

### RT-011 — DWG/DXF / CV human-level missing
- **СТАТУС: ЗАКРЫТО (honesty surface, 2026-07-17)** — capability honesty; native DWG / human-level CV **по-прежнему НЕ РЕАЛИЗОВАНО**.  
- **Severity (historical prose):** HIGH — do not quote as open defect; see CLOSED table above  
- **Category:** 2D  
- **Observed:** documented missing; OCR extra absent in env  
- **Allowed wording:** НЕ РЕАЛИЗОВАНО / ADVISORY_ONLY  

### RT-012 — SLA not published with machine+package evidence
- **СТАТУС: ЗАКРЫТО (fixture honesty + claim gate, 2026-07-17 / 2026-07-21)** — customer SLA ≤30 мин **по-прежнему НЕ ДОКАЗАНО**.  
- **Severity (historical prose):** HIGH — do not quote as open defect; see CLOSED table above  
- **Category:** Performance  
- **Observed:** tool + stage budgets + schema 1.3.0 claim gate (refuse `customer_measurable` without customer corpus + pack_hash + machine_fingerprint + mandatory capabilities); no customer package measurement artifact  
- **Allowed wording:** НЕ ДОКАЗАНО for customer комплект ≤30 мин  
- **Engineering readiness (2026-07-21):** claim gate hardened. **Product HOLD — customer SLA still open.**  

---

### RT-013 — Revision guard incomplete (empty revision / drawings out of scope)
- **СТАТУС: ЗАКРЫТО (remediation 2026-07-17)** — one-sided empty revision ⇒ conflict; drawings in identity collection.  
- **Severity (historical prose):** HIGH — do not quote as open defect; see CLOSED table above  
- **Category:** Document identity  
- **Exact file:** `domain/ingestion.py::revisions_conflict`, `analyze_project_package.py::_collect_identity_sources`  
- **Observed (pre-fix):** Conflict only if **both** revisions non-empty; drawing sources not in identity set  
- **Expected:** AMBIGUOUS / REQUIRES_HITL when revision missing on one side; drawings in identity scope  
- **Evidence:** Architecture layer audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md)  

### RT-014 — Soft empty-success edges (raster OK + empty OCR; bSI WARNING)
- **СТАТУС: ЗАКРЫТО (remediation 2026-07-17)** — raster requested+analyzer+zero annotations ⇒ FAILED; bSI ERROR under `require_bsi_schema`.  
- **Severity (historical prose):** HIGH — do not quote as open defect; see CLOSED table above  
- **Category:** Capability honesty  
- **Exact file:** analyze `_build_capabilities` (raster OK if analyzer configured); `_submit_bsi_validation` WARNING path  
- **Observed (pre-fix):** Empty OCR yield can still look capability-OK; remote schema WARNING may not fail pass  
- **Expected:** Explicit yield/coverage gates; schema pre-gate policy for pilot packages  
- **Evidence:** Architecture layer audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md)  

### RT-015 — Storage fallbacks may hide enterprise misconfig
- **СТАТУС: ЗАКРЫТО (remediation 2026-07-17)** — Postgres→FS fallback only in `dev`; non-dev re-raises.  
- **Severity (historical prose):** HIGH — do not quote as open defect; see CLOSED table above  
- **Category:** Reliability / ops  
- **Exact file:** `infrastructure/di/bootstrap.py::_build_audit_report_store`  
- **Observed (pre-fix):** Postgres init failure always falls back to filesystem (not only in dev); S3/Redis fall back in dev  
- **Expected:** Non-dev fail-closed when configured enterprise store is required  
- **Evidence:** Architecture layer audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md)  

### RT-016 — Published SLA evidence is fixture-microscopic
- **СТАТУС: ЗАКРЫТО (honesty / claim boundary, 2026-07-17)** — fixture SLA не выдаётся за customer; `customer_measurable` refuse-without-evidence. Customer SLA **НЕ ДОКАЗАНО**.  
- **Severity (historical prose):** HIGH — do not quote as open defect; see CLOSED table above  
- **Category:** SLA claims  
- **Exact file:** `docs/evidence/samolet-sla-pilot-moscow-2026-05-21.json`  
- **Observed (pre-honesty framing):** `sla_pass: true` on tiny Moscow fixture (~0.01 min class), not customer комплект  
- **Expected:** Measured SLA only with package hash + sizes + machine + cold/warm  
- **Evidence:** Claims/TZ audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md) · claim boundary: [`../../docs/pilot-claim-boundary-2026.md`](../../docs/pilot-claim-boundary-2026.md)  

### RT-017 — Advisory OFF==ON test is narrow
- **СТАТУС: ЗАКРЫТО (RT-E remediation 2026-07-17)** — real UC path, advisory ON/OFF; deterministic findings + `summary.passed` equality. Does **not** close RT-001/002/003 or flip **NO_GO**.  
- **Severity (historical prose):** MEDIUM — do not quote as open defect; see CLOSED table above  
- **Category:** Contour isolation  
- **Exact file:** `tests/test_architecture_seams.py::test_advisory_off_equals_advisory_on_for_summary_passed`  
- **Observed (pre-fix):** Side-call to IDS-assist stub between empty analyzes; does not toggle real OCR/CV/LLM path inside UC  
- **Expected:** Full report-hash / deterministic-findings equality under advisory feature flags  
- **Evidence:** Claims/TZ audit (session); wording SSOT: [`CLAIMS_LOCK_2026_07_17.md`](CLAIMS_LOCK_2026_07_17.md) · claim boundary: [`../../docs/pilot-claim-boundary-2026.md`](../../docs/pilot-claim-boundary-2026.md)  

---

**Checkpoint rule:** any of RT-001..RT-005 presented as “done” ⇒ automatic **NO_GO**.
