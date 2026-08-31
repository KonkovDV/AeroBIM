<!-- claims-lint: allow-file reason="Deep-study carrier facts; coverage_map_only; no names/hashes; NO_GO" -->
---
title: "Deep-study carrier facts — packs A/B/C (30.08.2026 evening)"
date: "2026-08-30"
last_updated: "2026-08-30"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Entity/property/format presence after unpack. Not pack processed.
  Not product accuracy. Not native RVT/NWD/LIRA. Not dual-rater gold.
  FireRating wall fill is not a fire-delivered claim. Checkpoint NO_GO.
---

# Deep-study carrier facts (30.08.2026 evening)

Machine pin: `python -c "from aerobim.domain.deep_study_facts import deep_study_snapshot"`.  
JSON: [`deep-study-carrier-facts-latest.json`](deep-study-carrier-facts-latest.json).  
Named trees stay under `.local/`. Pack letters match [`../quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md`](../quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md).

Checkpoint **`NO_GO`**. `processed: false`. `customer_confirmed_patterns: 0`. This is SIG-02 **depth on carriers**, not SIG-01 findings and not «пакет обработан».

## IFC (15 unique, IFC2X3 only)

Two exporters, both dated 20–21.08.2026:

| Exporter | Files | Packs |
|---|---:|---|
| Revit 23.1.30.97 (RUS) / IFC 23.3.1.0 (ODA SDAI 22.12) | 4 | B, C |
| EDM 5.02 + «alternative interface» 20.2.90.12 | 11 | A (6 AR + 5 KR) |

| Fact | A | B | C |
|---|---:|---:|---:|
| IfcSpace (AR) | 10 599 | 1 339 | 4 214 |
| NetFloorArea / Qto_SpaceBaseQuantities | **0** | **0** | **0** |
| IfcWall + StandardCase (AR) | 62 033 | — | — |
| FireRating filled on those walls | 3 538 (5.7 %), class **EI 45 only** | sparse mixed | sparse mixed |
| IfcGrid | **0** (plugin omits axes) | 13 (AR) | 53 (AR) |
| IfcReinforcingBar | **0** | **0** | **0** |
| AcousticRating | **0** | **0** | **0** |
| Duct / pipe / cable entities | **0** | **0** | **0** |

Doors on the same AR files also carry **EI30 / EI60 / EIS60**. That does not change the wall construct vs design-TZ class II / C0, and it is not fixture REI60.

KR `IfcMaterial.Name` carries concrete class tokens **B25 / B35** (CC-2 BIM side). Steel class is not in those names. `Pset_ReinforcementBarPitchOfWall` is present; pitch ≠ bars. `IfcFlowTerminal` exists on AR; that is not an MEP federation.

Pack C AR is the one file **over the 256 MiB SPF cap**. Do not raise `AEROBIM_MAX_IFC_BYTES`.

## PDF / CAD / LIRA (unique by name+size)

| Carrier | Unique | Note |
|---|---:|---|
| PDF | 1 440 | 44 200 pages; 130 without a text layer; **1** zero-page file (IRD/STU-class letter) |
| DWG | 1 227 | AC1032/2018 = 693; remainder 2004–2013. Native still `NOT_IMPLEMENTED` |
| RVT | 87 | Revit **2020** = 81; **2023** = 6; 20 workshared via Revit Server (`RSN://`) |
| NWD federations | 3 | one per house; NWC caches sit beside. Native fail-closed |
| LIRA blocks (pack A) | 16 | one block missing fragments #68/#69 and CRC-defect on #67 |
| `.lir` on pack B | **0** | KR IFC present, calculation model absent |

EIR v4.0 workbook + BIM-standard v4.0 are present as **text**. That is not `customer_approved` IDS (RT-002b OPEN).

## Tracker mapping (licensed speech)

| SIG | What this pass supplies | Forbidden speech |
|---|---|---|
| SIG-01 | Substrates: 15 IFC + 1 440 PDF (91 % with text) | Finding count = product accuracy |
| SIG-02 | Evening recensus + this pin | «43 ГБ обработаны»; commit names |
| SIG-04 | Observed classes (empty QTO, wall FireRating EI 45, grid-less plugin export, incomplete LIRA block, zero-page PDF). Catalog still unsigned | `customer_confirmed_patterns>0` |
| SIG-05 | Evidence for questions 5 (regs in an «unsupported» folder), 12 (RVT 2020/2023 + RSN), 13 (three NWD federations), 14 (readable rebar note still missing) | «пакет вопросов отправлен» (git does not send mail) |
| SIG-06 | `.lir` present on A and C; CC-2 tokens in KR IFC; CC-1/CC-3 still need a readable note | «конструкции пересчитаны»; native `.lir` parsed |
| SIG-07 | Counted RVT years and NWD federations | Native reader; DWG-ready |

Related: [`unpack-census-2026-08.md`](unpack-census-2026-08.md) · [`../quality/TZ_SEAM_COVERAGE_MAP_2026_08.md`](../quality/TZ_SEAM_COVERAGE_MAP_2026_08.md) · [`../quality/TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md`](../quality/TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md).
