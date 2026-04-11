# Requirement Samples Placeholder

Store structured requirement packs here for the internal rule DSL and document-normalization path.

Prefer compact, provenance-friendly fixtures that are easy to reason about in tests and audits.

The current baseline accepts:

- legacy rows: `rule_id|ifc_entity|property_set|property_name|expected_value`
- extended rows: `rule_id|rule_scope|ifc_entity|target_ref|property_set|property_name|operator|expected_value|unit|evidence_text`