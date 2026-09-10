<!-- claims-lint: allow-file reason="HD26 Red Team of red main CI and draft PR 51; Checkpoint GO; customer_go false; #40/#41/#44 OPEN" -->
---
title: "Триаж HD26 10.09.2026 — красный CI на main и черновик PR #51"
status: active
version: "1.0.0"
last_updated: "2026-09-10"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Red Team of origin/main after the PowerShell launcher commit. Checkpoint GO
  (regulatory_measurement_mvp). customer_go false. Not product accuracy. Not
  customer SLA. Issues #40 / #41 / #44 stay OPEN. PR #51 stays draft. Test
  counts live only in runtime-baseline-latest.json; do not remint locally.
auditor: "триаж × Red Team"
audited_head: "cca3dba1 plus the CI-venv launcher fix on this pass"
---

# Триаж HD26 — красный CI на main и черновик FE-CRUFT-02

Метод: `gh run` на `main@cca3dba1`, pytest-лог, черновик PR #51, живое дерево.
Лексика: **KILL / HOLD / ACCEPT**. `customer_go` **false**.

## 0. Итог

| ID | Verdict | Что |
|---|---|---|
| **HD26-CI-01** | **KILL; чинится в этом проходе** | CI и `backend-plan` красные: 2 failed / 3152 passed. `test_wrapper_finds_backend_venv_python` ходил в живой `backend/.venv`. В GitHub Actions venv нет. Второй тест падал на `main() → 1` до `subprocess.call`. |
| **HD26-P51-01** | **HOLD** | PR #51 (FE-CRUFT-02) — **черновик**, в заголовке «не мержить до показа 11.09». Автор сам цитирует HD25-CRUFT02-01. Не вливать этой ночью. Ветка пусть живёт. |
| **HD26-PS-01** | **ACCEPT уже на main** | PowerShell: `.\start.bat`, не `start` и не `start.bat`. `start.ps1` на origin. |
| **HD26-PIN-01** | **HOLD** | Pin `f9383efa` отстаёт от HEAD. Не чеканить локальным pytest. CI сам выложит attested JSON после зелёного `test`. |
| **HD26-I40-01** | **HOLD** | #40 / #41 / #44 OPEN. #51 их не закрывает. |

**OVERCLAIM: 0.** Недифференцированное CLOSED: 0.

## 1. Что этот проход делает

1. Лаунчер-тесты ходят в **фиктивное** дерево venv, не в CI-диск.
2. `main()` патчит `backend_venv_python` перед `subprocess.call`.
3. Речь HD26 + TIER0. PR #51 не merge.

## 2. Что **не** делать сегодня

- Не merge #51. Не заменять `window.confirm` на показе 11.09.
- Не закрывать #40 / #41 / #44.
- Не чеканить CI pin локальным vitest/pytest.
- Не говорить «фронт сдан».

## 3. Речь

Показ оболочки: `.\start.bat`. Показ жюри: `python -m aerobim.tools.run_kt3_jury`.
Checkpoint **GO**; `customer_go` **false**.
