# Vendored buildingSMART BCF-XML schemas

Official XSDs vendored verbatim for **local structural XSD validation** of
AeroBIM BCF exports (`bcf_consumers.verify_bcf_zip_structure`).

| Dir | Source (fetched 2026-07-25) |
|---|---|
| `release_2_1/` | https://github.com/buildingSMART/BCF-XML/tree/release_2_1/Schemas |
| `release_3_0/` | https://github.com/buildingSMART/BCF-XML/tree/release_3_0/Schemas |

Only the schemas needed for the files AeroBIM emits are vendored:
`version.xsd`, `markup.xsd`, `visinfo.xsd` (+ `shared-types.xsd` and
`extensions.xsd` included by release_3_0 schemas).

**License:** CC BY-ND 4.0 (buildingSMART International Ltd.) — see
`LICENSE_CC_BY_ND_4.0.txt` and `NOTICE`. Upstream:
https://github.com/buildingSMART/BCF-XML/blob/release_3_0/LICENSE

Do not edit these files; re-vendor from upstream. Attribution required.

Claim boundary: XSD-valid ≠ CDE import proof (RT-008 T2 stays customer-gated).
