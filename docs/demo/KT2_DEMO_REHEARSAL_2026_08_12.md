<!-- claims-lint: allow-file reason="Demo rehearsal script; non-claim boundaries" -->
---
title: "КТ#2 — репетиция демо 30–40 мин"
date: "2026-08-12"
claim_boundary: "Rehearsal script. Fixture GO. Checkpoint NO_GO."
---

# Demo rehearsal (30–40 min)

## Minute plan

| Min | Open | Say |
| --- | --- | --- |
| 0–3 | [`KT2_HANDOFF_COVER_2026_08_11.md`](KT2_HANDOFF_COVER_2026_08_11.md) | Fixture ready; checkpoint NO_GO |
| 3–8 | [`KT2_JURY_FAQ_2026_08_12.md`](KT2_JURY_FAQ_2026_08_12.md) | Speech bounds |
| 8–15 | `docs/evidence/kt2-handoff-2026-08-11/STATUS.json` + `VERIFY.json` | Automated L1 gate green |
| 15–22 | `wall-guid/report.html` | Shared-gate honesty; passed=false / BLOCKED |
| 22–28 | `vertical-slice/slice-summary.json` + LIMITATIONS | Text-layer / not CV |
| 28–32 | clash STATUS + overlay PNGs | AABB n=6; two deterministic zones |
| 32–36 | `bcf-t1/bcf-structural-handoff.json` | T1 OK; CDE NOT_VERIFIED |
| 36–40 | Ask list → Samolet | Corpus, pack, 2 experts, CDE T2 |

## Commands before the meeting

```powershell
cd backend
python -m aerobim.tools.verify_kt2_handoff --write-status ../docs/evidence/kt2-handoff-2026-08-11/VERIFY.json
```

Expect exit **0** and `checkpoint_verdict=NO_GO`.
