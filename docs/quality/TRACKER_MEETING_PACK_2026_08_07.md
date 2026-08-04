---
title: "Пакет к трек-встрече 07.08.2026 (К0)"
date: 2026-08-04
status: active
claim_boundary: >-
  Инженерный и процессный пакет для трекера. Не точность продукта, не закрытие
  RT-001/002/003, не customer SLA ≤30 мин, не «>90%».
---

# Пакет к трек-встрече — 07.08.2026, 08:00

**Адресат:** Д. Сигиневич (трекер Техлаба)  
**Checkpoint:** **NO_GO** (RT-001 / RT-002 / RT-003 открыты)  
**Приз:** оплачиваемый пилот — предмет продажи = исполняемый протокол, не «набор фич»

## Чеклист трекера (спринт 2)

| # | Запрос трекера | Статус | Артефакт |
|---|---|---|---|
| 1 | Baseline **PDF** + соотнесение с критериями ТЗ | **готово к выкладке** | [`../evidence/tracker-baseline-2026-08-07.pdf`](../evidence/tracker-baseline-2026-08-07.pdf) · [`.md`](../evidence/tracker-baseline-2026-08-07.md) |
| 2 | Список 30+ потенциальных заказчиков | **SSOT 28 орг.; контакты ЛПР — нет** (цель трекера 30+ ещё не добита) | локально: `.local/commercial-ops/commercial-pipeline.csv` (не в GH) |
| 3 | Факт контактов (отправлено / ответили / демо) | **0 / 0 / 0** | локально: `.local/commercial-ops/outreach-log.md` (не в GH) |
| 4 | Сценарий демо: завершённый проект → прогон → сравнение с экспертизой | **техпротокол готов**; `demo-format` ещё draft | [`../customer-demo/completed-project-comparison-protocol.md`](../customer-demo/completed-project-comparison-protocol.md) · [`DEMO_SCENARIO_TRACKER_RU_2026_08.md`](../customer-demo/DEMO_SCENARIO_TRACKER_RU_2026_08.md) · draft [`../customer-discovery/demo-format-2026-08.md`](../customer-discovery/demo-format-2026-08.md) |

**Текст в чат + 45 с открытия:** [`TRACKER_FRIDAY_OPENING_2026_08_07.md`](TRACKER_FRIDAY_OPENING_2026_08_07.md)

## Что сказать за 60 секунд

1. Измерили **открытый** бенчмарк AECV (чужой протокол): **0,4325** — рядом с Claude Opus 4.5 (0,42), ниже Gemini 3 Pro (0,51); это **не** точность продукта.  
2. На fixture-комплекте wall-clock p95 ≈ **0,53 с** — это **не** SLA заказчика.  
3. Синтетический detection baseline: P=0,75 / R=1,0 на 6 посаженных дефектах — **не** закрывает RT-001.  
4. Коммерческий трек: **SSOT 28 организаций** (`.local/commercial-ops/commercial-pipeline.csv`); исходящие контакты = **0** — нужен оператор на обзвон/письма.  
5. Предлагаем Самолёту **общий** протокол измерения «>90%» для всех пяти команд (К1 уже в репо).

## ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА до 07.08

1. Кто из двоих делает outreach и когда (хотя бы 10 писем до пятницы).  
2. Заполнить таблицу контактов после реальных отправок.  
3. Подтвердить/опровергнуть цифру «~11 ₽ за 100 замечаний» — в evidence зафиксировано **~111 ₽** на Wilson-выборку n≈111; **11 ₽ в PDF не публикуем**.  
4. Выложить PDF + CSV + факт контактов в чат «ТМ // AeroBIM» до 08:00 пятницы.

## Уже есть (К1–К6, локально; не путать с К0)

| ID | Файл |
|---|---|
| К1 | `docs/partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md` |
| К2–К3 | CoverageMapPanel + пять операторских состояний карты |
| К4 | `docs/partners/OPEN_DEMO_BEFORE_CUSTOMER_CORPUS_2026_08.md` |
| К6 | `docs/partners/TZ_TBD_PROPOSALS_TASK07_2026_08.md` |
| Защита | `docs/qa-defense-2026.md` |
