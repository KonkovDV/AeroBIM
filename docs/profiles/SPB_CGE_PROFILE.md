# SPb GAU «ЦГЭ» published IDS profile

Machine-readable CIM requirements published by SPb GAU «Центр государственной экспертизы», indexed as an AeroBIM check profile. **Check against a published rule set, without expertise status.** Not a customer-signed acceptance profile. Does not close RT-001 / RT-002 / RT-003.

## Source

| Field | Value |
| --- | --- |
| Publisher | СПб ГАУ «Центр государственной экспертизы» (ЦГЭ) |
| Page | https://www.spbexp.ru/bim/docs/ |
| Section | Машиночитаемые требования к ЦИМ |
| First published | 2023-12 (with ISP RAS) |
| OKS edition | 3.1.0 (2024-12-09) — 17 IDS files |
| RII edition | 1.1.0 (2024-12-10) — 5 IDS files |
| Retrieved | 2026-08-14 (`samples/ids/spbexp/SOURCE.md`) |
| Provenance | `OFFICIAL_PUBLISHED` |
| `signed_by_customer` | `false` (ЦГЭ is the publisher, not AeroBIM’s customer; Samolet RT-002b stays open) |

Linear-object CIM is a separate CGE subject and is **not** in this pack. Do not mix with Moscow AGR (DGP) or MOEXP packs.

## Reproduce (one command)

```text
cd backend
python -m aerobim.tools.validate_spb_cge_profile
```

Gates, fail-closed: JSON Schema + honesty locks → SHA-256/size vs manifest → buildingSMART IDS 1.0 XSD (`samples/ids-xsd/ids.xsd`) → IfcTester parse → two identical fixture runs on `samples/ifc/wall-pset-qto-pass.ifc`. Evidence: `docs/evidence/spb-cge-profile-validation-2026-08.json`.

A broken, missing, hash-mismatched, or non-IDS-1.0 file **fails the run**. Silence is never success.

## Coverage

**Checks:** attribute composition of IFC elements per the publisher’s IDS 1.0 specifications (356 specifications in 22 files); fail-closed validation of the IDS files themselves.

**Does not check:** geometry/clash (including MEP); engineering meaning of attribute values; completeness of a PD/RD pack or model↔sheet↔text seams; **and does not substitute GrK art. 49 expertise**.

## Honesty locks

`closes_rt001`, `closes_rt002`, `closes_rt003`, `signed_by_customer`, `samolet_alias` are JSON `false` and rejected if flipped. Manifest schema: `samples/profiles/spb-cge/manifest.schema.json`.
