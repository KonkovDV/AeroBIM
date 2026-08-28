# Customer corpus (gitignored)

Place NDA-bound customer packages here only. Paths under `samples/customer/`
are ignored by git except this README.

Do **not** commit IFC, drawings, or labels from Samolet / customer pilots.

Share channel received 2026-08-25 (NDA). The locator is **not** in this public tree after the 25.08 Red Team pass, the 26.08 jury-pack rewrite, and the 28.08 kitchen-literal rewrite of `main`. Owner keeps any locator outside git. GitHub copies, Actions logs, and forks are outside git and are not claimed purged.

Do **not** say the customer sent no data. The channel is received. A hashed pack is **not** in git. RT-001 stays OPEN.

Owner downloads locally (gitignored `files/`). A URL does **not** flip intake gates.

**26.08 owner:** rotating the old share locator and asking GitHub to purge rewritten SHAs are **not open checklist items**. This does not assert that an old URL returns 404, and it does not close RT-001.

## Checklist before flipping intake gates

1. Dual human adjudicators (LLM does not count)
2. Measure κ/α: `aerobim-measure-adjudicator-agreement --csv …`
3. Validate gate: `aerobim-validate-customer-intake-gate`
4. Checkpoint stays **NO_GO** until RT-001/002/003 evidenced in Claims Lock
