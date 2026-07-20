# CDE import proof (RT-008 Tier 2)

**Status:** `NOT_VERIFIED`

Tracked gate for independent evidence that an AeroBIM BCF ZIP (or BCF-API
push) imported successfully into a customer CDE.

Sensitive screenshots/logs may live in the gitignored mirror
`docs/evidence/internal/cde-import-proof/` — this tracked folder must still
receive a `STATUS.json` flip to `VERIFIED` plus hash references.

## Required before claiming “BCF ready for CDE”

| File | Purpose |
|------|---------|
| `import-log.txt` or tool export log | Timestamped import success/failure |
| screenshot / PDF (path referenced in STATUS) | Topics visible in CDE UI |
| `STATUS.json` | Machine gate (`status` must become `VERIFIED`) |
| `T2_EVIDENCE_TEMPLATE.json` | Empty field template — fill only with real pilot evidence |
| `hashes.json` | SHA-256 of BCF ZIP + screenshot + log |

Do **not** invent screenshots. Until real pilot import lands, keep
`STATUS.json` at `NOT_VERIFIED`.

Ladder taxonomy: [`docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md`](../../../docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md)
(T0 export → T1 structural → **T2 CDE import** → T3 round-trip → T4 production).

## Upstream

- Structural T1: `audit/evidence/bcf-structural-handoff-2026-07-18.json`
- CDE claim rule: keep `STATUS.json` at `NOT_VERIFIED` until real import evidence lands
- Allowed wording: **structural ZIP AVAILABLE**; **CDE NOT_VERIFIED**
