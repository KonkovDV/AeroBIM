<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Трёхисточниковая матрица требований: Самолёт × Техлаб × МИК"
status: active
version: "1.2.3"
last_updated: "2026-08-27"
claim_boundary: "Матрица трассирует требования, не повышает статусы: fixture ≠ customer; Checkpoint GO; customer_go false до RT-001/002/003."
tags: [aerobim, samolet, techlab, mik, traceability, requirements]
---

# Требования трёх сторон программы → AeroBIM (SSOT-навигатор)

Пилот имеет **пять** источников требований с разными ролями. До 2026-07-26
репозиторий покрывал два; контур МИК добавлен
([`MIK_PILOT_COMPLIANCE_2026.md`](../partners/MIK_PILOT_COMPLIANCE_2026.md)).
16.08: Interpretation/Use ledger сводит все источники в лицензированные выводы
(Kane 2013) — [`../quality/INTERPRETATION_USE_LEDGER_2026_08.md`](../quality/INTERPRETATION_USE_LEDGER_2026_08.md).
27.08: публичный **ТЗ v1 бриф** (6 стр.) запинен отдельно от v2, семи сравнений и проектного ТЗ — [`TZ_V1_CONTEST_BRIEF_PIN_2026_08.md`](TZ_V1_CONTEST_BRIEF_PIN_2026_08.md) · IUA `SAM-10`.

| Сторона | Роль | Чего требует | Канонический документ ответа |
|---|---|---|---|
| **Самолёт** | Заказчик-площадка | Функциональность (ТР-1..62), KPI качества, данные/эксперты со своей стороны | [`TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`](TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) + [`TZ_COMPLIANCE_MATRIX_2026.md`](TZ_COMPLIANCE_MATRIX_2026.md) |
| **Техлаб** | Программа отбора (жюри) | Заявка, MVP-демо, честные формулировки; участие — физлица / команда ≤10 | [`../partners/TECHLAB_TASK_07_READINESS_2026.md`](../partners/TECHLAB_TASK_07_READINESS_2026.md) + [`../partners/TECHLAB_SAMOLET_APPLICATION_2026.md`](../partners/TECHLAB_SAMOLET_APPLICATION_2026.md) |
| **МИК (Фонд)** | Оператор программы | Формы соглашения/акта **если** потребует оператор; не грантодатель входа в Техлаб | [`../partners/MIK_PILOT_COMPLIANCE_2026.md`](../partners/MIK_PILOT_COMPLIANCE_2026.md) |
| **Отрасль** | Нормы openBIM / приёмки | IDS 1.0, ISO 19650-2 5.7, Solihin 1–4, ПНСТ 909 | [`../quality/INTERPRETATION_USE_LEDGER_2026_08.md`](../quality/INTERPRETATION_USE_LEDGER_2026_08.md) IND-* |
| **Трекер** | Операционный спринт к КТ#3 | 6 задач 14.08; live CLI; не число демо в git | [`../demo/KT3_TRACKER_SIX_TASKS_2026_08.md`](../demo/KT3_TRACKER_SIX_TASKS_2026_08.md) · ledger TRK-* |

**Четыре бумаги Самолёта (не склеивать):** v1 бриф 6 стр. [`TZ_V1_CONTEST_BRIEF_PIN_2026_08.md`](TZ_V1_CONTEST_BRIEF_PIN_2026_08.md) · v2 ТР-1…62 · семь задач сравнения · проектное ТЗ объекта. IUA `SAM-10`.

## Сводная матрица по темам

Статусы: DONE · ENG_READY (инженерно готово, ждёт данных/форм) ·
PROTOCOL_READY (методика есть, замер не сделан) ·
PARTIAL · BLOCKED_CUSTOMER_DATA · VERIFY_WITH_OPERATOR · OUT (заявленное ограничение).

| Тема | Самолёт (ТЗ) | Техлаб (пилот) | МИК (оператор) | Статус AeroBIM | Разрыв / владелец |
|---|---|---|---|---|---|
| Функциональный контур (IFC/IDS/cross-doc/2D/отчёты) | ТР-1..47 | MVP-демо | — | DONE/PARTIAL по [ТР-матрице](TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) §19 | Открытые PARTIAL ждут данных |
| Точность | «>0.90 целевая» (P4) | interim ≥0.60 | В акт — фактическое значение с CI | **PROTOCOL_READY** (harness+κ/α+n); measurement **BLOCKED** | Корпус+2 эксперта / Самолёт |
| SLA ≤30 мин | ТР-49 | критерий пилота | В акт — замер на customer-паке | **PROTOCOL_READY** (fixture rail ≠ customer SLA) | Эталонный пакет / Самолёт |
| Экономия ≥20% | KPI §9.4 | критерий пилота | Строка акта | **PROTOCOL_READY** (методика); measurement **BLOCKED** | Baseline-часы / Самолёт |
| BCF → СОД | ТР-52-смежное | «виден в СОД» | Доказательство результата | T0/T1 DONE; T2 BLOCKED | Sandbox СОД / Самолёт (до 20.08) |
| Каталог ≥20 ошибок | Приложение 5 | критерий пилота | Подтверждение площадки | PARTIAL (synthetic scaffold) | customer_confirmed / Самолёт |
| Программа испытаний + план-график | — | — | **Ключевой артефакт Фонда** | PROTOCOL_READY (наш календарь КТ); формы Фонда **не получены** | Формы Фонда / **МИК — слот до 3 авг просрочен 15.08** |
| Соглашение + финотчётность 2 млн ₽ | — | Приз = платный пилот (соглашение Партнёр↔Фонд) | Не вход в программу; 449-ПП отдельно | **VERIFY_WITH_OPERATOR** | Шаблоны / **МИК**; не требовать ИП для участия |
| Акт о результатах пилота | подпись эксперта | итог пилота | Закрывающий документ | BLOCKED_CUSTOMER_DATA (приложения готовы) | Подписанты обеих сторон |
| Честность формулировок | Claims Lock §12 ТЗ | «Do not claim» список; не требовать юрлицо для входа | Публичность *если* в соглашении Фонда | DONE (enforced fail-closed) | Ревью любых публичных текстов |
| Ограничения (DWG/MEP/calc/CV) | ТР-53 | заявлены в анкете | В программу испытаний — как out-of-scope | DONE (gap-анализ) | — |

## Конфликты источников (разрешение зафиксировано)

1. **0.90 vs 0.60** — не конфликт, а разные горизонты: 0.60 interim (контракт
   пилота, идёт в акт МИК), >0.90 — целевой P4-горизонт ТЗ после корпуса.
   Запрещено смешивать в одном документе без пометки горизонта.
2. **Календарь**: КТ Самолёта (20.07 / 4–20.08 / 3–21.09) первичен для
   контента; план-график Фонда первичен для **формы и сроков отчётности** —
   при расхождении дедлайнов побеждает более ранний.
3. **Публичность**: жюри-пак Техлаба публичен (GitHub), документы Фонда и
   customer-данные — нет (NDA, `samples/customer/` вне git).

## Definition of Done трёхисточникового соответствия

- [x] Самолёт: ТР-матрица без пустых TBD (§19 ТЗ v2)
- [x] Техлаб: заявка + readiness + критерии пилота + «do not claim»
- [x] МИК: контур документирован, M1–M9 с владельцами
- [x] IUA ledger (16.08): лицензированные выводы Kane по пяти источникам
- [x] ТЗ v1 бриф (6 стр.) запинен отдельно от v2 / семи задач / проектного ТЗ (`SAM-10`)
- [x] Owner-AI plan 27.08: unsigned OOS + local inventory (`PLAN-00`…`PLAN-05`); не закрывает RT
- [x] Трекер (6 задач 14.08): [`KT3_TRACKER_SIX_TASKS_2026_08.md`](../demo/KT3_TRACKER_SIX_TASKS_2026_08.md) + `run_kt3_jury`; KPI демо не в git
- [ ] Формы Фонда получены и M2/M8 закрыты (запрос «до 3 авг» **просрочен**; статус VERIFY_WITH_OPERATOR)
- [ ] Акт МИК подписан по результатам КТ3 (сентябрь)
