<!-- claims-lint: allow-file reason="Red Team of Wave A fixture substitutes; forbidden phrases as non-claims; Checkpoint NO_GO" -->
---
title: "Red Team — Wave A KT#2 substitutes (2026-08-14 evening)"
status: active
version: "1.0.0"
last_updated: "2026-08-14"
claim_boundary: >
  Internal Red Team of Wave A after the operator lifted the ports/DI freeze.
  Checkpoint remains NO_GO. Does not close RT-001/002/003. Not customer
  accuracy. Not MEP delivered. Not CDE-ready. Not native DWG. Not a
  structural solver. CI tests_passed pin stays 2167. Local Windows pytest
  2259/12/0 is not a README replacement (N-26).
---

# Red Team — Wave A (survey XSD, clearance, IDS audit, SP 63 template)

**Author relationship:** Internal self-assessment  
**Scope:** uncommitted Wave A vs `dd1a0a7` (MinStroy survey XSD intake, IfcClash clearance extra-method, clash→BCF file ingest, jurisdiction IDS document audit, SP 63 cover *template*)  
**Code / architecture:** extra methods on existing `IfcClashDetector`; no new ports / DI tokens  
**Checkpoint:** **`NO_GO`**

## Verdict

| Lane | Result |
|---|---|
| Application security (Critical/High) | **0** — no new fetch/SSRF surface in analyze; catalog URLs are static catalog data |
| Integrity (Medium) | **Findings below; none silently promote RT CLOSED** |
| Claims Lock | **PASS intended** after this pack’s docs refresh |
| Customer Checkpoint | Still **NO_GO** (RT-001/002/003) |
| Full pytest | **Not claimed as CI pin refresh.** Local Windows 15.08: 2259 passed / 12 skipped / 0 failed on HEAD `005b7bc` (`docs/evidence/runtime-baseline-wave-a-windows-2026-08-15.md`). `tests_passed` in README **stays 2167** (commit `88e726be`, N-26). |

## Findings

| ID | Sev | Status | Finding | Mitigation |
|---|---|---|---|---|
| RT-WA-01 | MED | **MITIGATED** | `AnalyzeProjectPackageUseCase._run_clash_detection` still calls only `ClashDetector.detect()` (single-file). `detect_between` / `detect_clearance_between` are adapter extra-methods, not port methods | Documented in TZ fn15 / README. Not wired as product MEP clash |
| RT-WA-02 | INFO | **CLOSED** | A2 first pin hashed 3 IDS files. Attack: «pack is clean» from n=3 | Pack-wide rerun: MOEXP 24 + AGR 4 + SPb 22 = **50** files, **0** document issues. Still not IfcTester CIM coverage |
| RT-WA-03 | MED | **MITIGATED** | Survey-report zip title vs XSD root `GeologicalReport` (engineering-geological, not all-discipline) | Catalog `note` + `SOURCE.md` |
| RT-WA-04 | MED | **MITIGATED** | 07.08.2026 news named construction-stage XSDs; they were **not** on the 14.08 catalog scrape | No invented files. `construction-stage catalog gap` in SOURCE.md |
| RT-WA-05 | INFO | **ACCEPTED** | LOC pin 73166/47587/2271; CI `tests_passed=2167` on `88e726be`. Local suite 15.08 measured 2259/12/0 — **not** copied into README | Honest split: CI pin vs local evidence file |
| RT-WA-06 | MED | **MITIGATED** | SP 63 template uses `Pset_CoveringCommon.CoveringThickness` on IfcSlab/Beam/Column (IfcCovering pset, not SP 63 table 8.1 / exposure class) | Pack `status=synthetic-template`; `calculation_correctness` stays NOT_IMPLEMENTED |
| RT-WA-07 | HIGH | **ACCEPTED** | None of A1–A6 close customer blockers | `closes_rt001/002/003=false`; honesty lock tests untouched |
| RT-WA-08 | INFO | **MITIGATED** | `catalog_zip_url` rows are not live-fetched in CI | XSD sha256 pins in tests; zips stay out of git |
| RT-WA-09 | MED | **MITIGATED** | Plan A4 said HVAC fixture; that IFC has **no tessellated geometry** | Live clearance uses `clash-clearance-gap-{a,b}.ifc`. HVAC not used. fn14 |
| RT-WA-10 | INFO | **CLOSED** | Temptation to add a new clash port after freeze lift | Extra-method only. `ClashDetector` protocol unchanged |
| RT-WA-11 | INFO | **ACCEPTED** | Auditor validates against IDS **1.0** XSD, including some MOEXP **1.1** files that produced 0 errors | Do not read as IDS 1.1 certification or xbim/IDS-Audit-tool binary |
| RT-WA-12 | INFO | **MITIGATED** | Clash→BCF uses **our** `export_bcf`, not IfcClash native BCF-XML | File ingest T1; `cde_import=NOT_VERIFIED` |

## Attack scripts that failed (good)

1. **«Survey XSD = RT-001 CLOSED»** — intake fail-closed on empty XML; no remark corpus.  
2. **«Clearance on HVAC = MEP delivered»** — HVAC fixture skipped; gap pair is walls; default DI Unconfigured.  
3. **«0 IDS document issues = Samolet profile»** — `customer_pack_hash=null`; public organ files.  
4. **«Clash→BCF = CDE import / RT-008 T2»** — `cde_import=NOT_VERIFIED`.  
5. **«SP 63 template = independent calculation»** — template 20 mm; not a solver.  
6. **«Construction-stage schemas are in the product»** — catalog gap; files not invented.  
7. **«Analyze now does federated clearance»** — still `detect()` self-clash only.

## Claims Lock spot-check

| Invariant | Status |
|---|---|
| No product accuracy >90% / customer SLA as fact | Intact |
| No native DWG / LibreDWG | Intact |
| No MEP system clash delivered | Intact (`mep_system_clash=NOT_VERIFIED`) |
| No CDE-ready BCF | Intact |
| No Checkpoint GO | Intact |
| No new DI token / port | Intact |
| One TechLab customer (Samolet); A101/Gals not a substitute corpus | Intact |

## Residual risks

1. Jury reads «50 IDS files, 0 issues» as CIM compliance.  
2. Jury reads clearance-gap as HVAC/MEP system clash.  
3. Jury reads MinStroy survey XSD as expertise remarks.  
4. Someone regenerates planted `clash-federated-box-*.ifc` and breaks evidence hashes (generator now keeps existing planted files).

## Not claimed closed

RT-001, RT-002, RT-003, native DWG, MEP delivered, CDE import, independent calculation correctness, buildingSMART Validation Service (needs a human account), ODA trial, live CDE T2.
