---
title: "Red Team — KT#2 Friday pack (post-99d7167 remediation)"
date: 2026-08-05
auditor: agent
head_at_audit: "99d7167"
head_after_fix: "this commit"
claim_boundary: "Honesty / leak / claims audit. Not product accuracy. Checkpoint NO_GO."
---

# Red Team — пятничный пакет КТ#2

Аудит публичной поверхности после коммита `99d7167` (Exp B AR/VK, baseline, press registry).  
Метод: чтение SSOT + grep на claims lock / воронку / имена конкурентов / Segment E.  
Subagent: [Red Team KT2 pack](94501350-04b4-4a70-92cb-081a25a463eb).

## Verdict

| Класс | До фикса | После фикса (этот коммит) |
|---|---|---|
| CRITICAL | C1 funnel 0/0/0+28 public; C2 speech «работает сразу»; C3/C4 names | **CLOSED** на K0 path + Exp B speech + QWEN/LOI/docs.md/NOVATOR |
| HIGH | stale K0 vs Exp B; Exp A oversell; SHA pin | **CLOSED** |
| MEDIUM | n=12 fragility on K0; baseline alias | **MITIGATED** |
| Residual | TZ_V3_RED_TEAM named matrix (historical audit doc) | **ACCEPTED residual** — матрица аудита ТЗ, не Friday speech |

## Findings → disposition

| ID | Severity | Finding | Fix |
|---|---|---|---|
| C1 | CRITICAL | Live `0/0/0`, **28** orgs in `TRACKER_*` on GH | Public templates: placeholders / owner-at-send; kitchen stays `.local` |
| C2 | CRITICAL | Exp B speech «работает сразу / из коробки» | Rewritten: coverage status + AUTHOR_CLAIM + n fragility |
| C3 | CRITICAL | NormaChecker/WAIVE/AIDOX in QWEN feasibility | Anonymized to peer classes |
| C4 | CRITICAL | А101/Галс in NOVATOR pack | «другие девелоперы-партнёры» |
| H1 | HIGH | K0 omit Exp B AR/VK | MEETING_PACK + OPENING updated |
| H2 | HIGH | Speech ignored Киров≠Мордовия | Half-sentence in Friday script |
| H3 | HIGH | «2 эталона» / Минстрой as runnable | Exp A **NOT_RUN** explicit |
| H4 | HIGH | End on «лучшем» 25% | Speak all three; ban «лучшая точность» |
| H5 | HIGH | baseline SHA `a0c07ff` stale | Pin `99d7167` |
| H6 | HIGH | «пятёрка» in LOI/docs.md | Selection language + mos.ru |
| R1 | residual | Named peers in `TZ_V3_RED_TEAM_2026_07_30.md` | Left: historical red-team matrix; not K0 speech |

## Confirmed PASS (do not reverse)

- Exp A NOT_RUN; no synthetic-as-Minstry  
- Claims: no product >90%, no customer SLA, no MEP=OK as delivered  
- `.local` not tracked (`git ls-files .local` empty)  
- Public `qa-defense` without competitor names  
- Press registry: program ≠ project; mos.ru primary  
- Anti-cherry-pick: KR first despite worst product fit  

## Residual risk (owner)

1. Historical `TZ_V3_RED_TEAM` still names peers — move to `.local` only if jury path links it.  
2. `.local` backup on same volume C: — still needs off-disk copy.  
3. Funnel numbers must not be re-committed to GH when owner fills chat.

## Reproduce

```text
git log -1 --oneline
rg -n "0 / 0 / 0|работает сразу|NormaChecker|А101" docs/quality docs/evidence docs/partners docs/qa-defense-2026.md docs/architecture/QWEN38_AEROBIM_FEASIBILITY_2026_08_03.md
```
