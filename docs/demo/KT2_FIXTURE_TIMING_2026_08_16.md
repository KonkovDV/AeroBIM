<!-- claims-lint: allow-file reason="Fixture wall-clock sheet; SLA phrases as non-claims; NO_GO" -->
---
title: "КТ#2 — fixture timing (порядок величины, не SLA)"
date: "2026-08-16"
status: active
claim_boundary: >
  Fixture wall-clock only. representative_scale=false. Not customer комплект.
  Not ≤30 min SLA. Checkpoint NO_GO. sla_pass on the toy pack is not a claim.
---

# Fixture timing — порядок величины

Жюри спрашивает «≤30 минут — да или нет?». Короткий ответ: **на комплекте Самолёта — не измерено** (нет pack + machine + mandatory caps). На учебной фикстуре есть wall-clock **порядка секунды**, не контракт.

Источник SLA-гейта: `python -m aerobim.tools.measure_package_sla` (schema **1.4.0**). Без customer pack / fingerprint / `--mandatory-capabilities-complete` формулировка «≤30 мин» **запрещена**. Протокол: [`../sla-benchmark-protocol-2026.md`](../sla-benchmark-protocol-2026.md).

## Что можно показать на защите

| Прогон | Дата | Машина | Число | Что это **не** |
|---|---|---|---|---|
| `measure_package_sla` cold p95 | 2026-08-03 | Windows 11, 32 GB RAM, Python 3.13 | **p95 = 533 ms** (max 533 ms, avg 186 ms, 3 итерации) | Не SLA Самолёта. Пакет **4784 байт**, `representative_scale=false` |
| Wall-guid analyze | 2026-08-11 | тот же контур handoff | **analyze_elapsed_ms = 1725** | Overlay/handoff path, не sell-path Gate; не streaming latency |

Артефакты (не пересказывать `sla_pass=true` жюри — это гейт на игрушечном пакете):

- [`../evidence/samolet-sla-fixture-p95-2026-08-04.json`](../evidence/samolet-sla-fixture-p95-2026-08-04.json) — `claim_level: fixture_only`, `allowed_wording: Fixture wall-clock only; gate=p95; not customer комплект SLA`
- [`../evidence/kt2-handoff-2026-08-11/wall-guid/timings.json`](../evidence/kt2-handoff-2026-08-11/wall-guid/timings.json)

Sell-path КТ#2: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`. Живое время — с экрана терминала на этой машине; **не** подставлять p95 игрушечного пакета как время Acceptance Gate.

## Что говорить (дословно)

«На учебной стенке порядок — доли секунды / пара секунд. Это не ≤30 минут ТЗ. Тридцать минут мерим только на вашем согласованном пакете, на согласованном железе, с полным набором обязательных capability. Гейт без этого отказывается.»

## Запрещено

- «SLA ≤30 мин выполнен» / цитировать `sla_pass: true` без `representative_scale=false`
- переносить p95 533 ms на Renga/Tangl/10D комплект
- называть wall-guid 1.7 с временем продукта или streaming TTFF

Checkpoint **NO_GO**. RT-001/002/003 OPEN.
