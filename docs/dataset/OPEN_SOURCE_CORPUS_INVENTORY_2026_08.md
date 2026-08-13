# Open-source corpus inventory (Sprint 2)

**Date:** 2026-08-05 (tracker pack refresh)  
**claim_level:** inventory only — not product accuracy; Checkpoint **NO_GO**

**Обязательная оговорка:** ни один открытый корпус **не закрывает** блокер по точности (RT-001): нигде нет размеченных экспертами верных и ложных срабатываний на комплекте заказчика. Открытые данные дают регресс, устойчивость и замер времени — **не** публикуемую точность.

Rule: same as BSI — verbatim NOTICE + pin, or link-only until license GO. No derivatives without explicit license.

**Decision update:** do **not** draw synthetic geometry from scratch. Prefer real IFC → BatchPlan/ResBIM plans → planted defects. Detail: [`OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md`](OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md).

## Приоритетные источники (что даёт / чего не даёт)

| Источник | Что даёт | Чего не даёт |
|---|---|---|
| **Комплект МКД по ПНСТ 909-2024** (Renga, IFC+IDS, 22 сценария) | Регресс IDS/свойств; RU номенклатура; **Exp A + вторая ось покрытия** | Экспертную разметку TP/FP; publishable accuracy; ToS ≠ OSS license |
| **Реестр ПД повторного применения Минстроя** | — | **DEAD для файлов** (ФЗ 275-ФЗ; ЕГРЗ). Exp A перенесён на Renga |
| **Закупочная документация (zakupki.gov.ru)** | Язык ТЗ / разделы ПД / сметы в открытых архивах | IFC+IDS эталон; размеченный корпус |
| **Перечни типовых замечаний госэкспертиз** | Человеческий каталог (Exp B: Киров КР; Мордовия АР/ВК; **план:** СПб АР + Амур) | Precision/recall |
| buildingSMART IDS TestCases (n=290) | Регресс IDS CC BY-ND | Product accuracy; customer norms |
| IFC-Bench v2 (pin) | Открытый QA-слой моделей | Customer TP/FP; не vendor GPLv3 в MIT tree |

## Полный инвентарь

| Source | In repo? | License | Storage | Status | Notes |
|---|---|---|---|---|---|
| buildingSMART IDS TestCases | Yes | CC BY-ND 4.0 | Vendored + NOTICE + pins | **READY** | 290 regression pairs |
| buildingSMART BCF/IDS XSD | Yes | CC BY-ND 4.0 | Vendored + NOTICE | **READY** | RT-W-01 |
| AeroBIM fixtures / Level-B | Yes | Fixture / MIT | In-tree | **READY** | Synthetic floor for Sprint 2 PDF |
| **IFC-Bench v2** | Pin only | QA **CC BY 4.0**; models per-file (exclude GPLv3 from MIT tree) | `.local/ifc-bench-v2` + [`ifc-bench-v2/IMPORT_PINS.json`](../../samples/benchmarks/ifc-bench-v2/IMPORT_PINS.json) | **PINNED** | Measured 1026 QA rows; smoke 25/1026 scored @ 1.0 (`docs/evidence/ifc-bench-v2-smoke-latest.json`) |
| Типовые замечания КР (Киров) | Evidence doc + `.local` PDF | Public PDF | Exp B evidence | **USED** | Coverage map only |
| ПНСТ 909-2024 МКД (Renga) | Local pin only (no GH vendor) | Publisher ToS («ознакомительные») | `.local/renga-pnst909/` (45 IDS / 198 IFC) | **PACK_PINNED / Exp A** | Stub [`RENGA_PNST909_LOCAL_PIN_2026_08_05.md`](RENGA_PNST909_LOCAL_PIN_2026_08_05.md); ToS before metrics publish |
| Реестр Минстроя ПД повторного применения | No | N/A (no download) | — | **DEAD_CHANNEL** | Exp A → Renga |
| Закупки на проектирование | No | Public procurement | link_only | **INVENTORY** | Language of pain / acceptance |
| СПб / Амур типовые ошибки АР | No | Public HTML | `.local/evidence-sources/` | **PLANNED** | Exp B AR recount |
| KAAN residential IFC+plans | No | **No open primary** — [`KAAN_LICENSE_HONESTY_2026_08_04.md`](KAAN_LICENSE_HONESTY_2026_08_04.md) | pin_or_link_only | **PARTIAL** | Do not vendor |
| OSArch open data directory | No | varies | link_only | **PARTIAL** | MEP rehearsal; ≠ RT-003 close |
| BatchPlan / ResBIM | No | BatchPlan **MIT** + pythonocc — [`BATCHPLAN_PROBE_2026_08_04.md`](BATCHPLAN_PROBE_2026_08_04.md) | tool pin | **PARTIAL** | Preferred synthetic pipeline; not wired |
| ArchCAD-400K / FloorPlanCAD | No | check upstream | EXTERNAL | **PARTIAL** | Symbol vision (AECV weak spot) |
| CODE-ACCORD | No | check HF | EXTERNAL | **PARTIAL** | WP-04 / RT-002 later |
| Минстрой / Renga samples | No | TBD | pin_or_link_only | **INVENTORY** | No vendor without GO |
| CubiCasa5K / CVC-FP | No | via AECV | EXTERNAL_PIN | **INTERNAL_ONLY_LICENSE_REVIEW** | Do not copy to samples |

## ifcdiff / TZ row 28

See [`IFCDIFF_TZ_GAP_NOTE_2026_08_04.md`](IFCDIFF_TZ_GAP_NOTE_2026_08_04.md). Thin GUID/attribute adapter + fixture landed (`Tokens.IFC_MODEL_DIFF`); matrix row 28 stays **MISSING** until package-vs-package CDE compare. No `deepdiff` / wheel `ifcdiff` CLI.

## Manifest sync

- Root `DATASET_MANIFEST.json`: `review_pending=0`  
- Sprint provenance: CC BY-ND aligned  
- IFC-Bench v2: pins JSON only (no 2 GB vendoring this commit)
