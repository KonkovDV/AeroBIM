---
title: "Поле «Дополнительные материалы» — доказательства и самопроверка"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
claim_boundary: >
  Supporting evidence index. Open benches and fixtures are not the customer
  корпус. Checkpoint NO_GO; RT-001/002/003 OPEN.
---

# Дополнительные материалы

## 1. Доказательства прогонов

[`../../docs/evidence/`](../../docs/evidence/) — артефакты с датами, хешами и указанием, чем они **не** являются.

| Материал | Что показывает |
|---|---|
| [`../../docs/evidence/kt2-handoff-2026-08-11/README.md`](../../docs/evidence/kt2-handoff-2026-08-11/README.md) | Пакет передачи КТ#2 с самопроверкой |
| [`../../docs/evidence/ids-fail-closed-2026-08.md`](../../docs/evidence/ids-fail-closed-2026-08.md) | Поведение IDS-контура при пропусках |
| [`../../docs/evidence/drawing-overlay-smoke-2026-08/README.md`](../../docs/evidence/drawing-overlay-smoke-2026-08/README.md) | Наложение ошибки на чертёж |
| [`../../docs/evidence/renga-export-probe-2026-08.md`](../../docs/evidence/renga-export-probe-2026-08.md) | Проба выгрузки Renga (стек заказчика) |
| [`../../docs/evidence/DATA_STATEMENT_2026_08.md`](../../docs/evidence/DATA_STATEMENT_2026_08.md) | Происхождение данных |

## 2. Датасеты и открытые прокси

[`../../docs/demo/KT2_CORPUS_SSOT_2026_08.md`](../../docs/demo/KT2_CORPUS_SSOT_2026_08.md) — замороженная строка цифр открытых прокси. Корпусом заказчика они не являются.

Открытые наборы служат регрессией и репетицией движка. Корпусом заказчика они не являются, и в них нет разметки TP/FP от инженеров «Самолёта» — поэтому RT-001 остаётся открытым.

## 3. Самопроверка (красная команда)

Серия внутренних состязательных аудитов за 16.08 с реестром находок:

| Отчёт | Вектор |
|---|---|
| [`../../docs/quality/RED_TEAM_FINAL_VERDICT_2026_08_16.md`](../../docs/quality/RED_TEAM_FINAL_VERDICT_2026_08_16.md) | Итоговый вердикт серии |
| [`../../docs/quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md`](../../docs/quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md) | Атаки со стороны жюри |
| [`../../docs/quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](../../docs/quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md) | Академическая корректность заявлений |
| [`../../docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md`](../../docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md) | Принятые риски с обоснованием |

Мы публикуем собственные найденные слабости. Это осознанная позиция: проверяемость важнее гладкой картинки.

## 4. Рынок и позиционирование

| Документ | Содержание |
|---|---|
| [`../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md`](../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md) | Пять решений Задачи 07 по одинаковым полям |
| [`../../docs/partners/COMPETITIVE_MATRIX_2026_08.md`](../../docs/partners/COMPETITIVE_MATRIX_2026_08.md) | Мировые и российские аналоги |
| [`../../docs/partners/ROADMAP_3Y_2026_08.md`](../../docs/partners/ROADMAP_3Y_2026_08.md) | Дорожная карта |
| [`../../docs/demo/KT2_10D_INTAKE_CONTRACT_2026_08.md`](../../docs/demo/KT2_10D_INTAKE_CONTRACT_2026_08.md) | Предлагаемая граница с СОД заказчика |

## 5. Академический контур

[`../../docs/quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md`](../../docs/quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md) — разбор литературы 2026 года и того, что из неё применимо. [`../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md`](../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md) — журнал допустимых интерпретаций: что конкретный замер вправе означать, а что нет.

Цитирование проекта: [`../../CITATION.cff`](../../CITATION.cff).
