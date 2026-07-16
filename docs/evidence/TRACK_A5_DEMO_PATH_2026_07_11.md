---
title: "Track A5 — Demo path upload→analyze→BCF"
status: complete-engineering
delivered_at: "2026-07-11"
tags: [aerobim, demo, bcf, openbim, track-a]
---

# Track A5 — Demo path (2026-07-11)

Closes the highest-value **no-corpus** gap after A1–A3: a repeatable
TechLab demo loop on the Moscow fixture pack, aligned with buildingSMART
openBIM practice (IDS check → BCF-XML 2.1 file handoff; BCF-API = escalation).

## Было / стало

| Item | До A5 | После A5 |
|---|---|---|
| Demo script | разрозненные smoke / SLA / curl | один CLI `aerobim-run-demo-path` |
| Upload proof | отдельный P0 тест | в том же прогоне, что analyze+BCF |
| BCF gate | export tests | ZIP **structural smoke** (`VersionId` + GUID-folder markup + Topic) in demo evidence |
| Operator docs | smoke-path + CDE handoff | + `docs/ops/demo-path-runbook-2026.md` with forbidden claims |
| Claim honesty | вручную помнить | JSON `loop_ok` vs `analyze_passed` + `claim_boundary.proven` / `not_proven` |

## Atomic delivery

- **Tool:** `backend/src/aerobim/tools/run_demo_path.py` + console script
- **Tests:** `backend/tests/test_run_demo_path.py`
- **Ops:** `docs/ops/demo-path-runbook-2026.md`
- **Evidence:** this note

## Non-goals (unchanged)

- Customer precision / >90%
- CDE import proof
- MEP system clash
- CV/LLM sign-off

## Verification

```powershell
cd backend
python -m pytest tests/test_run_demo_path.py -q
python -m aerobim.tools.run_demo_path --output ..\docs\evidence\demo-path-pilot-moscow-2026-07-11.json
```
