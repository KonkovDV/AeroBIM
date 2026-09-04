<!-- claims-lint: allow-file reason="Local pin stub; city AGR IFCs not vendored; RT stay OPEN" -->
---
title: "Moscow AGR city example IFCs — local pin (no binaries in git)"
date: 2026-08-24
status: PACK_PINNED_LOCAL
claim_boundary: >-
  Integrity + ToS note. IFC binaries live only under .local/ (gitignored).
  Official IDS/TEP/Vedomost stay in samples/. Not a PD pack. Not Samolet.
  Does not close RT-001 / RT-002b / RT-003. Checkpoint GO; customer_go false.
closes_rt001: false
closes_rt002b: false
closes_rt003: false
---

# Moscow AGR city examples — public pin (no binaries)

City article [cim-agr](https://stroimprosto.mos.ru/knowledge/article/cim-agr/) publishes example CIM IFCs next to the official IDS. Those IFCs are **not** in git (size / city ToS). This pin is how AeroBIM **connects** them locally.

| Field | Value |
|---|---|
| Status | **PACK_PINNED_LOCAL** |
| Source page | https://stroimprosto.mos.ru/knowledge/article/cim-agr/ |
| Manifest (URLs, sizes) | [`samples/agr/dgp/CITY_IFC_MANIFEST.json`](../../samples/agr/dgp/CITY_IFC_MANIFEST.json) |
| Local root | `.local/moscow-agr-examples/` |
| IFC extract | `.local/moscow-agr-examples/ifc/` |
| Official IDS (in git) | `samples/ids/moscow-agr/pack/` |
| Official TEP / Vedomost (in git) | `samples/agr/dgp/` |
| Sign-off profile | `moscow_agr_2026` (clash/MEP honest SKIPPED) |
| Machine pin | `.local/moscow-agr-examples/PIN.json` |

## What is connected

1. Class-1 AGR exchange (IFC4 ReferenceView, five-field filename, no proxy, TEP sidecar, Vedomost XSD).
2. Official city IDS via IfcTester on the default five-field basement IFC (`NN_K01_S00_AR_AGR.ifc`).
3. Honest-scope policy `moscow_agr_2026`: clash/MEP stay SKIPPED; ACL/audit stay on.

## What is not connected (and must not be claimed)

- PD sheets, TZ, two revisions, calculations, expertise remarks, dual raters.
- `summary.passed` as Samolet accuracy.
- RT-001 / RT-002b / RT-003 closed.
- `inject_defects` — blocked until a **clean PD pack** exists. City CIM examples are not that pack.

Four-field names (`NN_K00_PS_AGR.ifc`, `NN_K00_BIO_AGR.ifc`) are expected to fail `AEROBIM-AGR-FILENAME` even though the city published them.

## Commands

```text
cd backend
python -m aerobim.tools.fetch_moscow_agr_city_examples
python -m aerobim.tools.run_moscow_agr_city_examples
```

`--skip-ids` skips IfcTester. `--ids-all` runs IDS on every IFC (the 50 MB section file is slow).
