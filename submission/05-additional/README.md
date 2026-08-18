---
title: "Поле «Дополнительные материалы» — доказательства и самопроверка"
status: active
version: "1.0.4"
last_updated: "2026-08-18"
claim_boundary: >
  Supporting evidence index. Open benches and fixtures are not the customer
  корпус. Checkpoint NO_GO; RT-001/002/003 OPEN.
---

# Дополнительные материалы

**Формула стадии (дословно, SSOT [`../../docs/demo/KT2_JURY_FAQ_2026_08_12.md`](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет корпуса Самолёта, двух разметчиков, подписанного профиля приёмки и подтверждения импорта в СОД.

Индекс доказательств: [`../../docs/evidence/`](../../docs/evidence/). Каждый артефакт помечен, чем он **не** является.

## Можно показывать жюри

| Материал | Роль |
|---|---|
| [`../../docs/evidence/kt2-handoff-2026-08-11/README.md`](../../docs/evidence/kt2-handoff-2026-08-11/README.md) | Пакет передачи; live CLI, не снимок HTML |
| [`../../docs/evidence/ids-fail-closed-2026-08.md`](../../docs/evidence/ids-fail-closed-2026-08.md) | IDS: пропуск обязательной проверки роняет комплект |
| [`../../docs/evidence/DATA_STATEMENT_2026_08.md`](../../docs/evidence/DATA_STATEMENT_2026_08.md) | Происхождение данных |
| [`../../docs/quality/RED_TEAM_FINAL_VERDICT_2026_08_16.md`](../../docs/quality/RED_TEAM_FINAL_VERDICT_2026_08_16.md) | Итоговый вердикт серии |
| [`../../docs/quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md`](../../docs/quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md) | Атаки шести столов |
| [`../../docs/quality/KT2_PACK_AUDIT_2026_08_18.md`](../../docs/quality/KT2_PACK_AUDIT_2026_08_18.md) | Аудит пакета подачи 18.08: гейты, живой CLI, дека, CI |
| [`../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md`](../../docs/demo/KT2_TASK07_COMPARISON_2026_08.md) | Пять решений Задачи 07; цифры конкурентов = их claims |
| [`../../CITATION.cff`](../../CITATION.cff) | Цитирование проекта |

## Только как fixture / open-bench / protocol evidence

Не корпус Самолёта. Не точность продукта. Не SLA заказчика.

| Материал | Граница |
|---|---|
| [`../../docs/demo/KT2_CORPUS_SSOT_2026_08.md`](../../docs/demo/KT2_CORPUS_SSOT_2026_08.md) | Замороженная строка открытых прокси; RT-001 OPEN |
| [`../../docs/evidence/drawing-overlay-smoke-2026-08/README.md`](../../docs/evidence/drawing-overlay-smoke-2026-08/README.md) | Наложение на учебный лист; P1 |
| [`../../docs/evidence/renga-export-probe-2026-08.md`](../../docs/evidence/renga-export-probe-2026-08.md) | Проба выгрузки Renga; не комплект заказчика |
| [`../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](../../docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | Protocol-only: методика до данных |
| [`../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md`](../../docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Kane IUA, заморозка `f9389bf` |
| [`../../docs/quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md`](../../docs/quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md) | Литература × IUA; Harbor NOT_RUN |
| [`../../docs/quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](../../docs/quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md) | Академическая корректность заявлений |

Открытые наборы — регрессия движка. В них нет разметки TP/FP инженеров «Самолёта».

## Внутренний red-team (можно открыть, не продавать как GO)

| Отчёт | Вектор |
|---|---|
| [`../../docs/quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md`](../../docs/quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md) | Вопросы венчура; ask = слот + комплект, не SAFE |
| [`../../docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md`](../../docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md) | Принятые риски, включая N-43 |
| [`../../docs/partners/COMPETITIVE_MATRIX_2026_08.md`](../../docs/partners/COMPETITIVE_MATRIX_2026_08.md) | Аналоги; не измеренный факт AeroBIM |
| [`../../docs/partners/ROADMAP_3Y_2026_08.md`](../../docs/partners/ROADMAP_3Y_2026_08.md) | `planning_only`. LOI / пилоты — будущие зависимости, не git-факт |
| [`../../docs/demo/KT2_10D_INTAKE_CONTRACT_2026_08.md`](../../docs/demo/KT2_10D_INTAKE_CONTRACT_2026_08.md) | Предлагаемые поля; не коннектор 10D |

## Нельзя выдавать за доказательство в этом поле

- operator kitchen, session dumps, промты для ИИ (лежат в `.local/`, не на GitHub);
- снимок HTML 11.08 и `wall-guid/report.html` как overlay;
- локальный pytest как CI pin;
- письмо трекеру как факт git;
- ролик как «видео-демо»: в git есть `aerobim_kt2.pptx` / `aerobim_kt2.pdf`, но mp4 нет и не появится;
- юрлицо, SAFE, оплаченный пилот, 2 млн ₽.

Мы публикуем найденные слабости сами, чтобы жюри не находило их первым.
