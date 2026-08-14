---
title: "Renga PNST 909-2024 — local pin stub (no binaries)"
date: 2026-08-05
status: PACK_PINNED_LOCAL
claim_boundary: >-
  Integrity + ToS note for Exp A. Files live only under .local/ (gitignored).
  Not OSS. Not publishable product accuracy without Renga confirmation.
---

# Renga ПНСТ 909 — публичный пин (без бинарников)

| Поле | Значение |
|---|---|
| Status | **PACK_PINNED_LOCAL** + **ToS cite GO** (2026-08-05) |
| Source page | https://rengabim.com/shablons/ |
| Public folder | https://disk.yandex.ru/d/mwP_LNRwnFD2Sg |
| Local root | `.local/renga-pnst909/pack/` |
| IFC extract | `.local/renga-pnst909/pack/IFC/` |
| Counts (local) | **94** top-level pack files (~1.63 GB); **45** `.ids`; **198** `.ifc` (~9.6 GB uncompressed) |
| Runtime | **18/22** scenarios IDS-executed (`runtime_clean`); 4 without IDS in pack |
| Inventory SHA-256 | `00c07565eb8a78f3a0a5ac40f74be04558e39211f50e9aa06fc3a4e35de46a87` |
| ToS note | `.local/renga-pnst909/NOTICE.md` — cite + aggregated metrics **allowed** |
| Machine pin | `.local/renga-pnst909/PIN.json` |

## ToS

**GO** на цитирование страницы и публикацию агрегированных чисел покрытия.  
**Не** вендорим бинарники; **не** заявляем product accuracy.

## This machine (2026-08-14)

Full 9.6 GB pack is **not** restored here. One member was extracted from the public `IFC.zip` for `run_renga_export_probe` (103 112 bytes, `Renga Professional 8.7.20879.0`, `FILE_SCHEMA=IFC4`). Evidence: [`../evidence/renga-export-probe-2026-08.md`](../evidence/renga-export-probe-2026-08.md). Not a Samolet export. Not Exp A 18/22 rerun.
