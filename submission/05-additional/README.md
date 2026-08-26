---
title: "Поле «Дополнительные материалы» — доказательства"
status: active
version: "1.0.8"
last_updated: "2026-08-26"
claim_boundary: >
  Supporting evidence index. Open benches and fixtures are not the customer
  корпус. Checkpoint NO_GO; RT-001/002/003 OPEN.
---

# Дополнительные материалы

**Формула стадии (дословно; источник — [карточка речи для жюри](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет независимого размеченного корпуса, двух разметчиков, профиля приёмки (публичные IDS экспертизы — измерение; подпись Самолёта — внедрение) и подтверждения импорта в СОД.

| Материал | Роль |
|---|---|
| [`../../docs/evidence/DATA_STATEMENT_2026_08.md`](../../docs/evidence/DATA_STATEMENT_2026_08.md) | Какие данные есть и каких нет |
| [`../../docs/evidence/ids-fail-closed-2026-08.md`](../../docs/evidence/ids-fail-closed-2026-08.md) | Пропуск обязательной проверки IDS роняет комплект |
| [`../../docs/evidence/kt2-handoff-2026-08-11/README.md`](../../docs/evidence/kt2-handoff-2026-08-11/README.md) | Пакет передачи; показ — живой CLI, не снимок HTML |
| [`../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md`](../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md) | Пять решений задаче Самолёта по верификации ПД/РД; цифры конкурентов = их claims |
| [`../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md`](../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Что цифры вправе значить |
| [`../../docs/demo/KT2_CORPUS_SSOT_2026_08.md`](../../docs/demo/KT2_CORPUS_SSOT_2026_08.md) | Замороженные открытые прокси; это не корпус Самолёта |
| [`../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | Методика до данных заказчика |
| [`../../docs/demo/KT3_JURY_FAQ_2026_08_25.md`](../../docs/demo/KT3_JURY_FAQ_2026_08_25.md) | КТ#3: живой CLI, файлов заказчика в git нет |

Открытые наборы и учебные комплекты — регрессия движка. В них нет разметки инженеров «Самолёта». Разбор шести столов (Техлаб, МИК, трекер, заказчик, жюри, оператор) — в [карточке речи](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md) и Interpretation/Use ledger.

Нельзя выдавать за доказательство: снимок HTML 11.08 и `wall-guid/report.html`; локальный pytest как CI pin; письмо трекеру как факт git; ролик как «видео-демо» (в git есть `aerobim_kt2.pptx` / `aerobim_kt2.pdf`, mp4 нет и не появится); SAFE; уже оплаченный пилот. **ИП/юрлицо не требование входа в Техлаб** (FAQ: физлица или команда до 10) и не доказательство готовности продукта.
