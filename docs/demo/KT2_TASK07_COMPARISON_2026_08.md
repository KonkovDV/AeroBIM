<!-- claims-lint: allow-file reason="Task 07 comparison; competitor 90%/pilots as their unverified claims; NO_GO" -->
---
title: "КТ#2 — сравнение пяти решений Задачи 07 (поля Анализ 3)"
date: "2026-08-16"
status: active
claim_boundary: >
  Competitive comparison only. Competitor numbers are their public claims
  (card 09.08), not AeroBIM measurements. Not product accuracy. Checkpoint NO_GO.
---

# Пять решений Задачи 07 — одна таблица

Слайд для жюри. Поля — «Анализ 3»: corpus, разметка, P/R/F1, кто ставит verdict, evidence, повторяемость, on-prem, BCF.

Цифры NormaChecker / WAIVE / AIDOX / AI Project Control **не переносим как факт**. Всегда: «покажите методику». Единый протокол сравнения: [`../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md).

Метки: `[Ф]` = публичная карточка/сайт 09.08; `[Н]` = слабо верифицируемо вне карточки МИК; `[репо]` = наш артефакт.

| Поле | AeroBIM | NormaChecker | WAIVE | AIDOX | AI Project Control |
|---|---|---|---|---|---|
| Слой | Пакет: требования↔IFC↔документы↔ревизии + доказательство | Нормоконтроль документа (СП/ГОСТ/сметы) `[Ф]` | Геометрия DWG/сетей на листе `[Ф]` | CV/OCR сканов `[Ф]`/`[Н]` | Широкий контур ТЗ + Yandex Cloud `[Ф]`/`[Н]` |
| Corpus | Fixture + open benches; **нет** ПД+экспертиза Самолёта. SSOT: [`KT2_CORPUS_SSOT_2026_08.md`](KT2_CORPUS_SSOT_2026_08.md) | Не опубликован как adjudication-pack `[Н]` | Не опубликован `[Н]` | Не опубликован `[Н]` | «прототип на данных заказчика» — без pack_hash `[Н]` |
| Разметка TP/FP | n=0 customer; dual-rater в протоколе | Не показано `[Н]` | Не показано `[Н]` | Не показано `[Н]` | Не показано `[Н]` |
| P/R/F1 | macro F1 ≈ 0.86 **fixture GT only**; RT-001 OPEN | «>90%» у карточек МИК **без методики** — не наш факт | то же | то же | то же |
| Кто ставит verdict | Человек. LLM **не** пишет `summary.passed` (ADR-001) | Не заявлено публично `[Н]` | Не заявлено `[Н]` | Риск: VLM в вердикте `[Н]` | Не заявлено `[Н]` |
| Evidence | GUID, expected/observed, evidence_refs, overlay PNG (P1) | Цитаты норм — по карточке `[Ф]`; пакет/ревизия — нет | Картинка на DWG; GUID/evidence refs не показаны `[Ф]` | Зонное чтение скана `[Ф]`/`[Н]` | Не показано `[Н]` |
| Повторяемость | reproducibility_hash + CI pins `[репо]` | Не показано `[Н]` | Не показано `[Н]` | Не показано `[Н]` | Не показано `[Н]` |
| On-prem | Docker offline smoke; пилот = 1 ВМ + static bearer | Заявлено локально / РФ `[Ф]`/`[Н]` | Не проверяли `[Н]` | Закрытый контур **не подтверждён** `[Н]` | Yandex Cloud `[Ф]` |
| BCF | ZIP 2.1/3.0 структурный; импорт в СОД **NOT_VERIFIED** | Не ядро слоя `[Н]` | Не ядро `[Н]` | Не ядро `[Н]` | Не показано `[Н]` |
| Честный проигрыш | Норм-корпус и визуал DWG слабее заявленного у них | Размер норм `[Ф]` | Живая геометрия `[Ф]` | Эффект «ИИ читает скан» `[Ф]` | Ширина слайда `[Ф]`/`[Н]` |

**Контр-ход (дословно):** слои не совпадают. Их пилоты/договоры/«90%» без corpus + TP/FP + методики не сравнимы. Предлагаем одну методику на одном пакете Самолёта — или NO_GO у всех, кто не меряет.

**Базовая линия валидации IFC (не шестой конкурент Задачи 07):** [buildingSMART IFC Validation Service](https://validate.buildingsmart.org/) — schema / info-takeoff / норматив Gherkin. Карта перекрытия: [`../evidence/upstream-validate-overlap-2026-08.md`](../evidence/upstream-validate-overlap-2026-08.md). AeroBIM **не** заявляет, что гоняет официальный сервис. Коммерческий якорь data-validation: [Solibri](https://www.solibri.com/solutions/bim-quality-assurance/data-validation) — в [`../partners/COMPETITIVE_MATRIX_2026_08.md`](../partners/diagrams/04-competitive-matrix.md), не в этой пятиколоночной таблице.

Checkpoint **NO_GO**. RT-001/002/003 OPEN.
