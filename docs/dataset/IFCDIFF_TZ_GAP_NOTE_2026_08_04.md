# ifcdiff → TZ row 28 (version / doc-type compare)

**Date:** 2026-08-04  
**Status:** engineering note — not yet implemented  
**Matrix:** [`audit/reports/TZ_RUNTIME_MATRIX.md`](../../audit/reports/TZ_RUNTIME_MATRIX.md) row **28 = MISSING**

## Finding

Tracker TZ requires «сравнение версий и типов документации». AeroBIM today only emits reserved kinds `STAGE_MISMATCH` / `VERSION_MISMATCH` on limited paths — not package-vs-package IFC diff.

## Existing dependency (no new packages)

IfcOpenShell **documents** `ifcdiff` next to `ifctester` / `ifcclash`. On the locked **0.8.5** wheel in this environment, there is **no** importable `ifcdiff` module and no `ifcdiff` console script on PATH.

Honest options (still no *new* third-party product dependency):

1. Port the small `ifcdiff` utility from the IfcOpenShell upstream repo (same project family as the already-declared dependency) behind `IIfcModelDiff`.  
2. Or implement a minimal GUID/attribute diff adapter using `ifcopenshell` APIs already installed.

Then: map diff classes → CRITICAL/WARNING/INFO; flip matrix row 28 MISSING → VERIFIED_FIXTURE_ONLY with a two-revision fixture.

## Claims Lock

- Diff findings are engineering signals, not «документация одобрена».  
- Does not close RT-001.  
- Do not claim CDE version management.

## Estimate

~1 day for thin port + fixture + matrix update after confirming the binary/API in the locked dependency version.
