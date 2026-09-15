---
title: "Поле «Презентация» — дека, речь, запреты"
status: active
version: "1.3.0"
last_updated: "2026-09-15"
claim_boundary: >
  Form-field binary remains aerobim_kt2.pptx / aerobim_kt2.pdf (KT#2).
  Demo-day 29–30.09 slide copy is demo_day_slides.md. Speech lock is
  docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md. Video not recorded.
  Checkpoint GO; customer_go false; RT-001 OPEN; RT-002a CLOSED
  regulatory / RT-002b CLOSED EIR carrier / RT-002c OPEN signed; RT-003 OPEN.
---

# Презентация

**Демо-день 29–30.09 — текст семи экранов:** [`demo_day_slides.md`](demo_day_slides.md).
Замок речи: [`../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md).
Красная черта деки 13.09: [`../../docs/quality/DEMO_DAY_DECK_REDLINE_2026_09.md`](../../docs/quality/DEMO_DAY_DECK_REDLINE_2026_09.md) — сверка, не кадр.
Дека 13.09 на рабочем столе устарела — её не показывать. Бинарь в git этим файлом не переписывается.

**Дека для поля формы (бинарь с меткой КТ#2, 20.08):** [`aerobim_kt2.pptx`](aerobim_kt2.pptx) · [`aerobim_kt2.pdf`](aerobim_kt2.pdf).
Текстовый каркас КТ#2 — [`slides.md`](slides.md). Если бинарь отсутствует в
клоне, для речи использовать FAQ, не выдумывать слайды.

Речь КТ#3 (карточка, не слайд-файл): [`../../docs/demo/KT3_JURY_FAQ_2026_08_25.md`](../../docs/demo/KT3_JURY_FAQ_2026_08_25.md) · runbook: [`../../docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md`](../../docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md). Ролик 2–3 мин **не записываем и не прилагаем.** Показ КТ#2 — `python -m aerobim.tools.run_demo_ifc_acceptance_gate`. Показ демо-дня — `python -m aerobim.tools.run_kt3_jury`. Живой CLI, не mp4 и не снимок HTML.

## Каркас слайдов

Дека в форме — **12 слайдов** в [`aerobim_kt2.pptx`](aerobim_kt2.pptx) / [`aerobim_kt2.pdf`](aerobim_kt2.pdf). Таблица ниже — опорный каркас речи КТ#2, не покадровый дубль. На 29–30.09 в зале — семь экранов из [`demo_day_slides.md`](demo_day_slides.md).

| № | Слайд | Обязательный тезис |
|---|---|---|
| 1 | Проблема | Комплект расходится сам с собой; ручная сверка. Не обещаем полный контроль всей документации |
| 2 | Решение | Ассистент приёмки: требование → объект → доказательство. Эксперт остаётся ответственным |
| 3 | Архитектура | Четыре контура; вердикт ставит детерминированный движок, ИИ только подсказывает (ADR-001) |
| 4 | Демонстрация | Команда в терминале: IFC + IDS → находка с GUID, правилом, expected/observed → HTML/JSON/BCF |
| 5 | Методика | Как мы будем мерить качество на комплекте заказчика (протокол опубликован заранее) |
| 6 | Конкуренты | Сравнение пяти решений задаче заказчика канала по верификации ПД/РД по одинаковым полям |
| 7 | Статус | Стадия доработки, Checkpoint `GO`, четыре пункта запроса к заказчику |
| 8 | Дорожная карта | Что закрывает КТ#3 и пилот |

Развёрнутые требования к деке: [`../../docs/tz/TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md`](../../docs/tz/TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md) §2–4.

## Речь

| Материал | Назначение |
|---|---|
| [`../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md) | Лицензированные числа 29–30.09; красная черта атак |
| [`../../docs/demo/KT2_JURY_FAQ_2026_08_12.md`](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md) | Формула стадии дословно; списки «можно / нельзя говорить» |
| [`../../docs/qa-defense-2026.md`](../../docs/qa-defense-2026.md) | Заготовки ответов на защиту |
| [`../../docs/partners/GLOSSARY_JURY_RU_2026_08.md`](../../docs/partners/GLOSSARY_JURY_RU_2026_08.md) | Термины для нетехнического члена жюри |

Ролик 2–3 мин **не записываем и не прилагаем.** Показ — живой CLI: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`. Демо-день: `python -m aerobim.tools.run_kt3_jury`.

Формула стадии (дословно):

> Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

**Первым делом, не дожидаясь вопроса:** штамп с листа в облако не отправляется; облачная модель видит только вырезанный фрагмент после клипа основной надписи.

## Источник цифр

Единственная строка корпуса, заморожена до 20.08: [`../../docs/demo/KT2_CORPUS_SSOT_2026_08.md`](../../docs/demo/KT2_CORPUS_SSOT_2026_08.md). Время на фикстуре: [`../../docs/demo/KT2_FIXTURE_TIMING_2026_08_16.md`](../../docs/demo/KT2_FIXTURE_TIMING_2026_08_16.md) — порядок величины, не SLA. Учебный p95 с честным масштабом inventory: [`../../docs/evidence/sla-package-scale-latest.json`](../../docs/evidence/sla-package-scale-latest.json) — не SLA заказчика.

Сравнение решений: [`../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md`](../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md). Цифры конкурентов — их публичные заявления, не наш измеренный факт.

## Запрещено в кадре и в голосе

- точность >90%
- выполненный SLA ≤30 мин на комплекте заказчика
- экономия ≥20%
- native DWG
- MEP delivered
- интеграция с Tangl / 10D
- CDE-ready BCF
- «ИИ понимает чертёж как инженер»
- Customer GO
- УГТ-5 / TRL 5 как заявленный уровень
- «ИИ не нужна»
- выдуманная фамилия валидатора
- дата регистрации юрлица
- диаграмма Ганта вместо GitHub Issues
- `sla_pass` на учебной фикстуре как SLA заказчика
- десять из десяти мутаций как полнота продукта

Полный реестр: [`../../docs/capability-claim-matrix-2026.md`](../../docs/capability-claim-matrix-2026.md). Нарушение ловится `scripts/lint_claims.py` в CI.
