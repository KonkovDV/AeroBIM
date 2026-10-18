# Requirement samples

Small rule tables for tests and for a local run. They are synthetic. They are not a signed acceptance profile.

Two row shapes:

- short: `rule_id|ifc_entity|property_set|property_name|expected_value`
- full: `rule_id|rule_scope|ifc_entity|target_ref|property_set|property_name|operator|expected_value|unit|evidence_text`

`target_ref` of `ALL`, `*`, `ANY`, or an empty cell means every instance of `ifc_entity`. A GlobalId is compared character by character, and the case matters.

A name is compared after lookalike Cyrillic and Latin letters are folded, and after case is folded. `С345` and `C345` are one grade. A Roman `I` stays `I`. `В2.7,8,9` and `В2.4–В2.6` match any one mark written inside them. `П300*300` stays a grille size.
