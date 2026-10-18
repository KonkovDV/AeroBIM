# Requirement Samples Placeholder

Store structured requirement packs here for the internal rule DSL and document-normalization path.

Prefer compact, provenance-friendly fixtures that are easy to reason about in tests and audits.

The current baseline accepts:

- legacy rows: `rule_id|ifc_entity|property_set|property_name|expected_value`
- extended rows: `rule_id|rule_scope|ifc_entity|target_ref|property_set|property_name|operator|expected_value|unit|evidence_text`

`target_ref` `ALL`, `*`, `ANY` or empty means every instance of `ifc_entity`. A GlobalId matches exactly. A name matches after Cyrillic/Latin lookalike folding and casefold (`С345` and `C345`). A short system-mark list or range (`В2.7,8,9`, `В2.4–В2.6`) matches one mark in that list. A token with `*` is not a mark list. Latin `I` is not folded.