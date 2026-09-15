---
title: "Поле «Дополнительные материалы» — доказательства"
status: active
version: "1.1.0"
last_updated: "2026-09-15"
claim_boundary: >
  Supporting evidence index. Open benches and fixtures are not the customer
  корпус. Checkpoint GO; customer_go false; RT-001/002/003 OPEN.
---

# Дополнительные материалы

**Формула стадии (дословно; источник — [карточка речи для жюри](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

Индекс всех citeable пинов: [`../../docs/evidence/README.md`](../../docs/evidence/README.md).

| Материал | Роль |
|---|---|
| [`../../docs/evidence/DATA_STATEMENT_2026_08.md`](../../docs/evidence/DATA_STATEMENT_2026_08.md) | Какие данные есть и каких нет |
| [`../../docs/evidence/ids-fail-closed-2026-08.md`](../../docs/evidence/ids-fail-closed-2026-08.md) | Пропуск обязательной проверки IDS роняет комплект |
| [`../../docs/evidence/kt2-handoff-2026-08-11/README.md`](../../docs/evidence/kt2-handoff-2026-08-11/README.md) | Пакет передачи; показ — живой CLI, не снимок HTML |
| [`../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md`](../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md) | Пять решений задаче заказчика канала по верификации ПД/РД; цифры конкурентов = их claims |
| [`../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md`](../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Что цифры вправе значить |
| [`../../docs/demo/KT2_CORPUS_SSOT_2026_08.md`](../../docs/demo/KT2_CORPUS_SSOT_2026_08.md) | Замороженные открытые прокси; это не корпус заказчика |
| [`../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | Методика до данных заказчика |
| [`../../docs/demo/KT3_JURY_FAQ_2026_08_25.md`](../../docs/demo/KT3_JURY_FAQ_2026_08_25.md) | КТ#3: живой CLI, файлов заказчика в git нет |
| [`../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md) | Лицензированные числа 29–30.09 |
| [`../../docs/quality/IFC_ANALYZE_VS_INGEST_CAP_2026_08.md`](../../docs/quality/IFC_ANALYZE_VS_INGEST_CAP_2026_08.md) | SPF 256 МиБ ≠ приём 1,5 ГБ |
| [`../../docs/quality/UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md`](../../docs/quality/UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md) | Review shell: что сделано / HOLD |
| [`AeroBIM_demo_day.pdf`](../03-presentation/AeroBIM_demo_day.pdf) | Дека поля формы, 29–30.09 |
| [`aerobim_kt2.pptx`](../03-presentation/aerobim_kt2.pptx) | Архив деки КТ#2 |

## Пины сентября (учебные и синтетические)

| Пин | Чем является | Чем не является |
|---|---|---|
| [`sla-package-scale-latest.json`](../../docs/evidence/sla-package-scale-latest.json) | Учебный p95 на стенке+IDS; inventory ≥1 МиБ за счёт публичных XSD; IFC анализа — 799 байт | не SLA заказчика; `sla_pass` на фикстуре не переносится |
| [`defect-injection-recall-run-latest.json`](../../docs/evidence/defect-injection-recall-run-latest.json) | 10/10 убитых мутаций на шовно-чистой стенке+IDS; нижняя граница Wilson 0,72 | Полнота продукта; recall на комплекте заказчика |
| [`tz-matrix-status-latest.json`](../../docs/evidence/tz-matrix-status-latest.json) | Снимок capabilities на учебной фикстуре | Закрытие ТЗ заказчиком |
| [`offline-bundle-trial-latest.json`](../../docs/evidence/offline-bundle-trial-latest.json) | Пробный Docker image-track | Данные заказчика; готовность СОД |
| [`data-residency-inventory-latest.json`](../../docs/evidence/data-residency-inventory-latest.json) | Диск отчётов, опциональный SQLite, задачи в процессе API | Заключение 152-ФЗ; durable workers |
| [`substitution-matrix-latest.json`](../../docs/evidence/substitution-matrix-latest.json) | 58 живых адаптеров из 63 токенов | Смета «заменить вендора» |
| [`../../docs/deployment-sizing-and-cost-2026.md`](../../docs/deployment-sizing-and-cost-2026.md) | Потолки RAM и набросок 2+0,5 FTE | Коммерческое КП; диаграмма Ганта |

Открытые наборы и учебные комплекты — регрессия движка. В них нет разметки инженеров «заказчика канала». Разбор шести столов (Техлаб, МИК, трекер, заказчик, жюри, оператор) — в [карточке речи](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md) и Interpretation/Use ledger.

Нельзя выдавать за доказательство: снимок HTML 11.08 и `wall-guid/report.html`; локальный pytest как CI pin; письмо трекеру как факт git; ролик как «видео-демо» (в git есть `AeroBIM_demo_day.pdf` / `aerobim_kt2.pptx`, mp4 нет и не появится); SAFE; уже оплаченный пилот. **ИП/юрлицо не требование входа в Техлаб** (FAQ: физлица или команда до 10) и не доказательство готовности продукта. Дату регистрации юрлица не выдумываем.
