---
title: "Official IDS 1.0 XSD audit (vendored schema)"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Schema-valid IDS ≠ requirement correctness. Fail-honest WARNING when validator absent, never silent OK. Checkpoint stays NO_GO."
---

# Wave F — Official IDS 1.0 XSD audit (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Official schema | buildingSMART IDS 1.0.0 `Schema/ids.xsd` (github.com/buildingSMART/IDS, `master` = released 1.0; targetNamespace standards.buildingsmart.org/IDS) — vendored verbatim 2026-07-25 |
| Audit practice | buildingSMART **IDS-Audit-tool**: schema audit before semantic audit |
| Validator | `xmlschema==4.3.2` (already in hashed locks) |
| SSRF policy | repo outbound-guard practice — validation must not fetch W3C imports remotely |

## Delivered (code + test)

- `samples/ids-xsd/ids.xsd` — vendored official IDS 1.0.0 schema + provenance
  README.
- `xml_ids_document_auditor.py`: three audit layers — (1) well-formedness/root
  fail-closed (existing), (2) **official XSD validation** (new: ERROR per
  finding with XSD path hint, capped at 20; explicit
  `AEROBIM-IDS-XSD-CAPABILITY` WARNING when the validator/schema is
  unavailable — never silent OK), (3) AeroBIM structural rules (existing).
- **Offline guarantee (SSRF)**: `ids.xsd` imports W3C base schemas by http URL;
  loader remaps those URIs to the copies bundled inside `xmlschema`
  (`uri_mapper`), verified by a socket-blocked test — no outbound fetch.
- Schema built once per path (`lru_cache`).
- `tests/test_ids_official_xsd_audit.py` — 6 tests: vendored schema discovery,
  all repo IDS fixtures XSD-clean, schema-invalid doc → ERRORs, missing schema
  → single WARNING, valid doc → no XSD issues, network-blocked validation.
- Verified: all 4 `samples/ids/*.ids` fixtures pass the official schema.

## Explicitly NOT claimed

- Semantic IDS audit depth of the reference IDS-Audit-tool (implementer
  agreements beyond XSD) — our layer 3 covers the AeroBIM-supported subset only.
- IDS validation outcomes vs IFC (unchanged contour); RT-001/002/003 unchanged.

## Gate evidence (2026-07-25 local)

`ruff format` clean · `ruff check` PASS · `mypy src` 192 files PASS ·
`pytest tests -q` **958 passed, 7 skipped**.
