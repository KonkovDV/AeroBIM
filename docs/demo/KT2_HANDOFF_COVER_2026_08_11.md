<!-- claims-lint: allow-file reason="KT#2 handoff cover note; forbidden phrases as non-claims only" -->
---
title: "КТ#2 — единый handoff cover"
date: "2026-08-11"
claim_boundary: "Fixture GO. Checkpoint NO_GO. Not customer accuracy."
---

# КТ#2 — cover note (11.08.2026, речь 15.08)

## Одна фраза для экрана

**Промежуточная версия на fixture готова показать; checkpoint у заказчика — NO_GO, пока нет корпуса / norm pack / MEP scope.**

## Что открыть 19–20.08

1. `cd backend && python -m aerobim.tools.run_demo_vertical_slice`
2. `artifacts/vertical-slice-demo/report.html` (`#kt2-overlay`, `#kt2-claim-boundary`)
3. Не открывать `kt2-handoff-2026-08-11/wall-guid/report.html` как ядро среза.
4. Репетиция: [`KT2_DEMO_REHEARSAL_2026_08_12.md`](KT2_DEMO_REHEARSAL_2026_08_12.md). Питч: [`../partners/_TECHLAB_2026_08.md`](../partners/_TECHLAB_2026_08.md) — первые 15 с = NO_GO, не раунд.

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
| Academic closure plan (12.08) | [`../pilot/KT2_ACADEMIC_CLOSURE_PLAN_2026_08_12.md`](../pilot/KT2_ACADEMIC_CLOSURE_PLAN_2026_08_12.md) |
| Max-eng plan | [`../pilot/KT2_MAX_ENG_PLAN_2026_08_12.md`](../pilot/KT2_MAX_ENG_PLAN_2026_08_12.md) |
| Jury FAQ / rehearsal | [`KT2_JURY_FAQ_2026_08_12.md`](KT2_JURY_FAQ_2026_08_12.md) · [`KT2_DEMO_REHEARSAL_2026_08_12.md`](KT2_DEMO_REHEARSAL_2026_08_12.md) |
| Tri-source alignment | [`../tz/KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md`](../tz/KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md) |
| N43 baseline lag=1 | checklist [`../audit/N43_REHEARSAL_CHECKLIST_2026_08_17.md`](../audit/N43_REHEARSAL_CHECKLIST_2026_08_17.md) — activate **17.08** only |

## Календарь до конца окна КТ#2 (20.08)

1. **15–16.08** — overlay / CDE wording / funding speech (live CLI, не wall-guid).  
2. **17.08** — N43: `max_commits_behind=1` **только в этот день** ([checklist](../audit/N43_REHEARSAL_CHECKLIST_2026_08_17.md)). Не раньше.  
3. **19.08** — видео (человек) + ЛК. Скрипт: [`KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md).  
4. **20.08** — КТ#2. Буфер: только критический фикс. Wave A ≠ RT CLOSED.

## Что просить на этой неделе (не раунд)

Комплект, подписанный norm pack, ≥2 эксперта, baseline-часы; MEP — только если в scope. Юрлица нет — не обещать договор / SAFE.  
См. [`../pilot/CUSTOMER_KICKOFF_MAP_2026_07_26.md`](../pilot/CUSTOMER_KICKOFF_MAP_2026_07_26.md) · [`../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md`](../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md).
