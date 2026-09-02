<!-- claims-lint: allow-file reason="Lab before/after time study; not partner hours; A1-A8 stay empty; NO_GO" -->
---
title: "Before/after measurement protocol — lab pack, not partner B4"
date: "2026-08-30"
last_updated: "2026-09-02"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Laboratory time-study protocol on an AeroBIM-owned pack. Not partner hours.
  Not B4 partner effect. A1-A8 stay empty until a partner baseline exists.
  Not the published analog -72.1%. Checkpoint NO_GO.
---

# Лабораторный замер «до / после» (не Б4 партнёра)

Это методика **контролируемого** замера на комплекте, которым владеет команда
(фикстура или синтетический мини-ПД). Это **не** часы Самолёта, **не**
заполнение A1–A8 и **не** экономия ≥20% из заявки.

Ячейки A1–A8 остаются пустыми:
[`ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md`](ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md).
`k4_revenue_claimed() == False`.
`foreign_labor_cut_as_ours() == False`.

## Протокол (ручной таймер против AeroBIM)

1. Freeze комплекта (хеш в журнале; комплект **не** из `samples/customer`).
2. Один эксперт, один протокол замечаний (суть + пункт + этаж/ось если есть).
3. Проход **без** системы: секундомер от открытия папки до списка замечаний.
4. Проход **с** AeroBIM на том же freeze: секундомер от запуска CLI до того же
   списка, подтверждённого человеком (HITL). LLM не ставит `summary.passed`.
5. Порядок проходов чередовать (половина экспертов начинает без системы), чтобы
   не склеить обучение с эффектом инструмента.
6. Не сравнивать с SLA «30 минут» заказчика. Fixture p95 не representative.

Формула (без чисел в git):

```text
сэкономленные минуты = минуты_ручные − минуты_с_системой
доля               = сэкономленные / минуты_ручные
```

Публиковать можно только с `claim_level=fixture_only` (или `synthetic_only`)
и явной пометкой «не корпус партнёра».

## Журнал (форма)

| Поле | Правило |
|---|---|
| `run_id` | дата + инициалы **не в git**, если это ФИО заявки |
| `pack_hash` | sha256 freeze; не NDA pack заказчика |
| `order` | `manual_first` / `tool_first` |
| `t_manual_s` | целое секунд |
| `t_tool_s` | целое секунд |
| `n_remarks_manual` | число |
| `n_remarks_tool_confirmed` | HITL-подтверждённые |
| `discrepancy` | FP/FN относительно ручного списка |
| `claim_level` | `fixture_only` или `synthetic_only` |

Расхождения фиксировать **по finding_id**, не «в целом быстрее».

## Мост-артефакт (только машинное время)

CLI `python -m aerobim.tools.run_lab_before_after_fixture --also-docs-evidence`
пишет [`../evidence/lab-before-after-fixture-tool-only-latest.json`](../evidence/lab-before-after-fixture-tool-only-latest.json):
`t_tool_ms` на git-стенке + IDS, `claim_level=fixture_only`.
`t_manual_s`, `n_remarks_manual`, HITL-подтверждение и `discrepancy` — **null**.
Формула доли **не** считается. Это не заполнение A1–A8 и не Б4 партнёра.

## Ограничения

- Малое n. Один эксперт ≠ κ.
- Не корпус заказчика. Не партнёрские часы.
- Не переносить −72,1% чужой публикации.
- Не заполнять A1–A8 этим журналом.
- Не говорить «готово к внедрению».

Связь с системой B: [`B_FINAL_SCORING_TICKSHEET_2026_09.md`](../quality/B_FINAL_SCORING_TICKSHEET_2026_09.md)
(Б4 остаётся пустым для партнёра).
