---
title: "Red Team — week surface 2026-08-03→08-05"
date: 2026-08-05
auditor: agent
head_at_audit: "c8fe19f"
head_after_fix: "this commit"
claim_boundary: "Honesty / leak / speech-sync. Checkpoint NO_GO."
subagent: "fdc99b19-a275-470a-b865-7b86ae73073f"
---

# Red Team — недельная витрина (03–05.08.2026)

**Контекст:** `main` уже был на `origin` (`c8fe19f`); WT чистый. Аудит закрыл остатки после Task 3 / H1.

## Verdict

| Класс | До | После |
|---|---|---|
| CRITICAL | PDF baseline: КР 0% / 25п.п. комплект | **CLOSED** — regen + script text |
| HIGH | ENGINEERING_STATUS KR 0/42; SPRINT2 `28/0/0`; README 48/67/58 | **CLOSED** |
| MEDIUM | Exp B L55 «0% из коробки» как текущее | **CLOSED** |
| Residual | RED_TEAM meta с именами peer / 0/0/0 | **ACCEPTED** (audit trail) |

## Fixes in this commit

1. `generate_tracker_baseline_pdf.py` + regenerate `baseline-2026-08.pdf` / alias  
2. `ENGINEERING_STATUS` KR ≈8.3/≈33  
3. `SPRINT2_TRACKER_DELIVERY` funnel → kitchen only  
4. README EN/RU inventory **46 / 71 / 59**  
5. Exp B L55 historical wording  
6. TASK0 head/inventory note  

## Week already on origin (no re-push needed for history)

`c8fe19f` … `f825a06` — H1 showcase, Task 3, Friday RT, Exp B, jury pack, AECV, grant RT, etc. This commit is the week-closure honesty patch.

## PASS (не откатывать)

- Claims Lock affirmative bans  
- Novator 2026 closed framing  
- Friday MD speech ≈8,3%  
- `.local` untracked  
- documented_env CI gate  
- Peer names stripped from live tz/architecture/partners  

## Reproduce

```text
rg -n "из коробки 0%|25п\.п\. комплект|KR 0/42|28 SSOT orgs / 0 / 0|48 Protocol ports / 67" docs README.md README.ru.md
python -m aerobim.tools.generate_tracker_baseline_pdf
# PDF text must contain ≈8,3% not «из коробки 0%»
```
