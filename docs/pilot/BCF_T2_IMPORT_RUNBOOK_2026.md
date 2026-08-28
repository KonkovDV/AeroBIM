<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "BCF T2 CDE-import runbook (pilot)"
status: active
version: "1.1.0"
last_updated: "2026-08-28"
claim_boundary: "Runbook only — executing it requires a real customer/pilot CDE session. T2 stays NOT_VERIFIED until the pack verifies (RT-008)."
---

# BCF T2 CDE-import runbook — Samolet pilot (2026)

Purpose: produce an **independent, hash-bound** proof that an AeroBIM BCF ZIP
imports into an external CDE. **Target confirmed 2026-08-28 (address level):**
the customer's pack share link resolves to the **10D** СОД contour
([samolet10d.ru/catalog/product/10d-cod](https://samolet10d.ru/catalog/product/10d-cod/),
publicly described as covering PD + RD + IRD after the **15.07.2025** update,
[ComNews](https://www.comnews.ru/digital-economy/content/240189/2025-07-15/2025-w29/1012/samolet-obnovil-reshenie-upravleniyu-dokumentaciey-stroitelnykh-proektakh)).
The application contour serves content only to a session browser — the address
is confirmed, the folder contents are **not** read, and no access-type claim is
made (operator must ask the customer whether the link is authorized-only or
public, and whether it expires). T2 stays `cde_import=NOT_VERIFIED` until a real
import log exists. Do not invent a 10D screenshot.

**Closure path without customer files (2026-08-28):** the identified CDE
publishes a Swagger-documented API and free developer licenses. A T2-class
engineering proof is therefore possible **without waiting for the customer data
regime**: developer demo tenant → push synthetic BCF remarks into the registry →
capture import-log + screenshot + hashes per the template below. That proves
integration with the CDE the customer already runs; it is **not** a customer
registry proof and does not flip `claim_allowed` (see RT-CDE-IDENT in
[`../quality/TZ_LIVE_TREE_TRIAGE_2026_08_27.md`](../quality/TZ_LIVE_TREE_TRIAGE_2026_08_27.md)).

**Positioning against the vendor's own checker (2026-08-28):** the same vendor
ships a model-checking product (TZ/EIR attribute completeness over RVT/DWG/IFC)
and a remarks registry with filters/priorities. Differentiation: their checker
validates **model attribute population**; AeroBIM checks **content norms on
documentation** (including scans) and cross-checks calculation documents against
sources. Different inputs, different error classes. Remarks should be written
**into the customer's 10D registry**, not shipped as a competing panel.
Corollary for the 27-model IFC ask: the vendor sells scheduled **batch IFC
export** — the request becomes "run your already-purchased batch export on one
building", not "do conversion work for us".

Consumer reality (Jul 2026): BIMcollab accepts BCF **3.0** import since
2026-02-20; Trimble Connect imports BCF **2.1**. Both exporters are XSD-validated
locally against official buildingSMART schemas (Waves C–E), so a T2 failure
isolates consumer-side behavior.

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
