---
title: "BCF Evidence Ladder T0–T4"
status: active
date: 2026-07-21
last_updated: "2026-07-21"
claim_boundary: "Structural ZIP AVAILABLE; CDE import NOT_VERIFIED. Checkpoint NO_GO unchanged."
---

# BCF Evidence Ladder (T0–T4)

Canonical taxonomy for AeroBIM BCF interoperability claims. Engineering remediations
do **not** flip CDE product wording. Checkpoint remains **NO_GO**.

## Ladder

| Tier | Name | What it proves | Current status |
|---|---|---|---|
| **T0** | Export surface | HTTP/API can emit a BCF ZIP (2.1 default; 3.0 experimental) | **AVAILABLE** |
| **T1** | Structural + dual-consumer | ZIP schema members parse; ≥2 independent consumers agree on GUID/title/viewpoint | **EVIDENCED** (`audit/evidence/bcf-structural-handoff-2026-07-18.json`) |
| **T2** | Independent CDE import | Customer CDE imported the ZIP (or BCF-API push) with log + screenshot + hashes | **NOT_VERIFIED** (`audit/evidence/cde-import-proof/`) |
| **T3** | Round-trip fidelity | Topics/comments/viewpoints survive CDE → re-export without semantic loss | **NOT_STARTED** (blocked on T2) |
| **T4** | Production handoff | Repeated customer CDE imports under signed scope + ops runbook | **NOT_STARTED** (blocked on T2/T3) |

## Allowed / forbidden wording

| Allowed now | Forbidden until T2+ |
|---|---|
| BCF ZIP structural OK | BCF ready for CDE |
| Structural ZIP AVAILABLE | CDE interoperable |
| CDE import NOT_VERIFIED / НЕ ДОКАЗАНО | production BCF handoff |
| OpenCDE BCF API push = Foundation (not T2) | pilot CDE-certified |

## T2 evidence pack (template)

Tracked folder: `audit/evidence/cde-import-proof/`

| Artifact | Role |
|---|---|
| `STATUS.json` | Machine gate (`status` must be `NOT_VERIFIED` until real import) |
| `T2_EVIDENCE_TEMPLATE.json` | Empty field template — fill only with real pilot evidence |
| `import-log.txt` | Timestamped import success/failure (absent until real run) |
| `screenshot.png` / PDF | Topics visible in CDE UI (do **not** invent) |
| `hashes.json` | SHA-256 of BCF ZIP + screenshot + log |

Do **not** invent customer corpus, CDE screenshots, or SLA packs. Flip
`STATUS.json` to `VERIFIED` only with real hashes + present files.

## Related

- RT-008 in `audit/reports/CRITICAL_BLOCKERS.md` (PARTIAL)
- Claims lock: `audit/reports/CLAIMS_LOCK_2026_07_17.md`
- Capability matrix: `docs/capability-claim-matrix-2026.md`
- README public ladder table
