<!-- claims-lint: allow-file reason="Local Samolet max pass; coverage_map_only; SIG-01 volume≠accuracy; seven tasks Uncertain; NO_GO" -->
---
title: "Maximum licensed pass on a local NDA copy — 31.08.2026"
date: "2026-08-31"
last_updated: "2026-08-31"
status: active
version: "1.1.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  What git plus a gitignored quarantine copy can do for TZ v2, TechLab
  seven comparison tasks, MIK speech, and tracker SIG-01…08. Inventory and
  unsigned volume shape only. Not product accuracy. Not pack processed.
  Not Meets/Does-not. Not a jury exhibit. Checkpoint NO_GO.
---

# Максимум на локальной копии Самолёта (31.08)

Машина: `python -c "from aerobim.domain.channel_local_max_pass import channel_local_max_pass_snapshot"`.

Локальный прогон (имена и хэши не в git): `python -m aerobim.tools.run_channel_max_pass --pack <unpack-tree> --out .local/pack-out/channel-max-pass-unpacked-2026-08-31 --findings-lite-dir <rerun>`.

Триаж семейств: [`CHANNEL_PACK_TRIAGE_2026_08.md`](CHANNEL_PACK_TRIAGE_2026_08.md). Несжатые ГиБ дерева в git **не** публикуем.

Checkpoint **`NO_GO`**. Формулировка SIG-01: **«объём находок на канале получен»**. `publishable_finding_count` = **0**. Семь задач Техлаба остаются **Uncertain**. Каталог: `customer_confirmed_patterns=0`.

Это не закрытие SIG-01…08 у владельца. Git даёт форму и честный разбор; письма, IdP, два разметчика, подпись IDS и OA-9 остаются за владельцем.

## Что сделано на копии vs что нельзя

| Контур | Сделано | Не сделано / запрет |
|---|---|---|
| SIG-01 | Таксономия объёма; CLI `--findings-lite-dir`; локальный rerun IFC/PDF | Сырой счётчик как точность; «пакет обработан»; дефекты заказчика |
| SIG-02 | `pack_probe` + `pack_archive_overlap`; пины census / deep-study | «43 ГБ обработаны»; имена/хэши в git |
| SIG-03 | `expert`/`user` в API | `GET /v1/auth/bff` остаётся **501** |
| SIG-04 | ≥20 классов + `channel_carrier_observations` | Подтверждение заказчиком; dual-rater |
| SIG-05 | Черновик пакета вопросов | Отправка почты |
| SIG-06 | Четыре проверки; байт-токены B25/B35/ЛИРА | Решатель; разбор `.lir`; «конструкции пересчитаны» |
| SIG-07 | Одностраничник RVT/NWD/CV | Native ingest; CADSoftTools 1660 $ |
| SIG-08 | OA-10 в owner-actions | Письмо РУТ |
| ТЗ / Техлаб | Карта семи задач; QTO 0; EI 45; нет стержней; нет MEP IFC | Meets/Does-not; ТЭП сверены; огнестойкость сдана |
| МИК | Речь «доработка»; формула стадии | Checkpoint GO; точность >90% |

## Носители (уже в git, без имён)

Вечерний census 30.08: wrapper **2552**, unpack **6408**. Deep-study: 15 IFC **IFC2X3**; `NetFloorArea` **0**; стены FireRating при заполнении **EI 45**; `IfcReinforcingBar` **0**; воздуховоды/трубы/кабели **0**. Один IFC выше SPF 256 МиБ — RocksDB, **не** подъём default.

Unsigned-пакеты `REQ-*` eq + `SAM-AR-*` exists на одном pset.prop — overlap, не два дефекта.

## Глубокий состав пакета (31.08, unpack-дерево 6408 файлов)

Агрегаты без имён и без несжатых ГиБ. Пин: `pack_family_snapshot()`. Источник обхода остаётся в `.local/`.

- Расчётные бинарники (именованные `.lir` / tilde / f74 / SCAD sidecar — **235** файлов) — **большинство байт** дерева. Не разбираем, не «конструкции пересчитаны».
- PDF **2046**: вектор 1318 / скан-подобные **728** — очередь HITL, без OCR-заявлений.
- DWG 1877 · DXF **321 (все ASCII)** · RVT 75 · NWD/NWC 8 · 3ds Max 164 (рендер-активы, не доказательства проекта).
- Office 579: OOXML 295 / OLE 284. В unpack-дереве 4 IFC-копии (15 уникальных уже прогнаны; повторный анализ не нужен).
- Четыре «объекта»: один расчётно-тяжёлый, один ОВ-тяжёлый, один — корпоративное дерево Стандарта, один сбалансированный. IFC+PDF-complete — **2**. Класс «РД» на путях: **0**.

### CC-2/CC-4 субстрат (SIG-06, не MATCH)

- **6 docx** содержат фразу «класс бетона» (все 6 — также про нагрузки); в контексте ±160 символов валидные классы СП 63 включают B25, B7, B15, B35, B30. Наивный regex по всем docx шумит (оси/марки).
- **46 xlsx** содержат токены нагрузок — кандидаты сбора нагрузок для CC-4.
- Расчётных PDF класса 6 почти нет: субстрат CC-2/CC-4 живёт в **Office**, не в PDF.
- Следующий шаг — владелец подтверждает каноничную записку на объект; движок `compare_declared_tables` уже умеет fixture-сверку.

## Решения по семействам файлов

| Семейство | Решение | Никогда |
|---|---|---|
| IFC (15 уникальных) | Уже прогнаны SIG-01; источник carrier-фактов | Повторный прогон копий как «новый объём» |
| PDF вектор | Инвентарь шифров (cartography); текст по запросу CC | CV-счёт дверей как findings |
| PDF скан | HITL-очередь; владелец решает про OCR-бюджет | OCR-заявление от нас |
| DWG | Fail-closed; вилка ADR-003/ODA — SIG-07, владелец | DWG-ready |
| DXF ASCII | `partial`; advisory-геометрия после окна КТ#3 | Полный парсинг в спринте A |
| RVT / NWD | Fail-closed; одностраничник SIG-07 | Native ingest |
| ЛИРА/SCAD named ext | **Не разбираем.** Владелец экспортирует записку/txt-протокол/xlsx | «Пересчитали» |
| Office | **Читаемый расчётный слой**; структурный разбор xlsx/docx только в `.local` | Токен = MATCH |
| Дерево Стандарта | Источник для задачи 2 Техлаба и будущего подтверждения каталога | Как источник дефектов ПД |
| 3ds Max / изображения / sidecar | Исключить из реестра приоритетов | Как доказательную базу |

## Что владелец всё ещё должен

OA-9 (тоталы канала вне git до режима данных) · SIG-05 через организаторов · SIG-08 письмо · production IdP к 18.09 · два разметчика · читаемая записка для CC-2/CC-4 MATCH · **не** поднимать `AEROBIM_MAX_IFC_BYTES`.

Связанные: [`CHANNEL_PACK_TRIAGE_2026_08.md`](CHANNEL_PACK_TRIAGE_2026_08.md) · [`TRACKER_EIGHT_TASKS_2026_08.md`](TRACKER_EIGHT_TASKS_2026_08.md) · [`TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md`](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md) · [`TZ_SEAM_COVERAGE_MAP_2026_08.md`](TZ_SEAM_COVERAGE_MAP_2026_08.md) · [`FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md`](FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md) · [`../evidence/pack-family-facts-2026-08.md`](../evidence/pack-family-facts-2026-08.md).
