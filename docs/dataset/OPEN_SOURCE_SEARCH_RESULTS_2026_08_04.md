---
title: "Спринт 2, блок 1: открытые источники данных — результаты поиска"
date: 2026-08-04
status: verified_inventory
version: "1.1.0"
scope: >-
  Блок 1.1 (инвентаризация). Landed into repo after operator research pass.
  Numbers for IFC-Bench v2 cross-checked against Hugging Face card 2026-08-04.
claim_boundary: >-
  Inventory and planning only. Does not close RT-001/002/003. Checkpoint NO_GO.
  Licenses for PARTIAL sources must be opened at primary URLs before vendoring.
---

# Открытые источники данных: что найдено

## 0. Главный вывод

Синтетику генерировать **не нужно с нуля**. Три опоры критического пути:

1. **Реальные IFC** (IFC-Bench v2, OSArch, …) — модель ↔ дисциплина уже есть.  
2. **BatchPlan** (или ResBIM) — 2D из вашего IFC → эталон по построению + программный инжектор ошибок.  
3. **`ifcdiff` в IfcOpenShell** — закрытие пробела ТЗ «сравнение версий» без новых зависимостей.

---

## 1. Реальные IFC-модели

### 1.1. IFC-Bench v2 — **VERIFIED** (HF card 2026-08-04)

- URL: https://huggingface.co/datasets/sylvainHellin/ifc-bench  
- GitHub: https://github.com/sylvainHellin/ifc-bench  
- QA pairs: **1 027** (v2 CSV); fixed eval split 514 test / 513 train (`eval-split-hellin2026.csv`; post-dedup train note on HF)  
- Projects / IFC files (HF card): **22 projects**, **51 IFC models** (operator note «21/37» superseded by HF)  
- QA license: **CC BY 4.0**  
- Per-model licenses: mostly CC BY 4.0 / MIT; **GPLv3** models must not be vendored into AeroBIM MIT tree without isolation: `4351`, `ettenheim_gis`, `hitos`, `samuel_macalister_sample_house`  
- CSV sha256 (HF): v2 `8f08f5d04834a79310eb7de81f2d6812e74d53a01363affdb815bf86dfc4dbf4`  
- Paper: arXiv:2605.01698; GNI 2026 Hellin/Nousias/Borrmann  

**AeroBIM today:** v2 smoke **25/1026** countable probes @ 1.0 on subset; measured CSV sha `e47ccd…` (HF card pin stale). Evidence: [`../evidence/ifc-bench-v2-smoke-latest.json`](../evidence/ifc-bench-v2-smoke-latest.json). Not product accuracy; does not close RT-001.

### 1.2. KAAN — **PARTIAL — do not vendor**

BatchPlan paper used **6** KAAN projects for tool development — **not** a redistributable open corpus. Primary open license **not found**. Record: [`KAAN_LICENSE_HONESTY_2026_08_04.md`](KAAN_LICENSE_HONESTY_2026_08_04.md).

### 1.3. OSArch Example Files — **PARTIAL**

https://wiki.osarch.org/index.php/AEC_Open_Data_directory — IFC2X3/4/4x3 including MEP. Useful for RT-003 engine rehearsal; does **not** close RT-003.

### 1.4. IFCNet / BIMNet — auxiliary

Classification / scan-to-BIM; secondary for current TZ path.

---

## 2. Чертежи / символы (AECV weak spot)

| Set | Status | Note |
|---|---|---|
| ArchCAD-400K | PARTIAL | Symbol panoptic; NeurIPS 2025 claim via catalog |
| FloorPlanCAD | PARTIAL | HF Voxel51/FloorPlanCAD |
| MLSTRUCT-FP / ResPlan | PARTIAL | Catalog only |

Do not vendor until primary license read. Improves vision contour later; not RT-001.

---

## 3. Синтетика: порождать, не рисовать

| Tool | Status | Role |
|---|---|---|
| **BatchPlan** (`github.com/byildiz/BatchPlan`) | PARTIAL (MIT tool; pythonocc blocker) | See [`BATCHPLAN_PROBE_2026_08_04.md`](BATCHPLAN_PROBE_2026_08_04.md) |
| ResBIM | PARTIAL | Ready model+plan pairs |
| SESYD / SFPI | PARTIAL | Methodology reference |

Preferred pipeline: real IFC → BatchPlan plan → programmatic defect → known GT.

---

## 4. Нормы (RT-002 path)

| Set | Status |
|---|---|
| CODE-ACCORD | PARTIAL — expert-annotated; England/Finland; WP-04 later |
| AECBench | PARTIAL |
| Purdue PTBC | PARTIAL |

Does not replace Russian norm pack; measures pipeline before Samolet norms.

---

## 5. Пробел ТЗ «сравнение версий»

Thin GUID/attribute IFC model-diff landed (no deepdiff). Wheel has no `ifcdiff` CLI. TZ row 28 remains **MISSING** for CDE package-vs-package compare. See [`IFCDIFF_TZ_GAP_NOTE_2026_08_04.md`](IFCDIFF_TZ_GAP_NOTE_2026_08_04.md).

---

## 6. Порядок работ (обновлённый)

| # | Action | Est. |
|---|---|---|
| 1 | Pin IFC-Bench v2 (QA CSV + non-GPL models policy) into inventory/pins | 0.5 d |
| 2 | Run deterministic comparable subset on v2; publish honest n_scored / n_total | 1 d |
| 3 | Open KAAN primary license | 0.5 d |
| 4 | BatchPlan + error injector on 5–10 IFCs | 2 d |
| 5 | Block-2 metrics (already have synthetic floor; re-run on planted real-geometry) | 1 d |
| 6 | Wrap `ifcdiff` → close TZ row 28 | 1 d |
| 7 | CODE-ACCORD → September | — |

---

## 7. Чего отчёт не сделал

- Full Block-2 customer metrics — needs local runs (synthetic floor already in `docs/evidence/sprint2-synthetic-baseline-*`).  
- Customer outreach — operator.  
- License texts for PARTIAL sources — open primary URLs before vendoring.  
- RT-001/002/003 — still customer artifacts; Checkpoint **NO_GO**.

## Sources

| Source | Status |
|---|---|
| HF IFC-Bench card | **VERIFIED** 2026-08-04 |
| arXiv:2605.01698 | **VERIFIED** id |
| DataDrivenAEC catalog | secondary index |
| KAAN / BatchPlan / ArchCAD / … | **PARTIAL** until primary license read |
