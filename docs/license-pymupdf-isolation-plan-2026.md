# LIC-001 PyMuPDF isolation / migration plan (2026)

**Status:** Option B **OWNER-SELECTED** (2026-07-31) — production core PDF path migrated.  
**Decision:** migrate off AGPL PyMuPDF to permissive `pypdfium2` + `pdfminer.six` (+ Pillow).  
**Residual:** optional `pdf-agpl` extra keeps PyMuPDF for legacy fixture/tools only; not in Docker runtime lock.

## Why Option B

- Owner directed license change away from AGPL dual-licensed core dependency.
- Shrinks production AGPL surface without Artifex commercial contract.
- Phase 1 seam (`AEROBIM_PDF_BACKEND`) retained: `pdfium` (default) | `pymupdf` | `none`.

## Phases

| Phase | Deliverable | Acceptance | Status |
|---|---|---|---|
| 1 | Port seam + plan + Claims honesty | EI producer selectable; adapters isolated | DONE |
| 2 | Optional `[pdf-agpl]` + core without pymupdf | runtime lock has no pymupdf; Docker image AGPL-free for PDF | **DONE** |
| 3 | Functional adapters (text, crop, preview) on pdfium/pdfminer | focused tests + CI | **DONE** (honest: not full OCR-vs-render product) |
| 4 | Owner picks A or B | recorded | **DONE — B** |

## Non-goals

- Declaring “no third-party license obligations”
- Claiming byte-identical crop/text parity with PyMuPDF
- Shipping AGPL PyMuPDF in production image

## Related

- `docs/license-policy-2026.md`
- `audit/reports/CRITICAL_BLOCKERS.md` LIC-001
- `backend/tests/test_license_isolation_guard.py`
- `backend/tests/test_pdfium_region_cropper.py`
