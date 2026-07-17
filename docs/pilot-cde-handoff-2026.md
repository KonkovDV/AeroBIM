---
title: "Pilot CDE BCF Handoff 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, pilot, bcf, cde, samolet]
---

# CDE / BCF handoff (Samolet 10/10 path)

## Evidence ladder (July 2026)

| Tier | Status | Artifact |
|------|--------|----------|
| T1 structural ZIP + dual consumers | **DONE** | [`../audit/evidence/bcf-structural-handoff-2026-07-17.json`](../audit/evidence/bcf-structural-handoff-2026-07-17.json) |
| T2 independent CDE import | **NOT_VERIFIED** | [`../audit/evidence/cde-import-proof/STATUS.json`](../audit/evidence/cde-import-proof/STATUS.json) |

Never claim “BCF ready for CDE” on T1 alone.

## Scenario A — BCF 2.1 ZIP (default, week 1)

| Step | Action | Owner | Done |
|------|--------|-------|------|
| A1 | Export BCF 2.1 from AeroBIM API | Operator | [ ] |
| A2 | Import ZIP into customer CDE | Samolet engineer | [ ] |
| A3 | Verify topics + descriptions (remark body) visible | Joint | [ ] |
| A4 | Store screenshot + log (gitignored `docs/evidence/internal/cde-import-proof/` OK) and flip tracked `audit/evidence/cde-import-proof/STATUS.json` to `VERIFIED` | Operator | [ ] |

Export:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  -o samolet-pilot.bcfzip \
  "https://<host>/v1/reports/<report_id>/export/bcf?version=2.1"
```

**Score when done:** CDE **9/10** (manual roundtrip proven).

## Scenario B — BCF API / OpenCDE (escalation only)

Trigger: CDE cannot import ZIP or requires API week 1.

| Step | Action |
|------|--------|
| B1 | Document CDE API requirements (auth, endpoints) |
| B2 | Add domain port `IBcfCoordinationAdapter` + adapter stub |
| B3 | Pilot MVP push/pull for agreed topic fields |

**Score when done:** CDE **10/10**.

Defer Scenario B to post-pilot branch A unless Samolet blocks on week 1.

## BCF 3.0 opt-in

Use only if CDE requires BCF 3.0: `?version=3` on export endpoint. Default remains **2.1**.

## Related

- [`pilot-case-study-report-2026.md`](pilot-claim-boundary-2026.md)
- Pre-pilot evidence: [`evidence/pre-pilot-bcf-handoff-2026-05-21.json`](evidence/pre-pilot-bcf-handoff-2026-05-21.json)
