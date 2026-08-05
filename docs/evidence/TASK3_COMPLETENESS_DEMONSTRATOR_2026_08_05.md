---
title: "Task 3 — completeness-class demonstrator (Exp B 25pp KR)"
date: 2026-08-05
rev: "2026-08-05 LOGIC_ABSENT #2+#4 closed"
head: "pending"
claim_level: coverage_map_update_AUTHOR_CLAIM
ports_delta: "+0"
adapters_delta: "+0"
tokens_delta: "+0"
claim_boundary: >-
  Open/synthetic package completeness only. Not product accuracy. Not PNST 909
  vendoring. Checkpoint NO_GO. Inventory-level topics/justification markers only —
  not OCR of customer ТЧ and not engineering calc correctness.
---

# Задача 3 — демонстратор класса «полнота комплекта»

**Зачем:** из 42% условных КР **25 п.п.** зависели от полноты комплекта, не от норм «Самолёта». Проверить на открытых/синтетических данных, какие из 6 строк **реально срабатывают**.

**ПНСТ 909-2024:** публичный комплект Renga (IFC по разделам + IDS) существует ([rengabim.com/shablons](https://rengabim.com/shablons/)), в репо **не вендорен** (`pin_or_link_only`). Прогон сделан на **синтетическом residential inventory + section JSON + public buildingsmart IFC path_hint** — тот же класс проверок (WP-05 + SectionDiff), без RT-002.

**Дельта:** порты **+0**, адаптеры **+0**, токены **+0**. Добавлены rules + fixtures + тесты + этот отчёт.

## Шесть строк КР (25 п.п.) — вердикты

| # | Суть | Вердикт | Runtime proof | Root cause (было) | Что сделано |
|---:|---|---|---|---|---|
| 2 | Нет сведений полов/перегородок в ТЧ | **обнаруживается** | `AEROBIM-PACKAGE-TECHNICAL-SPEC-MISSING-TOPIC` | было LOGIC_ABSENT | `content_topics` на `technical_spec` (inventory-level) |
| 3 | ТЧ ≠ значения раздела (PD↔RD) | **обнаруживается** | `SECTION-PAIR-KZH-*` | — | **Не** ТЧ≠лист / OCR |
| 4 | Расчёты необоснованно в составе ПД | **обнаруживается** | `AEROBIM-PACKAGE-UNJUSTIFIED-CALCULATION` | было LOGIC_ABSENT | `calculation` + stage PD + `has_justification=false` |
| 9 | Нет фундаментов на геол. разрезах | **условно** | — | **MISSING_ATTRIBUTE** | нужен `drawing_purpose` / shows_foundations; CV — вне scope |
| 10 | Нет разрезов несущих/ограждающих | **условно** | — | **MISSING_ATTRIBUTE** | обязательные drawing-роли по дисциплине |
| 24 | Наличие AR+KZH в комплекте | **обнаруживается** | `MISSING-SECTION` без KZH | — | **Не** геометрическая увязка |

### Итог по 25 п.п.

| | Строк | п.п. (≈4,2 каждая) | Класс |
|---|---:|---:|---|
| Подтверждено на open/synthetic | **4** (#2, #3, #4, #24) | **≈16,7** | без файлов заказчика |
| MISSING_ATTRIBUTE — условно | **2** (#9, #10) | **≈8,3** | атрибут роли листа / drawing purpose |

**Формулировка для пятницы:** ≈16,7% «обнаруживается» без единого файла заказчика (четыре строки класса полноты); ещё ≈8,3 п.п. (#9+#10) честно условно до атрибутов роли чертежа.

## АР (3 условных) и ВК (13 п.п. федеративная)

| Блок | Вердикт |
|---|---|
| АР #5/#6/#8 (norm-pack + IFC) | **не подтверждено** без RT-002 / customer-approved pack |
| ВК #5/#14 (федеративная модель) | **не подтверждено** — ожидаемо; RT-003 OPEN |

## Артефакты

| Путь | Роль |
|---|---|
| `samples/packages/residential-missing-kzh-inventory.json` | Негатив KR #24 (+ #4 на orphan calc) |
| `samples/packages/residential-tech-spec-missing-topics-inventory.json` | Негатив KR #2 |
| `samples/packages/residential-unjustified-calc-pd-inventory.json` | Негатив KR #4 |
| `samples/packages/residential-complete-inventory.json` | Позитив WP-05 |
| `samples/sections/kzh-*-synthetic.json` | KR #3 section-diff |
| `backend/tests/test_exp_b_completeness_demonstrator.py` | тесты |
| `backend/src/aerobim/domain/package_completeness.py` | rules #2/#4 |

## ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА

1. Пин комплекта **ПНСТ 909** (Renga) в `.local/renga-pnst909/` + ToS note — вход для Exp A и оси 22 сценариев.  
2. Не заявлять «25 п.п. закрыты» — закрыты **≈16,7 п.п.**; #9+#10 = MISSING_ATTRIBUTE → условно.  
3. Rename deferred: `kimi_vlm_drawing_pipeline.py` → neutral при ближайшем касании модуля.  
4. АР: выгрузить СПб+Амур в `.local/` и пересчитать (план SSOT).
