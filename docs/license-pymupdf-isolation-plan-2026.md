# LIC-001 PyMuPDF isolation / migration plan (2026)

**Status:** STARTED (Phase 1) — engineering, not legal clearance.  
**Selected default path:** **Option C phased** (isolate behind port → optional `[pdf]` extra → fail-closed without PDF).  
**Alternatives remain open:** A (Artifex commercial), B (pypdfium2/pdfminer migration).

## Why Option C first

- Does not require budget/legal to *start*.
- Shrinks AGPL surface for future AGPL-free core builds.
- Keeps current Docker/CI working while `pymupdf` remains installed.
- Does **not** claim LIC-001 closed.

## Phases

| Phase | Deliverable | Acceptance | Status |
|---|---|---|---|
| 1 | Port seam + plan + Claims honesty | all PyMuPDF imports still only in `infrastructure/adapters` + `tools`; EI producer behind `ExtractionIntegritySignalProducer` | **IN PROGRESS** |
| 2 | Optional extra `[pdf]` + Docker still installs it; core can build without pymupdf for non-PDF profiles | `pip install -e .` without `[pdf]` → PDF capabilities SKIPPED/FAILED honestly | NOT STARTED |
| 3 | Functional equivalence suite (text, bbox, RU/EN, crop) vs pypdfium2/pdfminer candidate | golden fixtures; CI gate | NOT STARTED |
| 4 | Owner picks A or B or stay on C+Artifex | legal/budget decision recorded | BLOCKED (owner) |

## Non-goals

- Declaring AGPL inapplicable
- Shipping AGPL-free production image in Phase 1
- Claiming PDF parity after a stub swap

## Related

- `docs/license-policy-2026.md`
- `audit/reports/CRITICAL_BLOCKERS.md` LIC-001
- `backend/tests/test_license_isolation_guard.py`
