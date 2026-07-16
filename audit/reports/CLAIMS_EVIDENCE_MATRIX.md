# Claims × Evidence Matrix

| Claim | Evidence | Corpus | Reproducible | Risk | Allowed wording |
|---|---|---|---|---|---|
| LOC / tests at freeze | `audit/evidence/audit-baseline.json` | n/a | Yes | MED | Measured at freeze SHA |
| extraction macro_f1≈0.86 | evaluate_extraction | fixture | Yes | HIGH if sold as accuracy | Fixture F1 only; not product accuracy |
| точность >90% | None | none | No | BLOCKER | **FORBIDDEN** until customer+2 adjudicators + κ/α |
| Full norm checking | synthetic packs | synthetic | Partial | BLOCKER | Утверждённый пакет: **НЕТ** |
| MEP clash | mep scaffold + honesty surface | none | No | BLOCKER | NOT VERIFIED (`/v1/system/capabilities`) |
| DWG analysis | honesty surface MISSING | none | No | HIGH | НЕ РЕАЛИЗОВАНО |
| SLA ≤30 min customer | schema 1.2 fixture pack only | fixture | Yes | HIGH | Fixture wall-clock only; customer НЕ ДОКАЗАНО |
| BCF structural ZIP | `bcf-structural-handoff-2026-07-17.json` + dual consumers | synthetic | Yes | MED | Structural OK; CDE import НЕ ДОКАЗАНО |
| BCF ready for CDE | No import artifact | none | No | HIGH | **FORBIDDEN** until T2 evidence |
| Checks calculations | OpenRebar digest + claim_labels | fixture | Partial | HIGH | Сверка PARTIAL; correctness НЕ РЕАЛИЗОВАНО |
| Understands drawings (CV) | honesty `cv_human_level=missing` | none | No | BLOCKER | НЕ РЕАЛИЗОВАНО |
| External academic audit | self evidence + display_label guard | n/a | Yes | HIGH | internal self-audit only |
| Production-ready | ACL + fail-closed P0; customer gates false | mixed | Partial | HIGH | НЕ ДОКАЗАНО (checkpoint NO_GO) |
| Solibri replacement | explicit disclaimer in pilot-claim-boundary | n/a | Yes | LOW if held | Do not claim replacement |
| Platform / automated compliance | marketing tone risk | mixed | n/a | HIGH | “Bounded openBIM validation pilot; not full compliance engine” |

Inventory JSON: [`../evidence/claims-inventory.json`](../evidence/claims-inventory.json)  
Intake gate (all false): [`../evidence/customer-intake-gate.json`](../evidence/customer-intake-gate.json)
