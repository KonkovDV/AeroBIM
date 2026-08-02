# Signature and immutability (2026)

**Capability:** `qualified_signature` = **ENG_PARTIAL** when a fixture envelope is audited; default **MISSING** when not evaluated.  
**Official law reference (not AeroBIM implementation):** ФЗ от 06.04.2011 № 63-ФЗ «Об электронной подписи» — [pravo.gov.ru](http://pravo.gov.ru/proxy/ips/?docbody=&nd=102146610) (портал правовой информации; редакции обновляются — сверять актуальную на дату сделки).

## VERIFIED in AeroBIM (ENG_PARTIAL)

- Input file hashes (sha256) in reports / evidence bundles / package provenance paths exist in code.
- Detached signature envelope schema `aerobim_detached_signature_envelope_v1`: presence, content SHA-256 integrity, required signer-role completeness, **presence-only** `signature_alg` / `signature_value` (no crypto verify), and optional multi-file `package_hashes` / `content_hashes` binding are assessed on fixture envelopes (`samples/signatures/`).
- Claims Lock forbids «УКЭП проверена» / «подпись документа проверена» as legal claims.

## NOT VERIFIED / missing

| Function | Status |
|---|---|
| Cryptographic signature validation (CMS/CAdES/etc.) | **missing** (crypto adapter not shipped) |
| Certificate / CRL / OCSP / trust chain | **NOT_VERIFIED** (always; no accredited CA/TSP access) |
| Signer authority beyond role-label presence | missing |
| UI «drawn signature» as validation | forbidden |
| Legal УКЭП / qualified-signature validity | **forbidden claim** |

## Engineering rule

Original bytes must not be rewritten; derived previews are not originals; hash mismatch → blocking finding when that check is enabled (`require_signature_audit` / `signature_envelope_path`). Trust chain remains **NOT_VERIFIED** even when envelope presence/integrity/roles/signature-field presence pass — never upgrade to legal «УКЭП проверена». Any future CMS/CAdES adapter must use a **new** capability name, not flip `qualified_signature` to OK.

**Legal note:** this document is engineering boundary, not legal advice for customer УКЭП process.

**claim_boundary:** presence/integrity/roles on fixture envelope only; trust chain NOT_VERIFIED; forbidden claims unchanged.
