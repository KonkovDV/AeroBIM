<!-- claims-lint: allow-file reason="Architecture re-audit scorecard; forbidden phrases as non-claims; Checkpoint NO_GO" -->
---
title: "Re-Audit #2 — полная перепроверка архитектуры после волны фиксов 2"
status: active
version: "1.1.0"
last_updated: "2026-08-16"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Audit only. Checkpoint NO_GO; RT-001/002/003 OPEN.
  Scorecard of 11 HD rounds against HEAD 3ca6b21 plus remainder close-out on this pass.
audited_head: "3ca6b21"
auditor: "ZCode, triage × Red Team, финальная перепроверка «от и до»"
---

# Re-Audit #2 — скорборд

## Результат: 13 из 13 позиций закрыты корректно (1 by-design задокументирован), 0 регрессий

| ID | Статус | Доказательство |
|---|---|---|
| HD8-TOOL-01 | **FIXED+** | `export_moexp_ids_coverage.py`: явные `STATUS_PASS/FAIL/UNSUPPORTED/LOAD_ERROR/UNKNOWN`, строгие `==` |
| HD7-IDS-03 | **FIXED+** | `ifc_tester_ids_validator.py`: `spec_status is True` + страховка `is not True` без issues |
| HD7-IFC-01 | **FIXED** | `_to_float`: bool-guard, int/float напрямую, строки → `parse_localized_number` |
| HD11-NUM-01 | **FIXED** | сервисный `to_float` → `parse_localized_number` (`56cebf1`) |
| HD11-XDOC-02a | **FIXED** | `normalize_unit_token` во всех трёх точках |
| HD10-XDOC-01 | **FIXED+** | `si_compare` → `SOFT_CONFLICT_WITHIN_TOLERANCE`; never HARD on equal values |
| HD10-FE-01 | **FIXED** | 2× AbortController в App.tsx |
| HD2-UP-01 | **FIXED** | reserve-first; 415/422/413 оставляют `bytes_used=0`, `upload_count=0`, без holds |
| HD3-BFF-01 | **FIXED** | непроверенные lab-сессии не становятся `AuthPrincipal` |
| HD9-VER-01 | **FIXED** | `--day` default = `latest` (`DEFAULT_RELEASE_EVIDENCE_DAY`); пустой/`None` → max dated `release-status-*.json`; нет dated → fail-closed |
| HDX-LINT-01 | **FIXED** | directory blinds сняты; scan = git-tracked; `RED_TEAM` / `ENGINEERING_STATUS` / `COMPETITIVE_MATRIX` остаются fragment-exclude |
| HD2-RL-02 | **BY-DESIGN** | `0` = off только в development (boot WARNING). `samolet_pilot` / `production` reject `<=0` at Settings boot (default 120) |
| HD-серия (закрытые ранее) | **OK** | редискшейпов не найдено |

## Вердикт

Вторая волна фикс-дисциплины закрыта. Публичный пак почищен от кухни. Регрессий честности не обнаружено; вердикт-контур не затронут.

**Остаток до нуля:** нет (HD2-RL-02 = by-design, задокументирован в Accepted Risks + Settings).

Checkpoint stays **NO_GO**. `closes_rt001: false`. `closes_rt002: false`. `closes_rt003: false`.
