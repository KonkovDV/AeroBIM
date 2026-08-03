# Vendored buildingSMART IDS 1.0 schema

`ids.xsd` — official IDS 1.0.0 schema (targetNamespace
`http://standards.buildingsmart.org/IDS`), vendored verbatim from
https://github.com/buildingSMART/IDS (`master` = released 1.0) on 2026-07-25.

Used by `XmlIdsDocumentAuditor` for local schema audit of IDS documents before
semantic validation (buildingSMART IDS-Audit-tool practice: schema audit →
semantic audit).

**License:** CC BY-ND 4.0 (buildingSMART International Ltd.) — see
`LICENSE_CC_BY_ND_4.0.txt` and `NOTICE`. Upstream:
https://github.com/buildingSMART/IDS/blob/development/LICENSE

Do not edit; re-vendor from upstream. Attribution required.

Note: the schema imports W3C base schemas (`xml.xsd`, `XMLSchema.xsd`) by URL;
the `xmlschema` library resolves these namespaces from its bundled copies, so
validation stays offline (no outbound fetch).
