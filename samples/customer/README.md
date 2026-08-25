# Customer corpus (gitignored)

Place NDA-bound customer packages here only. Paths under `samples/customer/`
are ignored by git except this README.

Do **not** commit IFC, drawings, or labels from Samolet / customer pilots.

Share channel received 2026-08-25 (NDA). The locator is **not** stored in this public tree after the 25.08 Red Team pass. Owner keeps it outside git.

Owner downloads locally (`.local/samolet/` or gitignored `files/`). A URL does **not** flip intake gates.

## Checklist before flipping intake gates

1. Dual human adjudicators (LLM does not count)
2. Measure κ/α: `aerobim-measure-adjudicator-agreement --csv …`
3. Validate gate: `aerobim-validate-customer-intake-gate`
4. Checkpoint stays **NO_GO** until RT-001/002/003 evidenced in Claims Lock
