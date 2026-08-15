---
title: "Red Team — Task 3 Exp B completeness @ 681b651"
date: 2026-08-05
auditor: internal
head_at_audit: "681b651"
head_after_fix: "this commit"
claim_boundary: "Honesty / speech-sync audit. Not product accuracy. Checkpoint NO_GO."
---

# Red Team — Task 3 / Exp B (после `681b651`)

Метод: чтение Friday/demo/baseline vs Exp B SSOT.

## Verdict

| Класс | До фикса | После фикса |
|---|---|---|
| CRITICAL | Friday packs: КР **0%** / **25 п.п. комплект** | **CLOSED** — ≈8,3% / ≈33% условно |
| HIGH | #3/#24 overclaim human wording; demo/baseline stale | **CLOSED** — narrowed openers + sync |
| MEDIUM | Exp B L26 «0%»; TASK3 head; TASK0 A10 | **CLOSED** |
| Residual | `baseline-2026-08.pdf` binary lag | **ACCEPTED** — regen PDF owner/CI |

## Findings → disposition

| ID | Sev | Fix |
|---|---|---|
| RT-T3-C1 | CRITICAL | `TRACKER_FRIDAY_OPENING` + opening 45s → ≈8% / Task 3 |
| RT-T3-H1 | HIGH | Exp B #3 opener: PD↔RD values, не «ТЧ≠лист» |
| RT-T3-H2 | HIGH | Exp B #24 opener: наличие разделов, не «графика увязана» |
| RT-T3-H3 | HIGH | `TRACKER_MEETING_PACK`, `demo-format`, `baseline-2026-08.md` |
| RT-T3-M1–M3 | MED | Exp B caveat; TASK3 `head: 681b651`; TASK0 A10 partial |

## Confirmed PASS

- Ports +0 in Task 3 commit  
- AUTHOR_CLAIM / не precision / не «25 п.п. закрыты» в SSOT  
- Tests 4 OK  
- Peer names / funnel на live paths — чисто  

## Residual

1. Пересобрать `baseline-2026-08.pdf` из обновлённого MD.  
2. ПНСТ 909 pin — у владельца.

## Reproduce

```text
rg -n "обнаруживается» 0|ноль из двадцати|25п\.п\. комплект|КР \*\*0 %\*\*" docs/quality docs/demo-format-2026-08.md docs/evidence/baseline-2026-08.md
# expect: no live speech hits
rg -n "≈8,3|около восьми|Не говорить «закрыли 25" docs/quality docs/evidence docs/demo-format-2026-08.md
```
