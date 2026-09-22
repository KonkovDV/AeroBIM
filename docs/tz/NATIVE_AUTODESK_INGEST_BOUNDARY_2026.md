<!-- claims-lint: allow-file reason="Honest refusal of native RVT/NWD; IFC-first ingest; NO_GO" -->
---
title: "Граница входа: RVT и NWD не читаем, вход — IFC"
date: "2026-08-27"
last_updated: "2026-09-22"
status: active
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Fail-closed refusal of closed Autodesk formats. Not a DWG/RVT/NWD reader.
  Stock Navisworks does not write IFC. Checkpoint GO; customer_go false.
---

# RVT и NWD мы не читаем

25 августа заказчик спросил про native `.rvt` и `.nwd` среди классов набора. Парсера этих файлов в дереве нет.

Revit (`.rvt`, `.rte`) и Navisworks (`.nwd`, `.nwc`) — закрытые форматы. Бесплатного читателя, который можно положить в это MIT-дерево, нет. В матрице ТЗ про DWG это уже сказано. Про RVT и NWD строка молчала. Молчание на закрытом формате читается как незакрытый пункт ТЗ.

## Что делает клон

Носители этих форматов есть в локальной распаковке. Файл на диске — ещё не читатель. Счётчики живут в инженерных пинах, на эту страницу их не кладём. Попытка сдать такой файл заканчивается отказом.

| Куда попал файл | Что происходит |
|---|---|
| HTTP-загрузка `.rvt` / `.rte` / `.nwd` / `.nwc` | `UploadContentError`. Текст: `native RVT/NWD parser is not implemented; closed Autodesk format without a free reader` |
| HTTP-загрузка `.zip`, внутри файлы Autodesk или контейнер Revit (`BasicFileInfo`) | Та же `UploadContentError`. Переименование в `.zip` отказ не снимает |
| Анализ `drawing_sources` с этими суффиксами или `.zip`, который их называет | `capabilities.dwg_dxf=FAILED`. `summary.passed=false`. Успешный соседний DXF отказ не снимает |
| Опись комплекта `format=rvt` или `format=nwd` | `AEROBIM-PACKAGE-UNSUPPORTED-FORMAT` (ERROR), тот же код, что у DWG |
| Проверка | `python -m aerobim.tools.validate_native_autodesk_toolchain` → `claim_allowed=false` |

Бинарник Navisworks, переименованный в `.zip` без сигнатуры ZIP, на HTTP-загрузке отвергается: содержимое не совпало с расширением. Нечитаемый ZIP среди чертежей, который файлы Autodesk не называет, идёт прежним путём CAD `MISSING`. Из этого пути не следует, что мы читаем RVT.

## Как просим отдавать комплект

1. Авторская программа выгружает **IFC 2x3, IFC4 или IFC4x3**. Сюда входит Renga: назначающая сторона уже показывала её публично на деле ИЖС в Пушкино.
2. Листы и письма идут как **PDF/A**. ПП 614 и приказ Минстроя 783/пр для машиночитаемого контура собраны на PDF/A и IFC.
3. Рядом можно положить DXF, если нужны пометки CAD. Чтение DWG остаётся `NOT_IMPLEMENTED` (`validate_dwg_toolchain`).

Так уже устроен их обмен. Публичные кейсы Renga и Tangl на стороне заказчика говорят про IFC и RVT. Наш шлюз принимает IFC, IDS и листы. Штатный Navisworks IFC не пишет: плагину нужно установленное место. Федерацию в IFC выгружает назначающая сторона.

## Что остаётся открытым

RT-001, RT-002 и RT-003 остаются открытыми. `AEROBIM_MAX_IFC_BYTES` не поднимаем: на пине CI разбор IFC остаётся 256 МиБ. Поддержки native Autodesk здесь нет. Checkpoint `GO`. `customer_go` false.

## Лицензии по публичным прайсам

Снято 30 августа 2026. Страница была жива 1 сентября 2026. ODA Sustaining — 7 500 USD в первый год и 4 500 USD на продление. Это пол для SaaS *Drawings*. Revit и Navisworks в эту цену не входят. BimRv и BimNv указаны по 6 250 USD каждый. LibreDWG — GPL-3 или новее, в это MIT-ядро не входит. CADSoftTools CAD .NET на публичной странице начинается от 765 USD: это DWG и DXF. Источники и разбор: [`NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md`](../quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md) · [`FORMAT_INGEST_TRIAGE_2026_09.md`](../quality/FORMAT_INGEST_TRIAGE_2026_09.md).
