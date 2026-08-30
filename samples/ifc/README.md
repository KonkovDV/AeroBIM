# IFC Samples

- `samples/ifc/*.ifc` — project-authored fixtures (repo fixture license).
- `samples/ifc/public/buildingsmart-sample-test-files/` — **CC BY 4.0** public
  samples from buildingSMART Sample-Test-Files (attribution required; see folder README).

Prefer small, license-clear fixtures first. Not customer evidence.

**Not a Renga export.** `walls-multi-entity.ifc` is authored with IfcOpenShell
0.8.4 (`FILE_SCHEMA(('IFC4'))`, project name `Samolet Multi Fixture`).
`walls-multi-entity-spatial.ifc` is the same walls plus one storey and one grid
so the demo report can stamp этаж/ось. A customer
IFC must come from **that customer's authoring export chain** (intake). Do not
describe this file as a Renga or Samolet production model. Do not state Samolet
authoring as Renga unless the customer confirms it.

A publisher Renga sample (PNST 909, ToS cite GO, binaries gitignored) is probed
by `python -m aerobim.tools.run_renga_export_probe`. That command is a vendor
pack probe, not a Samolet stack claim, and does not replace this fixture.
