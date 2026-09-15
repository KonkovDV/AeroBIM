<!-- claims-lint: allow-file reason="Submission index quoting TZ evaluation targets as non-claims; Checkpoint GO; customer_go false" -->
---
title: "КТ#3 — пакет подачи (Техлаб Москва, задача заказчика канала по верификации ПД/РД)"
status: active
version: "1.3.0"
last_updated: "2026-09-15"
claim_boundary: >
  Submission index only. TZ criteria (>90%, до 30 минут) are the customer's
  evaluation targets, not AeroBIM measurements. Checkpoint GO; customer_go false;
  RT-001/002/003 OPEN. RT-002a CLOSED regulatory / RT-002b CLOSED EIR carrier /
  RT-002c OPEN signed.
---

# Пакет подачи КТ#3

**Команда:** AeroBIM · **Задача:** 07 «Система автоматизированной верификации проектной и рабочей документации» · **Заказчик канала:** в публичном дереве не называется · **Окно КТ#3:** 03–21.09.2026 · **Демо-день / финал:** 29–30.09.2026 · **Архив КТ#2:** 20.08.2026

**Checkpoint: `GO` (`regulatory_measurement_mvp`).** `customer_go` **false**. Не прячем остаток приёмки. Стадия МИК — **доработка**. Остатки RT-001b / RT-002c / RT-003b закрываются только доказательствами заказчика (RT-002a = публичные IDS; RT-002b = EIR v4 как текст на канале): [реестр блокеров](../audit/reports/CRITICAL_BLOCKERS.md).

**Объект КТ#2.** Речь и пакет = текущий `main`. Цифры тестов = CI pin в [`docs/evidence/runtime-baseline-latest.json`](../docs/evidence/runtime-baseline-latest.json) (`attested_by=ci`: `commit_sha`, `tests_passed`, `tests_collected`). IUA freeze `f9389bf` (не HEAD). Прочие SHA на поверхностях — исторические. После правок документации pin может отставать на несколько коммитов до следующего прогона CI; локальные прогоны pytest не публикуем.

**Объект КТ#3 (без файлов заказчика в git).** Пакет показа не ждёт `samples/customer/`. Показ — живой CLI: `python -m aerobim.tools.run_kt3_jury`. Пакет без ожидания: `python -m aerobim.tools.run_kt3_without_customer`. Речь: [`../docs/demo/KT3_JURY_FAQ_2026_08_25.md`](../docs/demo/KT3_JURY_FAQ_2026_08_25.md). Замок речи демо-дня: [`../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md). Текст семи экранов: [`03-presentation/demo_day_slides.md`](03-presentation/demo_day_slides.md). Трекер: [`../docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md`](../docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md). Сценарий: [`../docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md`](../docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md). Review shell: `frontend/` (RBAC лаборатории ≠ SSO; PDF-кнопка = реальный `GET .../export/pdf`; XLSX нет). RT-001 **OPEN** (undifferentiated; `a_content_pairing` CLOSED). RT-002a **CLOSED** (публичные IDS) / RT-002b **CLOSED** (EIR v4 как текст) / RT-002c **OPEN** (подпись). RT-003 **OPEN** (undifferentiated; `a_federated_geometric_rehearsal` CLOSED; NWD-носитель CLOSED; `mep_system_clash` OPEN). Тома: [реестр блокеров](../audit/reports/CRITICAL_BLOCKERS.md).

## Пять полей формы → пять папок

| Поле формы | Папка | Что открыть первым |
|---|---|---|
| **Репозиторий** \* | [`01-repository/`](01-repository/README.md) | Структура, сборка, лицензия, CI |
| **Документация** \* | [`02-documentation/`](02-documentation/README.md) | Техобоснование + матрица ТЗ + границы заявлений |
| **Презентация** \* | [`03-presentation/`](03-presentation/README.md) | [`AeroBIM_demo_day.pdf`](03-presentation/AeroBIM_demo_day.pdf) · [`demo_day_slides.md`](03-presentation/demo_day_slides.md) · [`aerobim_kt2.pptx`](03-presentation/aerobim_kt2.pptx) |
| **Прототип** \* | [`04-prototype/`](04-prototype/README.md) | Команды запуска, живой CLI, веб-интерфейс |
| **Дополнительные материалы** | [`05-additional/`](05-additional/README.md) | Доказательства, датасеты, границы цифр, конкуренты |

Ссылка на репозиторий для всех пяти полей: **https://github.com/KonkovDV/AeroBIM** (доступ по ссылке открыт, лицензия MIT).

## Покрытие требований ТЗ

Полная построчная карта — [покрытие требований ТЗ](TZ_REQUIREMENTS_COVERAGE_2026_08.md). Снимок возможностей на учебной стенке: [`../docs/evidence/tz-matrix-status-latest.json`](../docs/evidence/tz-matrix-status-latest.json) (`ids=ok` на фикстуре ≠ закрытый профиль заказчика).

| Раздел ТЗ | Где закрыт | Честный остаток |
|---|---|---|
| Термины (OCR / CV / NLP / BIM) | [матрица соответствия ТЗ](../docs/tz/TZ_COMPLIANCE_MATRIX_2026.md) §1 | CV в вердикте нет — только подсказка |
| Концепция (ассистент, не замена) | [техобоснование](../docs/docs.md) | — |
| Целевые задачи (графика, сверка, ошибки) | матрица §2–4 | расчётного решателя нет — сверка |
| Функциональность (загрузка, анализ, AI, UI) | [прототип](04-prototype/README.md) | чтение DWG / RVT / NWD без конвертации — `NOT_IMPLEMENTED` |
| Источники и ограничения | [приложение ТЗ](../samples/tz-appendix/README.md) | корпус заказчика — RT-001 OPEN |
| Критерии оценивания | [покрытие требований ТЗ](TZ_REQUIREMENTS_COVERAGE_2026_08.md) §6 | целевые значения ТЗ **не измерены** на комплекте заказчика |

## Шесть столов — одна строка каждый

| Стол | Одна фраза |
|---|---|
| Техлаб | Доработка. Живой CLI. Учебный комплект. Checkpoint `GO`; `customer_go` false. |
| МИК | Стадия доработки. Валидация эффективности не начата. Пять полей формы — не акт Checkpoint. |
| Трекер | Tangl = модель, мы = комплект. Задачи 1–3 в репо; письмо заказчику канала отправляет человек, а не репозиторий. |
| Review shell | Пропуск IDS роняет комплект. CI pin = `runtime-baseline-latest.json`. Отставание pin на несколько коммитов принято. |
| Наука | Kane: на учебном комплекте цифры про содержание — да; про заказчика канала — нет. Заморозка `f9389bf`. |
| Венчур | Юрлица в пакете нет и дату регистрации не выдумываем. Слот + комплект, не SAFE. Backlog — GitHub Issues, не диаграмма Ганта. |

## Демо-день 29–30.09 — что открыть

| Материал | Роль |
|---|---|
| [`03-presentation/demo_day_slides.md`](03-presentation/demo_day_slides.md) | Семь экранов. Дека 13.09 с рабочего стола не показывать |
| [`../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md) | Лицензированные числа и запреты |
| [`04-prototype/README.md`](04-prototype/README.md) | `python -m aerobim.tools.run_kt3_jury` |
| [`05-additional/README.md`](05-additional/README.md) | Пины: учебный p95, синтетический recall, Docker-контур, хранение |

Публичное дерево не содержит выгрузки заказчика и не называет назначающую сторону. Локальные шаблоны NDA в git не входят.

## Что мы не заявляем

Точность продукта на комплекте заказчика; выполненный SLA заказчика; чтение DWG / RVT / NWD без конвертации; сданный MEP system clash; доказанный импорт BCF в СОД; независимую корректность расчётов; production-статус. Флаг `sla_pass` на учебной фикстуре — не SLA заказчика. Десять из десяти убитых мутаций на стенке+IDS — не полнота продукта.

Формула стадии (дословно; источник — [карточка речи для жюри](../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):

> Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.
