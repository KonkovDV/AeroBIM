<!-- claims-lint: allow-file reason="Submission index quoting TZ evaluation targets as non-claims; Checkpoint GO; customer_go false" -->

# Пакет подачи — Техлаб Москва

**Команда:** AeroBIM · **Задача:** автоматизированная верификация проектной и рабочей документации · **Демо-день:** 29–30.09.2026

**Ссылка на репозиторий:** https://github.com/KonkovDV/AeroBIM (публичный, MIT).

Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` **false**. Стадия — **доработка**.

> Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

## Пять полей формы

| Поле | Папка | Что открыть |
|---|---|---|
| Репозиторий | [`01-repository/`](01-repository/README.md) | Сборка, лицензия, CI |
| Документация | [`02-documentation/`](02-documentation/README.md) | Техобоснование и матрица ТЗ |
| Презентация | [`03-presentation/`](03-presentation/README.md) | [`demo_day_slides.md`](03-presentation/demo_day_slides.md); [`AeroBIM_demo_day.pdf`](03-presentation/AeroBIM_demo_day.pdf) |
| Прототип | [`04-prototype/`](04-prototype/README.md) | Команда запуска |
| Дополнительно | [`05-additional/`](05-additional/README.md) | Доказательства и границы цифр |

Построчная карта ТЗ: [`TZ_REQUIREMENTS_COVERAGE_2026_08.md`](TZ_REQUIREMENTS_COVERAGE_2026_08.md). Цифры тестов CI — [`docs/evidence/runtime-baseline-latest.json`](../docs/evidence/runtime-baseline-latest.json).

Показ: `python -m aerobim.tools.run_kt3_jury` на учебном комплекте из git. Файлов заказчика в репозитории нет.

## Что не заявляем

- точность продукта на комплекте заказчика
- выполненный SLA заказчика
- чтение DWG / RVT / NWD без конвертации
- сданный clash инженерных систем
- доказанный импорт BCF в СОД
- независимость расчётов
- production-статус

Пороги ТЗ (в том числе точность свыше 90 процентов и обработка комплекта за полчаса) — критерии заказчика, **не** наш замер.
