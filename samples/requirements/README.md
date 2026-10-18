# Requirement samples

Small rule tables for tests and for a local run. They are synthetic. They are not a signed acceptance profile.

Two row shapes:

- short: `rule_id|ifc_entity|property_set|property_name|expected_value`
- full: `rule_id|rule_scope|ifc_entity|target_ref|property_set|property_name|operator|expected_value|unit|evidence_text`

`target_ref` `ALL`, `*` or `ANY`, and an empty cell, mean every instance of `ifc_entity`. A GlobalId is matched character for character. A name is matched after Cyrillic and Latin lookalikes are folded and the case is folded (`С345` and `C345` are one grade). `В2.7,8,9` and `В2.4–В2.6` match any single mark written inside them. `П300*300` stays a grille size. A Roman `I` is left as `I`.
