# Sprint 2.1 final audit

**audit_date:** 2026-07-31  
**meeting:** `DATE_TO_BE_CONFIRMED`  
**start_state:** `audit/sprint-2-1-start-state.json`

## Acceptance checklist (technical)

| Criterion | Status | Evidence |
|---|---|---|
| Dataset manifest + hashes | DONE | `samples/benchmarks/sprint-2-1/manifest.json` |
| Public/synthetic baseline package | DONE | `baseline-package.json` |
| Mutation ground truth SSOT | DONE | `mutations/mutation-manifest.json` |
| Reproducible baseline CLI | DONE | `aerobim.tools.run_sprint_2_1_baseline` |
| JSON + Markdown artifacts | DONE | `artifacts/sprint-2-1/` |
| PDF | PDF_GENERATION_BLOCKED | Markdown/HTML only |
| Fixture vs customer claims split | DONE | claim_level fields |
| Samolet TZ traceability table | PARTIAL | in baseline JSON `tz_traceability` |
| Customer demo protocol | DONE | `docs/customer-demo/` |
| Severity draft | DONE | `PROPOSED_NOT_CUSTOMER_APPROVED` |
| Leads + drafts | DONE | contacted=0 |
| LLM provider abstraction | DONE | `domain/llm_advisory.py` |
| Mock Kimi/Qwen/Gemma tests | DONE | backend/tests/test_llm_* |
| Evidence-bounded + injection + invariance | DONE | tests |
| Research-to-code map | DONE | `docs/research/` |
| CI gates | DONE | `sprint-2-1-gates` job |
| Claims Lock update | DONE | CLAIMS_LOCK + claims-boundary |
| RT-001/002/003 not closed | HOLD | CRITICAL_BLOCKERS |

## Go / No-Go

| Gate | Verdict |
|---|---|
| Software update (Sprint 2.1 engineering rails) | `GO_WITH_LIMITATIONS` |
| Customer sign-off | `NO_GO` |

## Limitations

- Baseline CLI reports declared mutation inventory + pack hash timing; full TP/FP/FN requires mutation-apply + Analyze (explicitly null).
- Open third-party IFC corpora not vendored (`INTERNAL_ONLY_LICENSE_REVIEW`).
- No live cloud LLM calls in CI.
- No customer outreach executed.
