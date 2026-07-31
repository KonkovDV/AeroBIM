# Dependency license audit — 2026-07-31

## Method

1. `backend/requirements-lock.txt` as version SSOT for CI/Docker.
2. PyPI `info.license` for PyMuPDF 1.28.0 (HTTPS, 2026-07-31).
3. Inventory: `audit/dependency_license_inventory.json`.
4. Gates: `test_dependency_license_gate.py` (+ lock drift test added this cycle).

## Findings

| ID | Finding | Class | Evidence |
|---|---|---|---|
| LIC-001 | PyMuPDF mandatory core, dual AGPL/Artifex, lock 1.28.0 | VERIFIED engineering / legal review OPEN | PyPI + pyproject + 6 imports + Docker hashed install |
| LIC-DRIFT | Inventory previously listed 1.27.2.3 vs lock 1.28.0 | VERIFIED then FIXED | drift script + inventory update |
| LGPL | ifcopenshell/ifctester 0.8.5 | VERIFIED classifiers historically; local License field empty → keep legal_review | inventory |
| MPL | web-ifc frontend | VERIFIED | inventory + gate |
| MIT whole-product | Forbidden without disclosure | VERIFIED Claims Lock | README disclosure present |

## Decisions

- Do **not** declare AGPL legal blocker as final court opinion — LIC-001 = legal review required.
- Do not silently optionalize PyMuPDF without equivalence tests (crop + text + RU).
- Unknown license → release block (gate).

## Migration plan (options only)

A Artifex commercial · B pypdfium2/pdfminer.six + tests · C optional `[pdf-agpl]` fail-closed · D full AGPL product (rejected default).
