<!-- claims-lint: allow-file reason="Jurisdiction IDS document audit; RT-002 stays OPEN" -->
---
title: "Jurisdiction IDS document audit"
date: 2026-08-14
claim_level: ids_document_self_audit
closes_rt002: false
---

# Jurisdiction IDS document audit

Auditor: `XmlIdsDocumentAuditor` (document well-formedness + vendored IDS **1.0** XSD + AeroBIM facet rules).
Not the official buildingSMART `IDS-Audit-tool` binary. Official files were **not** rewritten.
`customer_pack_hash` remains null. Does **not** close RT-002.

- content_sha256: `5d1e02e140dc0eeea6cd4da62a1a522b3c4c5f2d1baf3530bae218e12e4c420d`
- Pack-wide document audit: **50** files (MOEXP 24 + Moscow AGR 4 + SPb CGE 22) → **0** issues
- Hashed samples in JSON: one MOEXP AR, one AGR, one SPb РИИ

`0` document issues is **not** IfcTester execution against a CIM, **not** IDS 1.1 certification (auditor schema is IDS 1.0), **not** a signed customer pack.

Checkpoint **NO_GO**.
