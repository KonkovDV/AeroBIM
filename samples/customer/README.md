# Customer corpus (gitignored)

Place NDA-bound customer packages here only. Paths under `samples/customer/`
are ignored by git except this README.

Do **not** commit IFC, drawings, or labels from Samolet / customer pilots.

## Checklist before flipping intake gates

1. Follow `docs/ops/intake-precision-runbook-2026.md`
2. Dual human adjudicators (LLM does not count)
3. Measure κ/α: `aerobim-measure-adjudicator-agreement --csv …`
4. Validate gate: `aerobim-validate-customer-intake-gate`
5. Checkpoint stays **NO_GO** until RT-001/002/003 evidenced in Claims Lock
