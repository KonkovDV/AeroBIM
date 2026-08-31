<!-- claims-lint: allow-file reason="Channel pack Red Team triage; LIRA majority≠solver; GiB not in git; NO_GO" -->
---
title: "Channel pack Red Team triage — 2026-08-31"
date: "2026-08-31"
last_updated: "2026-08-31"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  KILL/HOLD/ACCEPT over the local unpack inventory and CC-2/CC-4 shortlist.
  Calc binaries are the majority of unpack bytes — inventory, not a solver.
  Token shortlists are not MATCH. Uncompressed GiB stays .local. Not pack
  processed. Checkpoint NO_GO.
---

# Триаж пакета канала (31.08.2026)

Машина: `python -c "from aerobim.domain.channel_pack_triage import pack_triage_snapshot"`.

Пин семейств: `python -c "from aerobim.domain.pack_family_facts import pack_family_snapshot"`.

Живой обход unpack-дерева **совпал** с вечерним census 30.08 (**6408** файлов). Именованные расширения расчётного комплекса — **235** файлов. Бинарные расчёты — **большинство байт** дерева (точное число ГиБ в git **не** публикуем, OA-9). Читаемый слой CC-2/CC-4: **6** docx с фразой «класс бетона», **46** xlsx с токенами нагрузок. Это **не** MATCH.

Checkpoint **`NO_GO`**. `detected_count: 0`. `processed: false`. Семь задач Техлаба — **Uncertain**.

Связанные: [`CHANNEL_SAMOLET_MAX_PASS_2026_08.md`](CHANNEL_SAMOLET_MAX_PASS_2026_08.md) · [`SIG01_CHANNEL_TRIAGE_2026_08.md`](SIG01_CHANNEL_TRIAGE_2026_08.md) · [`CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md`](CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md).

## Этот проход (KILL / HOLD / ACCEPT)

| ID | Атака | Тормоз |
|---|---|---|
| RT-PACK-PROCESSED | 6408 файлов с хэшами = пакет обработан | `processed=false`; агрегат — инвентарь |
| RT-PACK-43GB | «43 ГБ» как замер или «обработано» | Формулировка задачи трекера, не этот обход |
| RT-PACK-GIB | Несжатые ГиБ NDA-дерева в git до OA-9 | `uncompressed_gib_in_git=false` |
| RT-PACK-LIRA-SOLVE | `.lir`/f74/tilde = конструкции пересчитаны | `parse_lira=false`; IUA TL-10 |
| RT-PACK-TOKEN-MATCH | 6 docx / 46 xlsx = CC-2/CC-4 MATCH | `is_cc2_match=false`; нужна каноничная записка |
| RT-PACK-NAIVE-B | Голые B67/B56 во всех docx = класс бетона | Окно ±160 вокруг «бетон/класс» |
| RT-PACK-IFC-RERUN | 4 копии IFC = новый объём SIG-01 | 15 уникальных уже прогнаны |
| RT-PACK-STD-DEFECT | Дерево Стандарта = дефекты ПД | Задача 2 Техлаба; `confirmed=0` |
| RT-PACK-MAX-EVIDENCE | 3ds Max / картинки = доказательства проекта | Вне priority 1 |
| RT-PACK-DXF-DWG | 321 ASCII DXF = DWG-ready | DXF `partial`; DWG fail-closed |
| RT-PACK-OCR | 728 скан-PDF = OCR сдан | HITL; бюджет OCR — владелец |
| RT-PACK-SCAN-FINDING | HITL сканов = находки чертежа | `service_hitl`; IUA SAM-03 |
| RT-PACK-PP87 | Токены ПЗ/АР/КР/КЖ = 87-ПП | `statutory_pp87=false` |
| RT-PACK-RD | Большой пакет ⇒ PD↔RD runnable | `tz_class_2_rd_files=0` |
| RT-PACK-MEETS | Семейства ⇒ Meets/Does-not семи задач | Criterion **Uncertain** |
| RT-PACK-HASH-GIT | Коммит `pack-local.json` / TSV | OA-9 |
| RT-PACK-TXT-STUB | Маленькое `.local/pack` (txt) = комплект BIM | Носители — unpack-дерево |
| RT-PACK-VOLUME-F1 | Объём SIG-01 = F1 фикстур / каталог | `publishable_finding_count=0` |
| RT-PACK-OOXML-PARSE | Разобрать 46 xlsx и сдать CC-4 | HOLD: только `.local`; MATCH ждёт записку |
| RT-PACK-OA9-SHARE | Вставить агрегат в чат до ответа OA-9 | HOLD: вставляет владелец |
| RT-PACK-OCR-BUDGET | Обещать OCR 728 сканов в спринте A | HOLD: решение владельца |
| RT-PACK-CENSUS-MATCH | Обход 31.08 расходится с пином 30.08 | ACCEPT: 6408 совпало |
| RT-PACK-HASH-LOCAL | OA-9 запрещает даже локальные хэши | ACCEPT: хэши только `.local/` |
| RT-PACK-CLASS-SHORTLIST | Нет читаемого субстрата CC-2 | ACCEPT: 6 docx; на КР IFC есть B25/B35 |
| RT-PACK-DXF-ASCII | DXF бинарный и нечитаем | ACCEPT: все 321 ASCII; всё ещё `partial` |

## Что чинить в речи и git на этом проходе

1. **Не публиковать несжатые ГиБ** unpack-дерева. Лицензия: «расчётные бинарники — большинство байт».
2. **Не называть токен MATCH.** Shortlist 6/46 — кандидаты, сверка `compare_declared_tables` после каноничной записки.
3. **Не путать txt-stub `.local/pack` с комплектом.** SIG-02 / SIG-06 ходят в unpack-дерево.
4. **Не перепрогонять 4 IFC-копии** как новый объём SIG-01.

Не разбирать `.lir`. Не коммитить `pack-local.json`. Не поднимать SPF 256 МиБ.
