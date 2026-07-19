# Claims × Evidence Matrix

**Refresh:** 2026-07-19 Red Team docs pass. Author: self. Checkpoint: **NO_GO**.

| Claim | Evidence | Corpus | Reproducible | Risk | Allowed wording |
|---|---|---|---|---|---|
| LOC / tests baseline | `docs/evidence/runtime-baseline-latest.json` | fixture | Yes | MED | Measured fixture baseline; refresh via export tool |
| extraction macro_f1≈0.86 | evaluate_extraction | fixture | Yes | HIGH if sold as accuracy | Fixture F1 only; not product accuracy |
| точность >90% | None | none | No | BLOCKER | **FORBIDDEN** until customer+2 adjudicators + κ/α |
| Full norm checking | synthetic packs | synthetic | Partial | BLOCKER | Утверждённый пакет: **НЕТ** |
| MEP clash | mep scaffold + honesty surface | none | No | BLOCKER | NOT VERIFIED (`/v1/system/capabilities`) |
| DWG analysis | honesty surface never OK | none | No | HIGH | НЕ РЕАЛИЗОВАНО as product DWG |
| SLA ≤30 min customer | schema 1.2 fixture pack only | fixture | Yes | HIGH | Fixture wall-clock only; customer НЕ ДОКАЗАНО |
| BCF structural ZIP | `bcf-structural-handoff-2026-07-18.json` + dual consumers | synthetic | Yes | MED | Structural OK; CDE import НЕ ДОКАЗАНО |
| BCF ready for CDE | No import artifact | none | No | HIGH | **FORBIDDEN** until T2 evidence |
| Checks calculations | OpenRebar digest + claim_labels | fixture | Partial | HIGH | Сверка PARTIAL; correctness НЕ РЕАЛИЗОВАНО |
| Understands drawings (CV) | honesty `cv_human_level=missing` | none | No | BLOCKER | НЕ РЕАЛИЗОВАНО |
| External academic audit | self evidence + display_label guard | n/a | Yes | HIGH | internal self-audit only |
| Production-ready | ACL + fail-closed; intake gates false | mixed | Partial | HIGH | НЕ ДОКАЗАНО (checkpoint NO_GO) |
| Fail-closed required clash | P0 + production/pilot sign-off profile | fixture | Yes | LOW | SKIPPED→FAILED under policy |
| Finding provenance | persist reject + stamps | fixture | Yes | LOW | Mandatory `finding_id`/`evidence_refs` |
| Object ACL | principal vs tenant_id | fixture | Yes | LOW | Cross-tenant **404** when enforced |
| Production sign-off default | settings + Dockerfile/compose | fixture | Yes | LOW | Non-dev defaults production profile |
| SSRF outbound guard | `outbound_url.py` + remediation tests | fixture | Yes | LOW | JWKS/bSI/OpenCDE guarded |
| Shared-gate `summary.passed` | ADR-001 + EvidenceAssembler | fixture | Yes | MED if misread | Technical Shared-gate ≠ Published |
| Solibri replacement | disclaimer in pilot-claim-boundary | n/a | Yes | LOW if held | Do not claim replacement |
| Platform / automated compliance | marketing tone risk | mixed | n/a | HIGH | “Bounded openBIM Shared-gate assistant; not full compliance engine” |

Inventory JSON: [`../evidence/claims-inventory.json`](../evidence/claims-inventory.json)  
Intake gate (all false): [`../evidence/customer-intake-gate.json`](../evidence/customer-intake-gate.json)  
Open blockers / checkpoint: [`CRITICAL_BLOCKERS.md`](CRITICAL_BLOCKERS.md)
