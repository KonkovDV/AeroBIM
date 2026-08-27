<!-- claims-lint: allow-file reason="TZ v1 brief pin; TZ 90%/SLA as evaluation targets not product scores; NO_GO" -->
---
title: "TZ v1 contest brief pin — 6-page public TechLab PDF"
date: "2026-08-27"
last_updated: "2026-08-27"
status: active
version: "1.0.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: tz_v1_brief_coverage
detected_count: 0
claim_boundary: >
  Pin of the public 6-page contest TZ v1. Not product accuracy. Not customer
  SLA. Not the seven comparison tasks. Not a house design TZ. Checkpoint NO_GO.
---

# ТЗ v1 (бриф конкурса) — что это за PDF

Файл на машине владельца: `7. Самолет ТЗ Техлаб 2026.docx-1.pdf` (6 стр., sha256 в машине [`../evidence/tz-v1-brief-coverage-2026-08.json`](../evidence/tz-v1-brief-coverage-2026-08.json)). Бинарь **не** в git.

Это **публичный бриф Задачи** (термины, концепция, критерии, приложения). В репозитории канон ответа — **ТЗ v2** [`TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`](TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) (Часть 0 уже аудирует v1).

**Не склеивать с:**

| Бумага | Этот PDF? |
|---|---|
| ТЗ v2, ТР-1…62 | нет (v2 закрывает TBD и Claims Lock) |
| Семь задач сравнения «ТЗ для Техлаб» | нет |
| Проектное ТЗ объекта (II/C0, ТЭП) | нет |
| Формы МИК (соглашение/акт) | нет |

## Что в шести страницах

Стр. 1 извлечённого текста нет (титул/графика). Стр. 2–6:

1. Термины: OCR, CV («как человек»), NLP, BIM.  
2. Актуальность ручной проверки.  
3. Концепция: ассистент эксперта; 2D+BIM; сверка ПД/РД с расчётами, ТЗ, разделами, нормами. Система не заменяет эксперта.  
4. Цели: коллизии (геометрия + пересечения инженерии); расчётные ошибки (в т.ч. нагрузки); площади; неэффективное пространство; логика (разделы, отсутствующие элементы, размеры); подсветка; замечания с редактированием.  
5. Функции: Office/PDF/DWG/BIM; сравнение версий/типов; CV/OCR/NLP; веб-UI (оверлей, фильтр, приоритет).  
6. Источники: чертежи, BIM, ТЗ RU/EN, внутренние стандарты. Ограничения: скан vs вектор, неструктурированность, мало обучающих данных.  
7. Критерии: коллизии **и** несоответствия — «точность >90%»; качество замечаний RU/EN; SLA «до 30 минут»; удобство UI / снижение когнитивной нагрузки — **не замерены**.  
8. Приложения: ПД, РД, стандарты, проектное ТЗ, типовые ошибки, расчётные модели.  
9. Архитектура, код, образ, презентация, сопр. документы — **TBD в v1** (заполнены в v2).

## Техлаб / МИК (как говорить)

- Стадия программы: **доработка**. КТ#3: 03–21.09. Приз: платный пилот 2 млн ₽ (соглашение Партнёр↔Фонд). ИП не вход.  
- В **акт МИК** идёт interim TP/(TP+FP) ≥ **0.60** по протоколу, не цифра v1 «>90%».  
- M2/M8 формы Фонда: **VERIFY_WITH_OPERATOR**.  
- Семь задач сравнения картографированы отдельно: [`../quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md`](../quality/TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md).

Машина: `python -c "from aerobim.domain.tz_v1_brief import v1_brief_snapshot"` — IUA `SAM-10`. Локальная сверка хэша PDF: переменная `AEROBIM_TZ_V1_PDF` (бинарь не в git).

## Этот проход / дальше

Сделано: pin V1-01…16, IUA `SAM-10`, речь КТ#3 если покажут этот PDF, акт МИК = 0.60 не цифра v1.

Не делается: native DWG/RVT/NWD/LIRA, IDS `customer_approved`, закрытие RT-001/002/003, `summary.passed` от модели, product score по «>90%».

Дальше (владелец): корпус + два разметчика; формы Фонда M2/M8; ИОС IFC или MEP-OOS; стержни или OOS п.7. Карта семи задач: [`../quality/TECHLAB_POST_CARTOGRAPHY_PLAN_2026_08.md`](../quality/TECHLAB_POST_CARTOGRAPHY_PLAN_2026_08.md). Триаж живого дерева 27.08: [`../quality/TZ_LIVE_TREE_TRIAGE_2026_08_27.md`](../quality/TZ_LIVE_TREE_TRIAGE_2026_08_27.md). Исполнение плана: [`../quality/OWNER_AI_PLAN_EXECUTION_2026_08_27.md`](../quality/OWNER_AI_PLAN_EXECUTION_2026_08_27.md).

Checkpoint **`NO_GO`**.
