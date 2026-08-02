# Signature fixtures (WP-03)

**Status:** ENG_PARTIAL (fixture envelope only).  
**claim_boundary:** Engineering checks cover detached envelope presence, content SHA-256 integrity, and required signer-role completeness. `trust_chain_status` is always `not_verified` (no accredited CA/TSP). This is **not** УКЭП legal validity, not a court-admissible qualified electronic signature claim, and not «подпись документа проверена».

## Files

| File | Purpose |
|---|---|
| `content.txt` | Small content blob for hash integrity demos |
| `content.txt.sig.json` | Good example envelope (`aerobim_detached_signature_envelope_v1`) matching the content hash |

## Forbidden claims

- «УКЭП проверена»
- «квалифицированная электронная подпись проверена»
- Legal significance / accredited CA chain verified
