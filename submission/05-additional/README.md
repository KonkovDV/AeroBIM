# Дополнительные материалы

> Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

| Материал | Роль |
|---|---|
| [`DATA_STATEMENT_2026_08.md`](../../docs/evidence/DATA_STATEMENT_2026_08.md) | Какие данные есть и каких нет |
| [`ids-fail-closed-2026-08.md`](../../docs/evidence/ids-fail-closed-2026-08.md) | Пропуск обязательной проверки IDS роняет комплект |
| [`INTERPRETATION_USE_LEDGER_2026_08.md`](../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Что текущие цифры вправе значить |
| [`QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | Методика до данных заказчика |
| [`AeroBIM.pptx`](../03-presentation/AeroBIM.pptx) | Поле формы; PowerPoint демо-дня (7 слайдов) |
| [`AeroBIM.pdf`](../03-presentation/AeroBIM.pdf) | Та же дека, PDF |
| [`demo_day_slides.md`](../03-presentation/demo_day_slides.md) | Текстовая копия слайдов показа |

## Цифры кадра 3

| Число на слайде | Где в git | Чем не является |
|---|---|---|
| macro F1 0,86 | [`runtime-baseline-latest.json`](../../docs/evidence/runtime-baseline-latest.json) | точность продукта |
| 10 из 10 | [`DEFECT_INJECTION_RECALL_SEAM_CLEAN_2026_09.md`](../../docs/evidence/DEFECT_INJECTION_RECALL_SEAM_CLEAN_2026_09.md) | полнота на комплекте заказчика |
| 1 из 8 | [`DEFECT_INJECTION_RECALL_RUN_2026_09.md`](../../docs/evidence/DEFECT_INJECTION_RECALL_RUN_2026_09.md) | тот же знаменатель, что 10/10 |
| IDS fail-closed | [`ids-fail-closed-2026-08.md`](../../docs/evidence/ids-fail-closed-2026-08.md) | SLA заказчика |

## Пины (учебные и синтетические)

| Пин | Чем является | Чем не является |
|---|---|---|
| [`sla-package-scale-latest.json`](../../docs/evidence/sla-package-scale-latest.json) | Учебный p95 на стенке+IDS | SLA заказчика |
| [`defect-injection-recall-run-latest.json`](../../docs/evidence/defect-injection-recall-run-latest.json) | Синтетические убитые мутации | Полнота продукта |
| [`tz-matrix-status-latest.json`](../../docs/evidence/tz-matrix-status-latest.json) | Снимок возможностей на учебной фикстуре | Закрытие ТЗ заказчиком |
| [`offline-bundle-trial-latest.json`](../../docs/evidence/offline-bundle-trial-latest.json) | Пробный Docker-контур | Данные заказчика |

Открытые наборы — регрессия движка, не разметка инженеров заказчика.
