# Claims × Evidence Matrix

| Claim | Evidence | Corpus | Reproducible | Risk | Allowed wording |
|---|---|---|---|---|---|
| LOC ~14.7K / 425+ tests | Measured src 15290 LOC; 439 collected / 436 passed | n/a | Yes (`generate_audit_baseline.py`) | MED — maturity theatre | “Measured at audit freeze; dirty tree may differ from README” |
| extraction macro_f1≈0.86 | evaluate_extraction | fixture | Yes | HIGH if sold as accuracy | Fixture F1 only; not product accuracy |
| точность >90% | None | none | No | BLOCKER | **FORBIDDEN** until customer+2 adjudicators |
| Full norm checking | synthetic packs | synthetic | Partial | BLOCKER | Утверждённый пакет: **НЕТ** |
| MEP clash | mep scaffold + generic clash | none | No | BLOCKER | NOT VERIFIED |
| DWG analysis | docs say missing | none | No | HIGH | НЕ РЕАЛИЗОВАНО |
| SLA ≤30 min | measure_package_sla tool | fixture | Partial | HIGH | НЕ ДОКАЗАНО for customer package |
| BCF ready | ZIP exporters + unit consumers | synthetic | Unit only | HIGH | Export yes; CDE import НЕ ДОКАЗАНО |
| Checks calculations | OpenRebar digest / numeric compare | fixture | Partial | HIGH | Сверка PARTIAL; correctness НЕ РЕАЛИЗОВАНО |
| Understands drawings (CV) | OCR extra absent; CV missing | none | No | BLOCKER | L0 PARTIAL; L2–L4 НЕ РЕАЛИЗОВАНО |
| External academic audit | self evidence + display_label guard | n/a | Yes | HIGH | internal self-audit only |
| Production-ready | boto3 absent; FE tests fail; no tenant ACL | n/a | No | BLOCKER | НЕ ДОКАЗАНО |
| Solibri replacement | explicit disclaimer in pilot-claim-boundary | n/a | Yes | LOW if held | Do not claim replacement |
| Platform / automated compliance | marketing tone risk | mixed | n/a | HIGH | “Bounded openBIM validation pilot; not full compliance engine” |

Inventory JSON: [`../evidence/claims-inventory.json`](../evidence/claims-inventory.json)
