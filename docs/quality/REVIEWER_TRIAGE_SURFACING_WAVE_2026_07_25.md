---
title: "Reviewer triage surfacing (HTML + review shell)"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Presentation only: band chips and ordering never change severity or summary.passed. Checkpoint stays NO_GO."
---

# Wave G — Reviewer triage surfacing (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Clash relevance triage | Ailem et al. 2026 (*Automation in Construction*); Koo et al. 2026 (*ASCE JCEM*) — triage must reach the reviewer, not just the data model |
| RU norms research | ПП РФ №715 + НИЦ ЦПС: реестр требований переведён в машиночитаемый формат (12.2025), методобеспечение опубликовано; **публичной XML-схемы СП пока нет** → импортёр норм не строим (не изобретаем формат; RT-002 остаётся клиентским) |

## Delivered (code + test)

Backend (`presentation/http/report_html.py`):
- `spatial` category section labeled "Spatial / Clash Coordination" (was raw key).
- Triage band chip next to severity, parsed from `evidence_refs`
  (`triage:band=…`) with a **strict allowlist** (critical/major/minor/negligible)
  — unknown/injected values are never reflected into markup (XSS-safe by
  construction, verified by test).
- Band chip CSS; issues already ordered by stamped priority (Wave B boost).
- `tests/test_report_html_triage.py` — 4 tests incl. allowlist/XSS and
  priority ordering.

Frontend (review shell):
- `triageBand()` helper (same allowlist), band chip in issue cards
  (`.triage-band-*` styles).
- Issue list now sorted priority-desc (stable; ties keep report order) —
  reviewer sees critical clashes first; original indexes preserved so
  selection/viewer focus semantics unchanged.
- `App.test.tsx`: new test — chips render with correct classes, critical card
  precedes negligible. Vitest **26 passed**, `npm run build` OK.

## Explicitly NOT claimed

- No ML relevance model (RT-001); no new verdict semantics; HITL flow unchanged.
- RU machine-readable norms importer — deferred until an official public XML
  schema for СП exists (tracked as research anchor only).

## Gate evidence (2026-07-25 local)

Backend: `ruff format --check` 319 files PASS · `ruff check` PASS · `mypy src`
192 files PASS · `pytest tests -q` **962 passed, 7 skipped**.
Frontend: vitest **26 passed** · `npm run build` OK.
