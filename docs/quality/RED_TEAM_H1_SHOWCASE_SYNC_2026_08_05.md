---
title: "Red Team — Horizon-1 Step1 showcase sync @ 9b06a93"
date: 2026-08-05
auditor: agent
head_at_audit: "9b06a93"
head_after_fix: "this commit"
claim_boundary: "Honesty / leak / claims audit. Not product accuracy. Checkpoint NO_GO."
subagent: "46f1b07a-8a91-4d38-beb3-b2587289efde"
---

# Red Team — витрина H1 Step1 (после `9b06a93`)

Метод: scoped grep Claims Lock + чтение README / docs.md / NOVATOR / TRACKER / Exp B + subagent [Red Team showcase](46f1b07a-8a91-4d38-beb3-b2587289efde).

## Verdict

| Класс | До фикса | После фикса (этот коммит) |
|---|---|---|
| CRITICAL | Peer names в `TZ_V3_RED_TEAM` | **CLOSED** — peer A–D / классы |
| HIGH | `AI Project Control` в QWEN feasibility; live `0/0/0`+28 в WAVE2 | **CLOSED** |
| MEDIUM | Pitch title «Новатор» без disclaimer; Friday C3 overstated CLOSED | **CLOSED** |
| Residual | Meta-таблицы RT с именами в истории; `claims_forbidden_wording.json` только README | **ACCEPTED** — audit trail / gate gap |

## Findings → disposition

| ID | Sev | Finding | Fix |
|---|---|---|---|
| RT-H1-C1 | CRITICAL | `TZ_V3_RED_TEAM` матрица с AIDOX/WAIVE/AI Project Control/NormaChecker | Peer A–D + классы осей атаки |
| RT-H1-H1 | HIGH | QWEN L76 «AI Project Control» | «Участник той же задачи №7» |
| RT-H1-H2 | HIGH | WAVE2 публикует `0/0/0` и **28** orgs | Kitchen-only wording |
| RT-H1-M1 | MED | `` без «не заявка 2026» | Banner + переименование смысла |
| RT-H1-M2 | MED | Friday pack заявил C3 CLOSED при residual | C3 → PARTIAL→CLOSED здесь |
| RT-H1-M3 | MED | Forbidden-wording CI только README | Accepted residual (optional later) |

## Confirmed PASS (не откатывать)

- README порядок: пример → работает → где → NO_GO → глубина  
- `docs/docs.md` v1.2: календарь КТ#2/#3/финал; «Новатор» 2026 закрыт  
- Exp B = coverage map / AUTHOR_CLAIM ≠ product accuracy  
- Public TRACKER_* — placeholders, не live funnel  
- Public `qa-defense` без имён участников задачи №7  
- Segment E имена отсутствуют в live partner packs  
- `.local` не tracked (`git ls-files .local` = 0)  
- `AEROBIM_DOCUMENTED_ENV` EN↔RU↔Configuration↔baseline + CI `--check-readme`  
- Нет affirmative >90% / DWG-ready / MEP delivered / customer ≤30 на витрине  

## Residual (владелец)

1. Копия `.local` вне диска C:.  
2. Не коммитить live funnel в GH.  
3. Опционально: CI deny-list имён peer / Segment E по `docs/`.  

## Reproduce

```text
git log -1 --oneline
rg -n "NormaChecker|WAIVE|AIDOX|AI Project Control|А101|Галс|0 / 0 / 0" docs README.md README.ru.md
# expect: only historical meta in older RT tables if any; TZ_V3/QWEN/WAVE2 cleaned
```
