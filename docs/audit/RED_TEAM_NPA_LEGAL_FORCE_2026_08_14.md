<!-- claims-lint: allow-file reason="Red Team NPA legal-force audit; forbidden phrases as non-claims; Checkpoint NO_GO" -->
---
title: "Red Team — NPA legal force (2026-08-14)"
date: "2026-08-14"
stage: "code+docs"
claim_boundary: >
  Adversarial review of TIM/CIM legal-force encoding after the 14.08.2026 NPA
  study. Not legal advice. Not customer accuracy. Checkpoint remains NO_GO.
  Does not close RT-001/002/003.
---

# Red Team: NPA legal force (14.08.2026)

**Author relationship:** Internal self-assessment  
**Scope:** domain register, jurisdiction IDS pointers, AGR class-1 fixture, living GTM/partners/regulatory docs, DWG memo, Qwen feasibility memo  
**Code freeze:** no new ports / adapters / DI (`moscow_agr` stays CUT)  
**Checkpoint:** **`NO_GO`**

## Reproduction

```text
python -m unittest tests.test_npa_legal_force tests.test_public_ids_pack_coverage tests.test_agr_exchange_checks tests.test_tz_proxy_rehearsal tests.test_rt_customer_blocker_honesty_lock tests.test_moexp_ids_coverage -v
python -m ruff check src/aerobim/domain/npa_legal_force.py src/aerobim/domain/tz_proxy_constructs.py
python -m mypy src/aerobim/domain/npa_legal_force.py
python scripts/lint_claims.py --matrix-guard
```

Focused unittest: **58 passed** (2026-08-14, CPython 3.12.10). matrix-guard: **OK**.

## Verdict

| Lane | Result |
|---|---|
| Application security (Critical/High) | **0** — no auth/egress change |
| Integrity / Claims Lock | **3 overclaims found and closed** in living docs; domain now refuses RT-close on IDS packs |
| Customer Checkpoint | Still **NO_GO** |
| New DI / `moscow_agr` port | **Not introduced** |

## Findings

| ID | Sev | Status | Finding | Mitigation |
|---|---|---|---|---|
| RT-NPA-01 | HIGH | **FIXED** | Living GTM/partners cited «состав ЦИМ с 01.03.2026» as if MinStroy order were in force | Project ID **155923**, negative MinEcon ORV, `legal_force=draft_unverified`. Scanner `cites_cim_composition_order_as_in_force` on living docs |
| RT-NPA-02 | MED | **FIXED** | DWG memo cited «ПП 614 п. 7» without distinguishing Rules item 7 (GIS pointers) from composition item 7 subitems b/g/d (PDF/A, LandXML, IFC) | Precise citation in memo + `PP614_FORMATS_CITATION` |
| RT-NPA-03 | MED | **FIXED** | `QWEN38_AEROBIM_FEASIBILITY` still said «УКЭП по ФЗ-309» | Rewritten to 63-ФЗ + 4420-КМ/14; 309-ФЗ ч.16 is not the UKЭП mandate (`CITATION_ERRATA`) |
| RT-NPA-04 | HIGH | **MITIGATED** | Public IDS zips (MOEXP / Moscow AGR / SPb CGE) could be read as federal NPA or Samolet EIR | Pointers + `overlay_ids_pack`: `legal_force=not_npa`; substitutes art. 49 / AGR certificate / EGRZ corpus / customer EIR = false; `closes_rt002=true` raises |
| RT-NPA-05 | MED | **MITIGATED** | AGR class-1 pass (11/11) looks like AGR approval | Fixture payload `product_function=precheck_exchange_shape`; cited NPA is territorial; IDS zip is not the NPA |
| RT-NPA-06 | MED | **VERIFIED** | PP RF 878 date collision (EGRZ 24.07.2017 vs radioelectronics 10.07.2019) | `PP878_DISAMBIGUATION` locked in tests |
| RT-NPA-07 | LOW | **ACCEPTED** | Checked-in MOEXP/Moscow/SPb *coverage JSON* not regenerated with `legal_force` in this pass (IfcTester pack runs) | Exporters now emit the fields on next export; pointers already carry them |
| RT-NPA-08 | LOW | **ACCEPTED** | «АГК с 01.06.2026» remains industry write-up, not a DGP PDF in-repo | Same residual as RT-OSINT-05; regulatory baseline labels it отраслевой разбор |
| RT-NPA-09 | INFO | **ACCEPTED** | GrK edition published 23.03.2026 (part in force 01.07.2026) not quoted article-by-article | Do not invent novella text; re-verify in SPS before external cite |
| RT-NPA-11 | HIGH | **MITIGATED** | MinStroy XSD intake could be read as RT-001 CLOSED or as unmodified XMLSchema11 load of PZ/ZnP | 14.08 evening: catalog subsections vendor PZ **01.07** / ZnP **01.01** (zip folders still `dev_`). XMLSchema11 still fails as published (`xml:id='Name'`); load-time documentation-id strip is a parser workaround. `overlay_egrz_intake(closes_rt001=True)` raises. No pass fixture |

## Attack scripts that failed (good)

1. **`overlay_ids_pack(..., closes_rt002=True)`** — `ValueError`.  
2. **Promote jurisdiction pointer to `customer_approved`** — pointers stay `draft`, `approval=null`.  
3. **«IfcTester coverage = CIM compliance / art. 49»** — `legal_force=not_npa`; `substitutes_grk_art_49_expertise=false`.  
4. **«AGR class-1 = свидетельство АГР»** — `substitutes_agr_certificate=false`; `territorial_scope=moscow`.  
5. **«ЕГРЗ = корпус замечаний / RT-001 CLOSED»** — public fields remain metadata; `closes_rt001` stays false.  
5b. **«MinStroy XSD = RT-001 CLOSED»** — versions now match ECPE; still `egrz_intake_precheck`; xml:id sanitize; no instance XML; `closes_rt001=false`.  
6. **«DWG не в 614 ⇒ вычеркнуть из ТЗ»** — memo still `TZ_MANDATORY_UNSUPPORTED`; regulator formats ≠ customer TZ.  
7. **Checkpoint GO** — no flip path.

## What the product may say (post-fix)

Pre-check / engine coverage on named public files. Territorial Moscow exchange shape on fixtures. Citation of a specific PP/GOST *item* with edition date. PDF/A + IFC/open-spec + XML as the **regulator** exchange set under PP 614 composition item 7 (when IM is mandatory under PP 331).

## What the product still must not say

Expertise passed. AGR approved. UKЭП verified. Full GOST/SP/PNST compliance. Samolet pack accepted. RT-001/002/003 CLOSED. MinStroy CIM-composition order in force. IM mandatory for every OKS.

## Residual product blockers (unchanged)

RT-001, RT-002, RT-003, native DWG, MEP system-aware clash, OIDC BFF `NOT_IMPLEMENTED`.
