---
title: "Инструкция двойной слепой разметки для экспертов-адjudicators"
status: active
version: "1.0.0"
last_updated: "2026-07-24"
claim_boundary: "Instruction only. LLM is not an adjudicator. Customer κ/α unpublished until RT-001 corpus."
---

# Инструкция для двух экспертов-разметчиков (Task 07)

## Назначение

Независимая разметка замечаний AeroBIM на согласованном комплекте. Результат — журнал TP / FP / FN, согласие Cohen’s κ / Krippendorff’s α, interim precision **TP/(TP+FP) ≥ 0.60** (порог согласовать письменно).

## Правила независимости (двойная слепая)

1. Эксперт A и эксперт B **не** видят метки друг друга до adjudication.
2. Эксперты **не** используют LLM / чат как «третьего adjudicator».
3. Оба работают по одному freeze комплекта (хэши файлов + версия кода в evidence-бандле).
4. Расхождения снимает **adjudication meeting** (третий эксперт или заказчик-sponsor); итог пишется в CSV/JSON с `adjudication_status`.
5. Baseline ручной проверки (часы, итерации, замечания, возвраты) фиксируется **до** или параллельно прогону, но не подгоняется под вывод системы.

## Классы ошибок (finding_class)

| Класс | Описание | Типичный источник доказательства |
|-------|----------|----------------------------------|
| `clash` | Геометрическая / clearance коллизия | IFC GUID(s), clash id, матрица |
| `attribute` | Атрибут / IDS / свойство | IFC entity + pset + property |
| `dimension` | Размер / габарит | Лист + annotation / IFC quantity |
| `area` | Площадь / ТЭП | Space / quantity compare |
| `cross_document` | ПД↔РД / ТЗ / расчёт vs модель | Пара документов + цитата / число |
| `missing_element` | Отсутствующий элемент по правилу | IDS `exists` / rule_id |
| `other` | Только с явной пометкой в notes | — |

Не смешивать классы в одной метке: при сомнении выбрать один primary + note.

## Уровни серьёзности

| Уровень | Когда | Влияние на Shared-gate |
|---------|-------|-------------------------|
| **Critical** | Блокирует приёмку / безопасность / обязательный критерий scope | Может блокировать PASS при fail-closed профиле |
| **Warning** | Существенное замечание, не обязательно stop | Не выдаёт «зелёный» без provenance |
| **Info** | Наблюдение / advisory / incomplete evidence | Не positive verdict |

Severity эксперта может отличаться от severity системы — фиксировать оба при adjudication.

## Вердикты разметки

| Verdict | Смысл |
|---------|--------|
| **TP** | Система права: ошибка/пропуск реальны относительно согласованного правила |
| **FP** | Система ошиблась: замечание неверно или вне scope |
| **FN** | Система пропустила: эксперт нашёл проблему, которой нет в detections (добавить в labels) |
| **excluded** | Вне scope memo / дубль / неразмечиваемо — не в precision |
| **unresolved** | Требует adjudication; **не** публиковать как adjudicated dataset |

## Процедура одного item

1. Открыть finding (или FN-кандидат из baseline).
2. Проверить **источник доказательства**: файл, лист, GUID, clause, число.
3. Сверить с **утверждённым** правилом / IDS / scope memo (не «по ощущению СП»).
4. Выставить `verdict` + `finding_class` + optional severity override + notes.
5. Записать в CSV по шаблону `samples/benchmarks/detection-precision/adjudication-template.csv`.

Колонки минимум: `match_key`, `adjudicator_id`, `verdict`, `notes`, `timestamp`.

## Adjudication и κ

```bash
cd backend
python -m aerobim.tools.measure_adjudicator_agreement \
  --csv ../samples/benchmarks/detection-precision/<pilot>-adjudication.csv
```

Целевой старт: κ ≥ 0.60 (согласовать). Конвенция Krippendorff’s α: ≥ 0.67 —
tentatively useful; ≥ 0.80 — предпочтительный порог для публикации (content-analysis
practice; не заменяет письменное согласование с Самолётом). При κ/α ниже порога —
уточнить инструкции классов, не «подкручивать» метки.

После согласия пары → `build_detection_labels` / labels JSON со `dataset_status=adjudicated` (≥2 adjudicators, без unresolved).

## Baseline (обязателен для экономического эффекта)

| Метрика | Как снять |
|---------|-----------|
| Время ручной проверки комплекта | Часы двух экспертов (одинаковый scope) |
| Число итераций / возвратов | Журнал проектного офиса |
| Число замечаний до AeroBIM | Baseline list |
| Время до первой находки (TFF) | Секунды от старта прогона до первого Critical/Warning TP |
| Время полного прогона | Wall-clock evidence-бандла |

## Что не размечаем как TP

- Замечание без provenance (файл/лист/элемент).
- Правило из **неутверждённого** norm pack.
- Fixture / synthetic findings как customer evidence.
- Advisory OCR/VLM без подтверждённого rule_id в scope.

## Чеклист готовности инструкции

- [ ] Scope memo подписан (дисциплины, стадии, in/out)
- [ ] Два именованных adjudicator_id
- [ ] Freeze комплекта + хэши
- [ ] Шаблон CSV/JSON согласован
- [ ] Пороги κ и TP/(TP+FP) письменно согласованы
- [ ] Канал adjudication назначен
