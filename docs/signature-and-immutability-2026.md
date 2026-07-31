# Signature and immutability (2026)

**Capability:** `QUALIFIED_SIGNATURE_VALIDATION` = **missing**.  
**Official law reference (not AeroBIM implementation):** ФЗ от 06.04.2011 № 63-ФЗ «Об электронной подписи» — [pravo.gov.ru](http://pravo.gov.ru/proxy/ips/?docbody=&nd=102146610) (портал правовой информации; редакции обновляются — сверять актуальную на дату сделки).

## VERIFIED in AeroBIM

- Input file hashes (sha256) in reports / evidence bundles / package provenance paths exist in code.
- Claims Lock forbids «УКЭП проверена» / «подпись документа проверена».

## NOT VERIFIED / missing

| Function | Status |
|---|---|
| Cryptographic signature validation | missing |
| Certificate / CRL / OCSP / trust chain | missing |
| Signer authority / mandatory signers set | missing |
| UI «drawn signature» as validation | forbidden |

## Engineering rule

Original bytes must not be rewritten; derived previews are not originals; hash mismatch → blocking finding when that check is enabled. Until a crypto adapter + tests exist, status stays **missing** — not «review_required as if validated».

**Legal note:** this document is engineering boundary, not legal advice for customer УКЭП process.
