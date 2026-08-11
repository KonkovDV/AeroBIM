<!-- claims-lint: allow-file reason="KT#2 handoff cover note; forbidden phrases as non-claims only" -->
---
title: "КТ#2 — единый handoff cover"
date: "2026-08-11"
claim_boundary: "Fixture GO. Checkpoint NO_GO. Not customer accuracy."
---

# КТ#2 — cover note (11.08.2026)

## Одна фраза для экрана

**Промежуточная версия на fixture готова показать; checkpoint у заказчика — NO_GO, пока нет корпуса / norm pack / MEP scope.**

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
| N43 baseline lag=1 | репетиция **17.08** |

## Календарь до конца окна КТ#2 (20.08)

1. **12–16.08** — TZ: держать clash/overlay честными; при появлении IFC заказчика — dual-blind, не выдумывать labels.  
2. **17.08** — N43: `max_commits_behind=1` + свежий runtime baseline.  
3. **до 20.08** — промежуточная версия + обратная связь экспертов; Claims Lock непрерывен.  
4. После **19.08** — RUF100 / FE lint (не раньше).

## Что просить у Самолёта завтра

См. [`../pilot/CUSTOMER_KICKOFF_MAP_2026_07_26.md`](../pilot/CUSTOMER_KICKOFF_MAP_2026_07_26.md) и [`../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md): комплект, norm pack, ≥2 эксперта, baseline-часы; MEP — только если в scope.
