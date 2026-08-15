<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# Jury pack — критерии мышления жюри МИК / Техлаб (верхний слой)

**Дата:** 2026-08-05  
**Назначение:** модель мышления жюри и материалы трекера — **не** заявка «Новатор Москвы» 2026 (цикл подачи закрыт; следующая возможная подача февраль–май 2027).  
**Номинация (если цикл 2027):** «Меняющие реальность» · направление «Благоустройство и строительство»  
**Checkpoint продукта:** по-прежнему **NO_GO** (RT-001/002/003) — это не оценка «код мёртв».

## Читать в этом порядке (15 минут эксперта)

0. [`../quality/TRACKER_MEETING_PACK_2026_08_07.md`](../quality/TRACKER_MEETING_PACK_2026_08_07.md) — **К0** к трек-встрече 07.08  
1. [`PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md`](PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md) — **протокол измерения и приёмки задачи №7** (для ТИМ-руководителя)  
2. [`FOUR_CHECK_STATES_OPERATOR_2026_08.md`](FOUR_CHECK_STATES_OPERATOR_2026_08.md) — пять операторских состояний карты покрытия (+ исходы пакета)  
3. [`OPEN_DEMO_BEFORE_CUSTOMER_CORPUS_2026_08.md`](OPEN_DEMO_BEFORE_CUSTOMER_CORPUS_2026_08.md) — демо на открытых данных  
4. [`TZ_TBD_PROPOSALS_TASK07_2026_08.md`](TZ_TBD_PROPOSALS_TASK07_2026_08.md) — предложения к TBD (не «ТЗ v2»)  
5. [`../qa-defense-2026.md`](../qa-defense-2026.md) — заготовки ответов 20–30 с  
6. [`COMPETITIVE_MATRIX_2026_08.md`](COMPETITIVE_MATRIX_2026_08.md)  
7. [`_TECHLAB_2026_08.md`](_TECHLAB_2026_08.md) — **15.08:** первые 15 с = NO_GO; не раунд  
7a. [`../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md`](../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md) — атаки венчура / diligence  
8. [`ROADMAP_3Y_2026_08.md`](ROADMAP_3Y_2026_08.md)  
9. [`diagrams/README.md`](diagrams/README.md) — 4 схемы  
10. [`GLOSSARY_JURY_RU_2026_08.md`](GLOSSARY_JURY_RU_2026_08.md)  
11. [`../docs.md`](../docs.md) · [`../ENGINEERING_STATUS_2026_08.md`](../ENGINEERING_STATUS_2026_08.md)

## Вне репозитория (критично для баллов)

| Действие | Критерий | Статус в репо |
|---|---|---|
| Заявка РИД: программа для ЭВМ (+ опц. БД правил) | 1.3 | [`IP_REGISTRATION_CHECKLIST_2026_08.md`](IP_REGISTRATION_CHECKLIST_2026_08.md) |
| Строительный эксперт в команду (имя, стаж) | 2.6 / защита | **не закрывается текстом** |
| Подписанное LOI Самолёта | 3.7 | [`LETTER_OF_INTEREST_SAMOLET_TEMPLATE_2026_08.md`](LETTER_OF_INTEREST_SAMOLET_TEMPLATE_2026_08.md) |
| Препринт / Habr / пресс | 2.8 | Реестр: [`PRESS_MENTIONS_REGISTRY_2026_08.md`](PRESS_MENTIONS_REGISTRY_2026_08.md) — СМИ 03.08 = программа, не проект; нужны B1/B2 собственные статьи |
| Фонд внедрения / рамка пилота | — | **20 млн ₽ на 10 задач**; 2 млн = доля задачи / платный пилот; цель — **коммерческое соглашение с партнёром** (не грант) |
| Сегмент E (другие девелоперы-партнёры программы) | коммерция | Только через оператора: `.local/commercial-ops/SEGMENT_E_…` (имена — не в публичном пакете) |
| 4 схемы (контур, provenance, fail-closed, матрица) | 2.4 | [`diagrams/README.md`](diagrams/README.md) — Mermaid; экспорт PNG перед PDF-заявкой |

## Claims Lock (не снимать)

Не заявлять: точность >90%, MEP delivered, CDE-ready, SLA ≤30 мин на customer, «окупаемость доказана» без пилота.

## Честная карта баллов (модель мышления, не бланк 2026)

Новатор-2026 **не подаём**. Если жюри Техлаба думает теми же осями (RBC demo days: команда, новизна, проблема, масштаб, конкуренция, презентация, защита, рынок):

| Ось | Балл 0–2 | Почему не 2 |
|---|---|---|
| Соответствие задаче №7 | 1 | Fixture-путь IFC+PDF+IDS есть; корпуса Самолёта нет |
| НТ новизна (гибрид + fail-closed) | 1 | Архитектура реальна; не уникальный ров против in-house |
| Презентация / демо | 1 | Live CLI выживает; snapshot HTML 11.08 — ловушка |
| Честность / защита | 2 | NO_GO в первые 15 с |
| Валидация эффективности (МИК этап 3) | **0** | Нет размеченного комплекта |
| Внедрение (МИК этап 4) | **0** | CDE import NOT_VERIFIED; юрлица нет |
| Команда / строитель (2.6) | 0–1 | Только факты; не выдумывать CV |
| Коммерциализация | 1 | MIT + услуги; нет LOI |
| РИД (1.3) | 0 | Чеклист есть, номера заявки в git нет |
| Номинация «Лидеры инноваций» | **0** | Нет юрлица и выручки. Максимум 2027: «Меняющие реальность» |

Не усреднять эту таблицу в «точность продукта». Полный attack tree: [`../quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md`](../quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md).
