---
title: "Official BCF XSD validation (vendored schemas)"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "XSD-valid ≠ CDE import proof (RT-008 T2 stays customer-gated). Checkpoint stays NO_GO."
---

# Wave D — Official BCF XSD validation (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Official schemas | buildingSMART BCF-XML `release_2_1` / `release_3_0` `Schemas/*.xsd` (fetched verbatim 2026-07-25) |
| Validator | `xmlschema==4.3.2` — already in hashed locks (XSD 1.0/1.1, pure Python) |
| Consumer reality | BIMcollab BCF 3.0 import (2026-02-20) — schema fidelity is consumer-visible |
| RU norms context | ПП РФ № 715 от 09.06.2026 — ускоренный перевод СП в машиночитаемый формат (anchor for norm-pack track; no code claim this wave) |

## Defects found (beyond Wave C, against official XSDs)

- **3.0 `bcf.version`**: only the `VersionId` attribute is allowed — we emitted a
  `DetailedVersion` child (2.1-ism). Fixed.
- **3.0 `visinfo` Components order** is Selection?, Visibility?, Coloring? — we
  emitted `Coloring` first, and the old test *pinned the wrong order*. Fixed both.
- **2.1 namespaces**: official 2.1 XSDs declare **no targetNamespace**; our
  invented `buildingsmart-tech.org/bcf/...` xmlns blocked validation. Removed.
- **2.1 `OrthogonalCamera`**: has no `AspectRatio` element (3.0-only). Removed.
- **2.1 empty `<Coloring/>` / `<Selection/>`**: invalid (both require ≥1 child).
  Now emitted only when populated; `Visibility` (required) always present.

## Delivered (code + test + evidence)

- `samples/bcf-xsd/{release_2_1,release_3_0}/` — vendored official schemas
  (version/markup/visinfo + shared-types for 3.0) with provenance README.
- `bcf_consumers.py`: `_validate_against_xsd` + `default_bcf_xsd_dir` —
  validates `bcf.version`, every `markup.bcf` and `viewpoint.bcfv`;
  `xsd_status ∈ {passed, failed, skipped, not_configured, not_run}`;
  auto-discovers vendored schemas by `VersionId`; never fakes `passed`
  (missing lib/schemas → `skipped` with note; findings → `failed` + `ok=false`).
- Exporters fixed per defect list above (2.1 + 3.0).
- Tests: 4 new end-to-end XSD tests (2.1/3.0 pass; tampered Topic order fails;
  invalid 22-char IfcGuid fails); 2 honesty tests updated (incomplete schema
  dir → `skipped`, still never `passed`); fixtures upgraded to valid IfcGuids.
- T1 evidence refreshed: `audit/evidence/bcf-structural-handoff-2026-07-25.json`
  — both archives `xsd_status="passed"`, `structural_ok=true`,
  `cde_import=NOT_VERIFIED` (unchanged honesty).

## Explicitly NOT claimed

- CDE import (RT-008 T2) — still requires an independent external-tool import
  artifact; local XSD PASS is a stronger T1, not a T2.
- extensions.xml vocabularies, snapshots, BCF-API — out of scope.
- RU machine-readable norms (ПП №715) — research anchor only; RT-002 unchanged.

## Gate evidence (2026-07-25 local)

`ruff format --check` 317 files PASS · `ruff check` PASS · `mypy src` 192 files
PASS · `pytest tests -q` **947 passed, 7 skipped**.
