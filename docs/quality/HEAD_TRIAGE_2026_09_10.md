<!-- claims-lint: allow-file reason="HD22 Red Team + triage of post-#47 main; KILL/HOLD/ACCEPT; Checkpoint GO; customer_go false; residual RT OPEN" -->
---
title: "Триаж HEAD 10.09.2026 — Red Team HD22 (post PR #47)"
status: active
version: "1.0.0"
last_updated: "2026-09-10"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Red Team + triage of live main after PR #47. Remediations in this pass.
  Checkpoint GO (regulatory_measurement_mvp). customer_go false.
  Not a MIK score. Not product accuracy. Not customer SLA. Not MEP delivered.
  Test counts live only in docs/evidence/runtime-baseline-latest.json.
auditor: "триаж × Red Team × White Hat"
audited_head: "main after merge of PR #47; this commit is HD22 remediations"
---

# Триаж HEAD 10.09 — HD22

Метод: живое дерево `main` после merge PR #47 (review-shell ergonomics), плюс
повторный Red Team поверхностей вердикта, HITL, пакета ревью, claims-lint,
фронтенда плотности и речи checkpoint. Онтология не сдвигается. Лексика:
KILL / HOLD / ACCEPT. IDs **HD22-***. Серия `docs/quality/RED_TEAM_REAUDIT*`
намеренно в `.gitignore` — этот файл отслеживаемый.

GitHub **#40 / #41 / #44** остаются **OPEN**. Stash с логотипом и старыми
грязными деревьями **не** вливать. Ветка продукта — только `main`.

## 0. Триаж (итог прохода)

| ID | Verdict | Что |
|---|---|---|
| **HD22-STALE-01** | **KILL → FIXED** | `CALL_09_09_TRIAGE`: скопированные `tests_collected`/`tests_passed` и SHA pin 09.09 |
| **HD22-STALE-02** | **KILL → FIXED** | `REMEDIATION_PLAN_P0_P2`: «Facts to quote» копировал целые baseline |
| **HD22-NOGO-01** | **KILL → FIXED** | `TECHLAB_SEVEN_TASKS_CARTOGRAPHY` тело `Checkpoint: NO_GO` при YAML GO |
| **HD22-CAP-01** | **KILL → FIXED** | Живая речь «Checkpoint remains NO_GO» в capabilities / release evidence / `.env.example` |
| **HD22-AUTH-01** | **KILL → FIXED** | Пакет ревью: omitted/`None` `summary.authoritative` fail-open в `True` |
| **HD22-DEN-02** | **HOLD → FIXED** | HITL readonly note: CSS ждал `.hitl-readonly-note`, DOM был только `compact-copy` |
| **HD22-DEN-03** | **HOLD → FIXED** | `.capability-skip-banner` не в compact-preserve / print / surfaces |
| **HD22-PACK-02** | **HOLD → FIXED** | Markdown shortlist молчал, что `similar_count` живёт в JSON/CSV |
| **HD22-IDX-01** | **HOLD → FIXED** | `FRONTEND_UI_EXTERNAL_REVIEW` и этот триаж не были в карте TIER0 |
| **HD22-INJ-01** | **HOLD** | `defect-injection-recall-run-latest.json` — прогон 03.09, `checkpoint: NO_GO`; не переписывать; remint = owner |
| **HD22-DECK-01** | **HOLD** | Колода всё ещё `aerobim_kt2.pptx` / `.pdf`; пересборка КТ#3 = owner |
| **HD22-PIN-01** | **HOLD** | Baseline `commit_sha` — merge-ref PR, не обязательно reachability `main` |
| **HD22-OA-01** | **HOLD** | OA-20 «не менее 50» UNVERIFIED; OA-25 10–25 карточек до 14.09; on-prem vs cloud письменно |
| **HD22-FE-34** | **HOLD** | WP-FE-34 `<main>`, 35 virtualize, 36 sticky headers, 37 report layers, 38 print route |
| **HD22-D12** | **HOLD** | D-12 время эксперта не замерено |
| **HD22-ABOUT-01** | **ACCEPT** | GitHub About уже: Checkpoint GO, `customer_go` stays false |
| **HD22-ADR-01** | **ACCEPT** | ADR-001: LLM не пишет `summary.passed` |
| **HD22-CK-01** | **ACCEPT** | `CUSTOMER_GO = False` + `require_honest_checkpoint` |
| **HD22-PACK-01** | **ACCEPT** | Схема пакета 1.1.1; пустой `customer_decision.status`; HITL только `review.status` |
| **HD22-COV-01** | **ACCEPT** | Coverage = overlap identity-key, не recall; `similar_count` включает self |
| **HD22-UI-01** | **ACCEPT** | Skip `#work-area`; lazy IfcViewer; `force-light.css` последним; compact не `display:none` honesty |
| **HD22-HOM-01** | **ACCEPT** | Нет недифференцированного «RT-001 CLOSED» / «RT-003c CLOSED» как состояния продукта на фокус-доках |
| **HD22-KT2-01** | **ACCEPT** | KT#2 handoff `NO_GO` = HISTORICAL_PIN |
| **HD22-STASH-01** | **ACCEPT** | Локальные stash (логотип, старые dirty trees) не продукт и не merge в `main` |

**OVERCLAIM продукта: 0.** Недифференцированное CLOSED: 0.

## 1. Identity / ontology (Red Team)

Живой SSOT: `aerobim.domain.checkpoint` — `CHECKPOINT=GO`,
`GO_KIND=regulatory_measurement_mvp`, `CUSTOMER_GO=false`.
`PrecisionClaim.publishable` false. Симулированные разметчики ≠ люди.
Атака «GO ⇒ приёмка Самолёта» блокируется `customer_go` и
`closes_rt001/002/003=false`.

HD21 закрыл «Checkpoint **stays** NO_GO». HD22 закрыл синоним
«Checkpoint **remains** NO_GO» в live `backend/src/aerobim` (кроме
`verify_kt2_handoff.py`). Исторические датированные прогоны августа и
аудиторский бриф, где фраза — *название находки*, не живая речь продукта —
не переписывались.

## 2. White Hat (пакет ревью)

`build_customer_review_pack`: `authoritative` только при явном `True`.
Store default остаётся `False`. Markdown не выдаёт размер семьи за полноту:
сноска указывает на JSON/CSV. `customer_acceptance` остаётся
`NOT_EVALUATED`. UI не пишет `summary.passed`.

## 3. Что остаётся OPEN (не подмена)

RT-001b люди; RT-001c корпус заказчика; RT-002c подпись назначающей стороны;
RT-003c MEP (`b3`); федеративный IFC заказчика; CDE T2; production OIDC BFF
501. Git не шлёт почту и не закрывает OA-20/OA-22/OA-25.

Issues **#40 / #41 / #44** — не закрывать без живого доказательства.

## 4. Гвозди этого прохода

- `test_rt_customer_blocker_honesty_lock.py` — live src без «Checkpoint remains NO_GO»
- `test_build_customer_review_pack.py` — omitted `authoritative` → `False`
- `ergonomics-contract.test.ts` — `.capability-skip-banner` и `.hitl-readonly-note`

## 5. Финал

Checkpoint **GO** (`regulatory_measurement_mvp`); `customer_go` **false**.
PR #47 на `main`. Этот проход чинит fail-open пакета, живую NO_GO-речь и
рассинхрон pin-копий. Не основание объявлять приёмку, SLA, точность >90%,
MEP delivered или CDE-ready BCF.
