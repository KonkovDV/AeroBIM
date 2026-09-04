<!-- claims-lint: allow-file reason="RT-001 dual-rater protocol rehearsal; simulated passes; humans stay 0; closes_rt001 false; NO_GO" -->
---
title: "RT-001b protocol rehearsal — two simulated independent passes"
date: "2026-09-04"
checkpoint: GO
customer_go: false
closes_rt001: false
independent_human_raters: 0
llm_counts_as_rater: false
claim_level: protocol_rehearsal_not_human
claim_boundary: "Two simulated independent passes on the same in-repo fixture units. Not two human raters. LLM is not a rater. Fixture author is not counted twice. corpus_kind stays synthetic. closes_rt001 stays false. PrecisionClaim.publishable stays false. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
---

# RT-001: симуляция двух независимых проходов

Это **репетиция протокола** на учебном комплекте, не двое людей и не разметка LLM. Оба прохода видят те же `finding_id`. κ/α/AC1 считает `aerobim.domain.eval_statistics.agreement_artifact`.

- Checkpoint: **GO**
- closes_rt001: **false**
- independent_human_raters: **0**
- llm_counts_as_rater: **false**
- `b_protocol_rehearsal`: **CLOSED**
- `b_criterion_dual_rater`: **OPEN**
- n: **28** (пилот протокола ≤30)
- Cohen κ: **0.705263** (порог 0.60)
- Krippendorff α: **0.706927** (порог 0.67)
- Gwet AC1: **0.869413** (порог 0.60)
- raw agreement: **0.8929**
- расхождений: **3**
- CSV: `samples/benchmarks/detection-precision/rt001-dual-rater-simulation.csv`

- Проход A (`sim-rater-a`): strict planted-gold: TP if the frozen contract says the defect is real and expected; FP if excluded/control; FN if unresolved or known miss
- Проход B (`sim-rater-b`): conservative evidence: TP only with machine-checkable evidence (GUID / IDS / canonical LOAD / inventory rule); geometric pipe-vs-wall is not system MEP; free-text narrative is out of сверка

Расхождения (ожидаемы; иначе κ=1.0 не независимость):

`SYNTHETIC-AR-001-01`, `planted_federated_pipe_vs_wall`, `LB-004-freetext-area-mutation`

| A/B | n |
|---|---|
| `FN/FN` | 2 |
| `FN/FP` | 1 |
| `FP/FP` | 2 |
| `TP/FP` | 2 |
| `TP/TP` | 21 |

Инструкция людей: `docs/pilot/EXPERT_LABELING_INSTRUCTION_2026.md`. Когда появятся двое живых разметчиков на комплекте заказчика, этот CSV не подменяется: заводится новый журнал с человеческими `adjudicator_id`.
