---
title: "Samolet TZ / Task 07 — remaining tails"
status: active
last_updated: "2026-07-12"
tags: [aerobim, samolet, tz, blockers]
---

# Хвосты по ТЗ Самолёта (Task 07) — после A1–A5 + Red Team

Инженерные scaffolds в репо **закрыты**. Ниже — что ещё не закрывает букву ТЗ / пилотный контракт.

## A. Блокеры только у Самолёта (нельзя дописать в git)

| Хвост | ТЗ / KPI | Статус AeroBIM |
|---|---|---|
| 1 согласованный комплект ПД/РД+IFC+ТЗ+расчёты+2D | SLA ≤30 мин, precision | Fixture only |
| Approved residential IDS/rule pack | vs norms | `synthetic-template` ≠ sign-off |
| ≥20 typical errors **customer_confirmed** | appendix | Catalog scaffold, confirmed=0 |
| 2 adjudicators + labeled corpus | >90% / TP≥60% | Harness+A3 ready, labels empty |
| Baseline часов ручной проверки | −20% review time | Нет данных |
| CDE + BCF import proof | handoff | Export+demo path; import у заказчика |
| Signed scope memo | границы CV/ГОСТ/MEP | Шаблон ask есть |

См. [`SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](SAMOLET_WHAT_WE_NEED_2026_07-ru.md).

## B. Частичные строки ТЗ (можно углублять без корпуса, но не «закрыть ТЗ»)

| Тема | Матрица | Что осталось в продукте |
|---|---|---|
| CV «как человек» | missing / out of acceptance | Не делать sign-off |
| DWG/DXF | missing P2 | Thin adapter |
| MEP system clash | `MEP-CLASH-001` | Federated IFC + правила от Самолёта |
| Space efficiency | missing P4 | Только если KPI согласован |
| Full SP/GOST | non-claim | Никогда не обещать «все нормы» |
| LLM remarks/IDS | advisory stub | P3 + HITL |
| Version/CDE diff | partial | ISO 19650-lite уже; полный diff — post-pilot |

## C. Уже закрыто инженерно (не путать с customer KPI)

- A1 section pairing, A2 norm packs, A3 precision intake, A5 demo path  
- Sign-off honesty: `capabilities.FAILED` → `summary.passed=false` (analyze + IDS paths)  
- Upload streaming, BCF UUID, path jail, Redis CAS, auth defaults (`debug`/`anonymous` opt-in)  
- Vite auth proxy (bearer не в браузер); OIDC `verify_nbf`  
- Verification 2026-07-12: **406 passed / 3 skipped**; demo path `ok: true`

## Следующий шаг

1. Kickoff с Самолётом по [`SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](SAMOLET_WHAT_WE_NEED_2026_07-ru.md).  
2. После корпуса — `docs/ops/intake-precision-runbook-2026.md`.  
3. Опционально без корпуса: A4 typical-errors mapping coverage или DWG thin (P2).
