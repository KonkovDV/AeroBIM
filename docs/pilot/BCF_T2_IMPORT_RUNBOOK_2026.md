---
title: "BCF T2 CDE-import runbook (pilot)"
status: active
version: "1.0.0"
last_updated: "2026-08-03"
claim_boundary: "Runbook only — executing it requires a real customer/pilot CDE session. T2 stays NOT_VERIFIED until the pack verifies (RT-008)."
---

# BCF T2 CDE-import runbook — Samolet pilot (2026)

Purpose: produce an **independent, hash-bound** proof that an AeroBIM BCF ZIP
imports into an external CDE. Consumer reality (Jul 2026): BIMcollab accepts
BCF **3.0** import since 2026-02-20; Trimble Connect imports BCF **2.1**.
Both exporters are XSD-validated locally against official buildingSMART
schemas (Waves C–E), so a T2 failure isolates consumer-side behavior.

**Eng readiness:** `python -m aerobim.tools.verify_bcf_t2_evidence --checklist`
prints required artifacts without flipping `claim_allowed`. Tracked
`audit/evidence/cde-import-proof/STATUS.json` remains **NOT_VERIFIED** until a
real CDE session supplies log + screenshot + hashes.

## Preconditions

1. Fresh T1 evidence: `python -m aerobim.tools.verify_bcf_structural_handoff`
   → `audit/evidence/bcf-structural-handoff-<date>.json` with
   `xsd_status="passed"` for both archives. Record both `sha256` values.
2. Export the pilot report's BCF from the running instance
   (`GET /v1/reports/{id}/export/bcf` for 2.1; `?version=3` for 3.0).
   Compute `sha256` of the downloaded file — it must equal the T1 digest of
   the same generator when produced from the same report bytes; if the pilot
   uses a different report, re-run the handoff tool against that report first.

## Import session (operator = pilot engineer, not AeroBIM)

3. Import the BCF into the CDE (BIMcollab: Project → Import BCF; select 3.0
   archive). Do not edit topics before capturing evidence.
4. Capture into a new pack directory `audit/evidence/cde-import-proof/<date>/`:
   - `import-log.txt` — tool/export log or a timestamped operator note with
     CDE product + version + result per topic count;
   - `screenshot.png` — CDE UI showing imported topics (titles + priority
     column visible; our clash topics carry `[band]` in the title);
   - `hashes.json` — SHA-256 of `import-log.txt`, `screenshot.png`, and
     `bcf_zip_sha256` = digest of the imported archive;
   - `STATUS.json` — `{"status": "VERIFIED", "claim_allowed": true}` only
     after the files above are real.
5. Fill `T2_EVIDENCE_TEMPLATE.json` fields (cde_product, cde_version,
   operator, observations.topics_visible/viewpoints_visible/comments_visible).

## Verification gate (fail-closed)

6. Dry-run checklist (no claim flip):
   `python -m aerobim.tools.verify_bcf_t2_evidence --checklist`
   Lists required artifacts with descriptions; `claim_allowed` stays false.
7. Run:
   `python -m aerobim.tools.verify_bcf_t2_evidence --dir audit/evidence/cde-import-proof/<date> --structural-evidence audit/evidence/bcf-structural-handoff-<date>.json`
   - exit 0 + `claim_allowed=true` requires: all files present, **every hash
     recomputes**, and `bcf_zip_sha256` matches a T1 digest (artifact binding);
   - any mismatch keeps `NOT_VERIFIED` — do not edit hashes to fit; re-run the
     import with the correct archive instead.
8. Commit the pack + verification JSON output. Update
   `audit/evidence/cde-import-proof/STATUS.json` only via this gate.

## Wording discipline

- Allowed after PASS: «независимый импорт BCF в <CDE product+version>
  подтверждён, артефакт привязан по SHA-256».
- Still forbidden: «BCF ready for CDE», «CDE interoperable», «production BCF
  handoff» (T3 round-trip and T4 production remain open).
