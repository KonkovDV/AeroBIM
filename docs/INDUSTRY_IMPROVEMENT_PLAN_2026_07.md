# AeroBIM — Industry-Grade Improvement Plan (July 2026)

**Status:** active — **W0–W2 complete**; **W3 largely landed**; **TZ Response Pack + P0 landed 2026-07-10**; **P1 engineering scaffolds landed 2026-07-10** (norm packs, section pairing, precision harness, ≥20 typical patterns). Next: customer corpus / approved pack / MEP intake.  
**Version:** 2.4.0  
**Date:** 2026-07-10  
**Horizon:** H2 2026 → H1 2027  
**Inputs:** deep audit [`ACADEMIC_DEEP_AUDIT_2026_07_10.md`](evidence/ACADEMIC_DEEP_AUDIT_2026_07_10.md), fact-check [`FULL_AUDIT_FACTCHECK_2026_07_10.md`](evidence/FULL_AUDIT_FACTCHECK_2026_07_10.md), prior roadmap [`13-academic-execution-plan-2026.md`](13-academic-execution-plan-2026.md), external standards & analogs (July 2026)

---

## 1. Executive thesis

AeroBIM already occupies a **defensible niche** that Solibri / BIMcollab / Speckle do not fully cover: **cross-modal, deterministic validation** (IFC + IDS + specs + calcs + drawings) with provenance and open export. Industry leadership in 2026–2027 is not “more AI”; it is:

1. **Validator soundness** — never report PASS when a required capability failed silently.  
2. **openBIM conformance** — IDS 1.0 + IFC schema gate + BCF file/API path aligned with buildingSMART.  
3. **ISO 19650-aligned acceptance criteria** — machine-readable requirements → automated gate before “Published”.  
4. **Deployment integrity** — fail-closed auth, storage jail, size limits, durable jobs.  
5. **Honest claim boundaries** — publish only what is implemented and measured.

This plan reorders work around those five pillars, grounded in July 2026 external evidence and the live defect register.

---

## 2. External evidence base (July 2026)

### 2.1 Standards & official services

| Source | Relevance to AeroBIM | Implication |
|--------|----------------------|-------------|
| **IDS 1.0** (buildingSMART final, Jun 2024); feedback for **1.1 / 2.0** | Primary alphanumeric requirement language | Stay on IDS 1.0 as SSOT; track 1.1; add **IDS file audit** (IDS Audit Tool class) before model check |
| **buildingSMART IFC Validation Service** | Normative schema/SPF checks; **not** project EIR | Insert as **pre-gate**: schema-valid IFC before IDS/project rules (industry recommended workflow) |
| **BCF file 2.1 / 3.0** + **BCF API 3.0** (OpenCDE Foundation) | Issue transport to Solibri/BIMcollab ecosystems | Keep file export; roadmap **BCF API client** for CDE hubs (post-pilot) |
| **openCDE** (Foundation, Documents, Dictionary APIs) | Enterprise CDE integration | Phase after BCF API; do not invent proprietary issue sync |
| **ISO 19650** (2018 + **2026 DIS revision**) | EIR→**IPR**, machine-readable acceptance criteria, CDE Review/Authorize | Map AeroBIM report to **acceptance-criteria evidence** for CDE quality gates |
| **bSDD** | Classification/property dictionaries | Keep pilot mapper; deepen for LOIN/classification checks |

### 2.2 Academic & practice literature (selected)

| Work / theme | Finding | AeroBIM action |
|--------------|---------|----------------|
| W78 2024 — ACC with IDS (accessibility / NBR 9050) | IDS succeeds for alphanumeric rules; **geometry/topology need extensions** | Do **not** overclaim code-compliance; keep clash/geometry as **separate capability** with explicit status |
| MEP openings + IDS + spatial reasoning (2025) | IDS as pull filter + geometry pipeline | Cross-modal path is research-aligned; document modality boundaries |
| Industry practice (ACCA / Solibri blogs) | IDS ≠ clash detection; combine both | Align product messaging + `capabilities` payload |
| ISO 19650 major-project commentary (2026) | Machine-readable acceptance criteria essential at scale | Treat AeroBIM as **acceptance-criteria engine**, not “AI checker” |

### 2.3 Analog / competitor positioning (2026)

| Product | Strength | Gap vs AeroBIM opportunity |
|---------|----------|----------------------------|
| **Solibri** (Office / CheckPoint) | Gold-standard rule-based IFC QA + clash + IDS rule + BCF live | Proprietary; weak **cross-document** (PDF/spec/calc/drawing) fusion |
| **BIMcollab** (Zoom + Nexus) | Issue hub, Smart Issues, BCF sync, clash in viewer | Coordination-first; not multimodal requirement fusion |
| **Speckle** | Object-level data platform, automation | Not a compliance/IDS validator |
| **bSI Validation Service** | Free IFC schema conformity | Explicitly **not** project-specific rules |
| **IfcOpenShell / IfcTester / IfcClash** | Open toolchain AeroBIM already uses | Need production wrapping (auth, soundness, CDE) |

**Differentiation statement (use in pilots):**  
> AeroBIM is an **open, multimodal acceptance-criteria engine** for ISO 19650-style information exchanges: it validates IFC against IDS **and** cross-checks specs, calculations, and drawings with full provenance — then exports BCF for Solibri/BIMcollab coordination. It does **not** replace Solibri’s geometric rule depth; it complements it.

---

## 3. Gap map: audit findings → industry requirements

| Industry requirement (2026) | AeroBIM today | Audit IDs | Plan wave |
|-----------------------------|---------------|-----------|-----------|
| Fail-closed production auth | Fail-open if token unset | C1, H1 | **W0** |
| Storage path integrity | Symlink gap | C2 | **W0** |
| Validator soundness (no silent empty clash) | Exception → `[]` | H2, H3 | **W0** |
| Incomplete rules visible | Silent skip | H5, H6 | **W0** |
| Schema-valid IFC pre-gate | Not first-class | — | **W1** |
| IDS file self-audit | Model check only | — | **W1** |
| Clash ↔ pass/fail contract | Decoupled | H3 | **W0–W1** |
| Durable async jobs | In-memory, stuck after restart | H7, M7 | **W1** |
| ConflictKind complete or narrowed | 6 enum / 3 assigned | M1 | **W1** |
| Drawing SI unit parity | Cross-doc only | M3 | **W1** |
| BCF API / OpenCDE | File only | roadmap | **W2** |
| OIDC / multi-tenant | Static bearer | deferred | **W2** |
| Honest README metrics | Stale ports/LOC | M12 | **W0** |
| Frontend CI | Release-only smoke | M11 | **W1** |

---

## 4. Program structure (waves)

```text
W0  Soundness & Security Hardening     2–3 weeks     BLOCKING for any external pilot claim
W1  openBIM Conformance & Acceptance   4–6 weeks     Industry-parity validator
W2  CDE / Enterprise Integration       6–10 weeks    Solibri/BIMcollab-adjacent ops
W3  Research Differentiation           ongoing       Cross-modal + LOIN + publication
```

Each wave has: **goal**, **deliverables**, **acceptance tests**, **non-goals**, **evidence artifacts**.

---

## 5. Wave 0 — Soundness & Security (P0)

**Goal:** A degraded or misconfigured deployment must **never** look like a successful validation.

### 5.1 Deliverables

| ID | Deliverable | Standard / analog | Done when |
|----|-------------|-------------------|-----------|
| W0.1 | Auth fail-closed outside `development`; docker-compose requires token | OWASP API1 Broken Object Level / fail-secure defaults | Non-dev without token → refuse start or 401 on all `/v1/*` |
| W0.2 | Frontend Bearer (`VITE_AEROBIM_API_BEARER_TOKEN`) | Solibri/BIMcollab always authenticated hubs | UI works with secured API |
| W0.3 | Reject symlinks in `_resolve_safe_path` + ObjectStore | Path-jail best practice | Symlink fixture test fails closed |
| W0.4 | `Report.capabilities` object: `{clash, ids, ifc_schema, raster, …} ∈ {ok,skipped,failed}` + reason | ACCA/Solibri: separate info vs geometry; bSI: schema vs project | Clash engine failure ≠ empty list |
| W0.5 | Incomplete IFC rules → WARNING/ERROR (never silent `continue`) | IDS facet completeness | Test: rule without property_name fails visibly |
| W0.6 | Unit-scale failure → capability warning, not silent `1.0` | UCUM / ISO 80000 honesty | Numeric compare gated when scales missing |
| W0.7 | Clash policy: `AEROBIM_CLASH_AFFECTS_PASS=true\|false` (default documented) | Solibri: clash is first-class QA | Contract test for both modes |
| W0.8 | README / claim-boundary refresh (ports, LOC, ConflictKind subset, raster split) | Pilot claim boundary discipline | Diff reviewed against audit |
| W0.9 | IFC size limit (e.g. 256 MB aligned with bSI Validation Service) + reject | bSI Validation Service limit | Large upload returns 413 |

### 5.2 Non-goals (W0)

- OIDC, BCF API, Redis queues  
- New geometric rule language  
- LLM/VLM in sign-off path  

### 5.3 Evidence pack

- New tests: auth matrix, symlink, capabilities, incomplete rules  
- Updated `pilot-claim-boundary-2026.md`  
- Security note in `SECURITY.md` + `ops/environment-matrix.md`

---

## 6. Wave 1 — openBIM Conformance & Acceptance Criteria

**Goal:** Match the **industry-recommended validation stack**: schema → IDS → project multimodal → BCF.

### 6.1 Pipeline (target architecture)

```text
IFC file
  │
  ├─① SPF / schema / implementer agreements   (bSI Validation Service class)
  ├─② IDS document audit                      (IDS Audit Tool class)
  ├─③ IDS model validation                    (IfcTester — existing)
  ├─④ Multimodal cross-doc + drawings         (AeroBIM differentiator)
  ├─⑤ Clash / clearance (optional capability) (IfcClash — soundness-wrapped)
  └─⑥ BCF 2.1/3.0 export + report evidence    (existing + hardened)
```

### 6.2 Deliverables

| ID | Deliverable | Rationale |
|----|-------------|-----------|
| W1.1 | Optional `IfcSchemaValidator` port (or adapter wrapping open validation rules / IfcOpenShell schema checks) | bSI: schema gate **before** project rules |
| W1.2 | `IdsDocumentAuditor` — validate `.ids` against XSD + facet constraints before run | IDS Audit Tool pattern; fail early on bad EIR/IDS |
| W1.3 | Implement or **delete** unused `ConflictKind` values (`STAGE`, `VERSION`, `SOFT`); wire stage/revision from ISO 19650-lite fields | Honest taxonomy |
| W1.4 | Drawing validation uses same SI/`QuantityValue` path as cross-doc | Unit parity |
| W1.5 | Durable job store (Postgres or Redis) + CAS `QUEUED→RUNNING→DONE`; startup replay | Enterprise async |
| W1.6 | Replace `asyncio.run` in Postgres adapter; TTL deletes index rows | Enterprise storage integrity |
| W1.7 | S3: fail bootstrap in production on misconfig (no silent local fallback) | Multi-instance safety |
| W1.8 | WebP in drawing assets; sanitize `Content-Disposition` | Preview + header safety |
| W1.9 | Frontend unit/smoke in CI **or** explicit “release-readiness only” badge in README | Quality gate honesty |
| W1.10 | DI token for `ExternalEvidenceVerifier`; presentation export via application ports | Architecture hygiene |

### 6.3 Acceptance criteria (Wave 1)

- Benchmark packs still green; F1 ≥ 0.70  
- New schema/IDS-audit fixtures in CI  
- Zero silent clash/rule-skip paths under forced failure injection tests  
- Claim boundary updated: “schema pre-gate available”

### 6.4 Non-goals

- Full Solibri-class geometric rule DSL  
- Full OpenCDE Documents API  

---

## 7. Wave 2 — CDE / Enterprise Integration

**Goal:** Sit next to Solibri/BIMcollab in real project ops without becoming a proprietary CDE.

| ID | Deliverable | Analog |
|----|-------------|--------|
| W2.1 | **BCF API 3.0 client** (push topics to BIMcollab/Solibri hubs) via OpenCDE Foundation auth patterns | BIMcollab live connector class |
| W2.2 | OIDC / JWT (replace static bearer for multi-user) | Enterprise SSO |
| W2.3 | arq/Redis (or equivalent) job workers; horizontal scale | Solibri Autorun / scheduled checks |
| W2.4 | Report ↔ ISO 19650 container metadata (status: Work in Progress / Shared / Published) | CDE workflow states |
| W2.5 | Optional hook: submit IFC to bSI Validation Service API **or** local schema pack; store certificate/result ID | Industry pre-gate |
| W2.6 | Postgres-backed `list_reports` filters (true enterprise index) | Close write-only gap |
| W2.7 | Revit thin client: export package + open report deep link (not full authoring) | Solibri Inside-lite |

### Non-goals

- Replacing ACC/Procore/CDE products  
- Claiming ISO 19650 certification of the org  

---

## 8. Wave 3 — Research differentiation (ongoing)

**Goal:** Publishable, reproducible advantage in **cross-modal** acceptance checking.

| ID | Theme | Academic anchor |
|----|-------|-----------------|
| W3.1 | Expand RU + EN annotated corpora; inter-annotator agreement protocol | Extraction F1 + Cohen’s κ |
| W3.2 | LOIN-aware requirement levels (geometry vs alphanumerics) | ISO 7817 / LOIN practice |
| W3.3 | Hybrid: IDS alphanumeric + explicit spatial predicates (openings, clearances) as **separate** modules | W78 IDS limits; MEP openings paper |
| W3.4 | Ablation studies already started → paper-ready tables | `run_ablation_study` |
| W3.5 | Human-in-the-loop review UX metrics (time-to-triage, remark acceptance) | Pilot KPI protocol |
| W3.6 | Optional LLM **assist** for IDS drafting only — **never** in sign-off path without HITL | 2025–26 LLM+IDS research; keep claim boundary |

---

## 9. Quality system (industry bar)

### 9.1 Definition of Done (every PR)

```text
ruff format/check + mypy + pytest
capability-failure injection tests for touched validators
claim-boundary check if README/docs change
openapi export if API change
```

### 9.2 Release readiness (existing workflow + additions)

| Gate | Mode |
|------|------|
| Benchmark thresholds | advisory → enforced for tagged releases |
| Extraction F1 ≥ 0.70 | enforced |
| Live review smoke | enforced for pilot tags |
| Auth fail-closed smoke | **new** enforced for `prod` compose profile |
| Schema/IDS-audit smoke | **new** after W1 |

### 9.3 Evidence & FAIR

- Keep `REPRODUCIBILITY-2026.md` as SSOT  
- Every pilot claim cites: pack path, CLI flags, artifact hash, commit SHA  
- No performance numbers without environment matrix  

---

## 10. Risk register

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Overclaiming “code compliance” | High | Claim boundary: decision-support; IDS alphanumeric + optional clash |
| Solibri comparison trap | High | Position as **complement**, not replacement |
| IDS 1.1 breaking changes | Medium | Abstract IdsValidator; pin 1.0 fixtures |
| ISO 19650 2026 terminology churn (EIR→IPR) | Medium | Use dual labels in UI/docs during transition |
| Async/job complexity delay | Medium | W0 without Redis; W1 minimal durable store |
| OCR false positives in drawings | Medium | Keep deterministic path; confidence + HITL |

---

## 11. Suggested calendar (indicative)

| Window | Focus |
|--------|-------|
| **Jul–Aug 2026** | Wave 0 complete; pilot VM with fail-closed auth |
| **Sep–Oct 2026** | Wave 1 schema/IDS-audit + ConflictKind honesty + durable jobs |
| **Nov 2026–Jan 2027** | Wave 2 BCF API pilot with one CDE/issue hub |
| **Ongoing** | Wave 3 corpus + publication evidence |

---

## 12. Success metrics

| Metric | Baseline (Jul 2026) | Target (post-W1) |
|--------|---------------------|------------------|
| Silent capability failures | Present (clash/rules) | **0** in CI failure-injection suite |
| Auth default (non-dev) | Fail-open | Fail-closed |
| Extraction macro F1 | ≈ 0.86 | ≥ 0.70 gate; track ≥ 0.85 |
| ConflictKind honesty | 3/6 live | 100% of advertised kinds implemented **or** docs narrowed |
| BCF interoperability | File 2.1/3.0 | File + **one** live BCF API push (W2) |
| Pilot claim audit findings (CRITICAL) | 2 | **0** |

---

## 13. Immediate next actions (this week)

1. Close **customer blockers** after P1/A1–A5 scaffolds: approved residential pack, real PD↔RD pair, adjudicated precision corpus — see [`tz/TZ_COMPLIANCE_MATRIX_2026.md`](tz/TZ_COMPLIANCE_MATRIX_2026.md).  
2. Re-run TechLab demo gate before each pitch: `python -m aerobim.tools.run_demo_path` ([`ops/demo-path-runbook-2026.md`](ops/demo-path-runbook-2026.md); A5 landed).  
3. Fill dual-annotator IAA worksheets to κ ≥ 0.80 on new EN/RU spans (**W3.1**).  
4. Optional English narrative patterns (beyond structured-text) for bilingual F1.  
5. Pilot one live bSI Validation Service submit when credentials available.  
6. Cite [`docs/evidence/ablation-study-paper-table-2026.md`](evidence/ablation-study-paper-table-2026.md) in publication drafts.

---

## 14. TZ MVP preparation (expert assistant)

The customer TZ (OCR/CV/NLP/BIM co-pilot) is the same class as Samolet TechLab #07.

| Artifact | Role |
|----------|------|
| [`tz/README.md`](tz/README.md) | Response pack index |
| [`tz/TZ_COMPLIANCE_MATRIX_2026.md`](tz/TZ_COMPLIANCE_MATRIX_2026.md) | Requirement → status → phase |
| [`tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md) | Architecture TBD fill |
| [`tz/TZ_BUILD_AND_QUALITY_2026.md`](tz/TZ_BUILD_AND_QUALITY_2026.md) | Build TBD fill |
| [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) | R1–R15 companion |
| [`samples/tz-appendix/`](../samples/tz-appendix/) | Data appendices skeleton |

**MVP posture:** deterministic sign-off path; CV/LLM/DWG = Phase 2 advisory. KPI «>90%» is aspirational until adjudication — see [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md).

| Phase | Focus |
|-------|-------|
| P0 | Upload + remarks UI + EN templates |
| P1 | Norm packs, section pairing, precision harness |
| P2 | DXF/DWG thin + OCR deepen + CV advisory |
| P3 | LLM assist advisory + HITL |
| P4 | Customer corpus → publish precision |

---

## 15. References (external)

1. buildingSMART — IDS: https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/  
2. buildingSMART — IFC Validation Service: https://technical.buildingsmart.org/services/validation-service/  
3. buildingSMART — IDS Audit Tool: https://github.com/buildingsmart/ids-audit-tool  
4. buildingSMART — BCF API 3.0 / OpenCDE Foundation: https://github.com/BuildingSMART/BCF-API  
5. W78 2024 — Automated compliance checking using IDS (accessibility use case): https://itc.scix.net/pdfs/w78-2024-paper_21.pdf  
6. MEP openings + IDS + spatial reasoning (2025): https://d-nb.info/1386241806/34  
7. Solibri — IDS + data validation vs clash: https://www.solibri.com/solutions/bim-quality-assurance/data-validation  
8. BIMcollab — clash + BCF issue management: https://www.bimcollab.com/en/clash-detection-in-bim/  
9. UK BIM Framework — developing information requirements (ISO 19650): https://www.ukbimframework.org/  
10. ISO 19650 2026 revision commentary (machine-readable acceptance criteria): Digital Construction Plus / industry DIS notes  

---

## 16. Relationship to prior AeroBIM plans

| Document | Role after this plan |
|----------|----------------------|
| `13-academic-execution-plan-2026.md` | Historical A/B/C iterations; many ✅ — **keep**; hygiene gaps superseded by **W0/W1 here** |
| `pilot-claim-boundary-2026.md` | Still SSOT for what may be claimed — **update after W0** |
| `ACADEMIC_DEEP_AUDIT_2026_07_10.md` | Defect register feeding this plan |
| This document | **Industry-grade delivery plan (July 2026)** |

## Drawing AI posture

See [evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
