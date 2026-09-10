<!-- claims-lint: allow-file reason="Accuracy-answer artifact; TZ 90% quoted as criterion not claim; NO_GO" -->
---
title: "Accuracy answer — fixture/open-corpus numbers, not product %"
date: "2026-09-09"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
---

# Ответ на критерий «точность >90 %»

Это методика и числа с границей переноса, не точность продукта.
На комплекте заказчика не измеряли.

| id | metric | n | corpus_kind | чем не является |
|---|---|---:|---|---|
| fixture_aabb_clash | precision_recall | 6 | fixture | customer corpus; TZ clash accuracy >90%; IfcClash mesh product |
| defect_injection_recall | mutation_kill_recall | 8 | synthetic | semantic TP; customer-pack recall |
| open_corpus_binary_match | binary_match_rate | 7 | open_corpus | TP/FP; product accuracy; summary.passed as a quality score |
| dual_rater_simulation | agreement | 28 | synthetic | two human raters; LLM-as-rater; RT-001 closed |
| typical_error_class_coverage | class_coverage | 26 | synthetic | precision; customer-confirmed typical-error gold |

## Чтобы измерить на комплекте заказчика

- labeled customer corpus with finding-level gold
- two named human raters
- blinding / independent passes
- held-out split
- coverage map hash frozen before labels

Checkpoint **GO**; `customer_go` false.

