<!-- claims-lint: allow-file reason="Format-ingest Red Team triage; IFC+PDF/A exchange; not a DWG product; NO_GO" -->
---
title: "Format-ingest Red Team triage — 2026-09-01"
date: "2026-09-01"
last_updated: "2026-09-01"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  KILL/HOLD/ACCEPT over closed CAD/solver files. KT#3 exchange is IFC + PDF/A
  (PP 614 / MinStroy 783/pr). Closed Autodesk CAD and `.lir` stay fail-closed.
  ODA trial is measurement, not a product. Checkpoint NO_GO.
---

# Триаж форматов ingest (01.09.2026)

Машина: `python -c "from aerobim.domain.format_ingest_triage import format_ingest_triage_snapshot"`.

Семь классов решения (ISO 19650 объект обмена; Kane IUA; EGCC Missing/Uncertain; Солихин 1–4): назначающая сторона; лицензионный SDK; reverse-engineering; конвертер-сайдкар; документ-прокси; HITL/Missing; письменный OUT.

**Решение окна КТ#3:** не писать читалки DWG / NWD / RVT / `.lir`. Shared-gate — IFC + векторный PDF. Сканы — HITL. Сводная Navisworks → IFC и записки ЛИРА — запрос назначающей стороне. ODA 60 дней — замер потерь (ADR-003), не продукт.

Лицензионный пол (attributed 30.08, страница ODA жива 01.09): Sustaining 7 500 USD — DWG-контур, не Revit. BimRv / BimNv — по 6 250 USD. Пара RVT+NWD ≈ 20 000 USD в первый год. CADSoftTools CAD .NET от 765 USD. LibreDWG — GPL-3, не MIT-ядро. Stock Navisworks **не** пишет IFC (плагины требуют их рабочее место).

Связанные: [`NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md`](NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md) · [`../tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md`](../tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md) · [`../architecture/ADR-003-dwg-oda-trial-kt3-2026.md`](../architecture/ADR-003-dwg-oda-trial-kt3-2026.md) · [`CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md`](CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md) · [`../demo/KT3_RVT_NWD_CV_ONEPAGER_2026_08.md`](../demo/KT3_RVT_NWD_CV_ONEPAGER_2026_08.md) · [`SPG_CONSTRUCTION_VS_FM_2026_09.md`](SPG_CONSTRUCTION_VS_FM_2026_09.md).

Checkpoint **`NO_GO`**. `detected_count: 0`. `is_dwg_ready: false`.

## Этот проход (KILL / HOLD / ACCEPT)

| ID | Атака | Тормоз |
|---|---|---|
| RT-FMT-DWG-PRODUCT | Любой DWG-путь = продукт CAD | `dwg_dxf` никогда OK; ADR-003 FAILED |
| RT-FMT-PARSE-NWD | Python-читалка NWD, потому что файлы есть локально | Нет публичной схемы; presence ≠ reader |
| RT-FMT-NAVIS-IFC | Navisworks уже пишет IFC — запрос не нужен | Stock UI/API IFC не экспортирует |
| RT-FMT-PARSE-LIR | Разобрать `.lir` или свой FEM как SIG-06 | `native_lir=not_implemented`; сверка с запиской |
| RT-FMT-SUSTAINING-RVT | Sustaining 7 500 $ = native RVT/NWD | BimRv/BimNv — отдельные расширения |
| RT-FMT-LIBREDWG | LibreDWG в MIT-ядро | GPL-3; ADR-002 LICENSE не меняет |
| RT-FMT-EZDXF-DWG | ezdxf на DXF = закрытый DWG | DWG требует ODA File Converter, другая лицензия |
| RT-FMT-OCR-DONE | Скан-PDF = OCR сдан | Вектор в git; сканы HITL; `cv_human_level=MISSING` |
| RT-FMT-BENCH-OURS | DrawingVQA / Appl. Sci. как наша точность | Чужие корпуса; RT-001 OPEN |
| RT-FMT-ODA-PRODUCT | 60-дневный trial = фича на карте жюри | ADR-003: fact-finding; `claim_allowed=false` |
| RT-FMT-ADSK-BUY | Купить Revit API для РФ-юрлица в этом окне | Канал Autodesk 2022+; не путь КТ#3 |
| RT-FMT-RAISE-SPF | Поднять SPF 256 МиБ, чтобы «влез» native CAD | Кап — in-memory IFC; native — класс формата |
| RT-FMT-ODA-TRIAL | Не мерить proxy/SHX на Drawings trial | ADR-003 разрешает замер; `claim_allowed` остаётся false |
| RT-FMT-SDK-SIGN | Купить BimRv/Nv до подписи профиля Самолёта | Правило покупки ADR-003: доля DWG-only + профиль |
| RT-FMT-GPL-PROC | LibreDWG sidecar, чтобы обойти copyleft | Юридическая вилка; без license ADR не ship |
| RT-FMT-EXCHANGE | Молчание в п. 1.1.5 = не закрытый native RVT | ПП 614 / 783/пр: PDF/A + IFC |
| RT-FMT-FAIL-CLOSED | Тихий skip `.rvt`/`.nwd`/`.dwg`/`.lir` в ZIP | Upload и ZIP-члены fail-closed |
| RT-FMT-CC-NOTE | На карточке восьми задач нет пути ЛИРА | CC-2/CC-4 vs записка; не решатель |
| RT-FMT-SEVEN | Только A/B/C для DWG; NWD/ЛИРА без карты | Семь классов на каждый закрытый формат |

## Что делать в окне (не парсеры)

1. Письмо: федерация NWD → IFC; 1–2 читаемые записки; native OUT в профиле.
2. Прогон SIG-01 на IFC + PDF. Не поднимать SPF default.
3. Опционально: ODA Drawings 60-day на эталонном DWG — цифры потерь в `.local/`, не pin CI.

Не говорить: продукт CAD; «откроем NWD»; «ЛИРА пересчитана»; Sustaining = Revit; OCR сдан; пакет обработан.
