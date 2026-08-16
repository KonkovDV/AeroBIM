<!-- claims-lint: allow-file reason="KT#2 handoff cover note; forbidden phrases as non-claims only" -->
---
title: "КТ#2 — единый handoff cover"
date: "2026-08-11"
claim_boundary: "Fixture GO. Checkpoint NO_GO. Not customer accuracy."
---

# КТ#2 — cover note (речь 15.08, HEAD `25ef3ee`)

## Одна фраза для экрана

Мы на стадии доработки. Одна команда показывает live CLI с fail-closed доказательным finding на fixture. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется до корпуса Самолёта, двух разметчиков, signed scope и CDE-подтверждения.

## Что открыть 19–20.08

1. `cd backend && python -m aerobim.tools.run_demo_ifc_acceptance_gate` → `artifacts/ifc-acceptance-gate-demo/`
2. Overlay P1, если время: `python -m aerobim.tools.run_demo_vertical_slice` → `artifacts/vertical-slice-demo/report.html` (`#kt2-overlay`)
3. Не открывать `kt2-handoff-2026-08-11/wall-guid/report.html` как ядро среза.
4. Репетиция: [`KT2_DEMO_REHEARSAL_2026_08_12.md`](KT2_DEMO_REHEARSAL_2026_08_12.md). Питч: [`../partners/PITCH_NOVALTOR_TECHLAB_2026_08.md`](../partners/PITCH_NOVALTOR_TECHLAB_2026_08.md) — первые 15 с = формула, не раунд. Первые 30 с продукта: сценарий трекера №4, без публикации цифр без разметки.

## Пакет

Полный индекс и команды: [`../evidence/kt2-handoff-2026-08-11/README.md`](../evidence/kt2-handoff-2026-08-11/README.md)

| Блок | Статус |
| --- | --- |
| Methodology DoD (протокол, harness, TZ matrix, kickoff) | eng **done** |
| Wall-guid evidence bundle + verify | **passed** (tip `701a267` regen) |
| Vertical slice + limitations | **done** |
| Harness synthetic + `--require-publishable` fail-closed | **done** (exit 1) |
| Clash AABB fixture n=5 | **fixture_measured** |
| Drawing overlay PNG | **fixture_rendered** |
| Mentor pack | **done** |
| RT-001 / RT-002 / RT-003 | **OPEN** (данные Самолёта) |
| OIDC BFF | **501** Phase 2.5 stub — не production |
| Jury FAQ / rehearsal | [`KT2_JURY_FAQ_2026_08_12.md`](KT2_JURY_FAQ_2026_08_12.md) · [`KT2_DEMO_REHEARSAL_2026_08_12.md`](KT2_DEMO_REHEARSAL_2026_08_12.md) |
| Tri-source alignment | [`../tz/KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md`](../tz/KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md) |
| N43 baseline lag=1 | checklist [`../audit/N43_REHEARSAL_CHECKLIST_2026_08_17.md`](../audit/N43_REHEARSAL_CHECKLIST_2026_08_17.md) — activate **17.08** only |

## Календарь до конца окна КТ#2 (20.08)

Только четыре закрытия:

1. Live CLI на каждом показе (Gate; overlay — fallback).  
2. **17–18.08** — сухой прогон + fallback-ролик ([`KT2_VIDEO_DRY_RUN_2026_08.md`](KT2_VIDEO_DRY_RUN_2026_08.md)); **19.08** — видео (человек).  
3. **19–20.08** — ЛК (человек): отозвать текущее решение → обновить страницу → «Загрузить решение». Текст: [`KT2_LK_COVER_TEXT_2026_08_15.md`](KT2_LK_COVER_TEXT_2026_08_15.md). Команду не менять.  
4. Запрос заказчику: [`../partners/SAMOLET_KT2_ASK_2026_08_15.md`](../partners/SAMOLET_KT2_ASK_2026_08_15.md) (owner + ack 20.08).

N43 / AEC-Bench **не** входят в это окно. Wave A ≠ RT CLOSED. 20.08 — только критический фикс.

## Что просить на этой неделе (не раунд)

Комплект, подписанный norm pack, ≥2 эксперта, baseline-часы; MEP — только если в scope. Юрлица нет — не обещать договор / SAFE.  
См. [`../pilot/CUSTOMER_KICKOFF_MAP_2026_07_26.md`](../pilot/CUSTOMER_KICKOFF_MAP_2026_07_26.md) · [`../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md`](../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md).
