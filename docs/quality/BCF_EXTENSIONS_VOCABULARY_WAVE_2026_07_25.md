---
title: "BCF 3.0 extensions.xml vocabularies"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Vocabulary declaration + local XSD validation only. No CDE import claim (RT-008 T2 customer-gated). Checkpoint stays NO_GO."
---

# Wave E — BCF 3.0 extensions.xml vocabularies (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Spec | buildingSMART BCF-XML release_3_0: root `extensions.xml` (`extensions.xsd`) — `Topic.Priority` / `TopicType` / `TopicStatus` / `Labels` are "Predefined list in extensions.xml" |
| Consumer reality | BIMcollab BCF 3.0 import (2026-02-20) resolves topic vocabularies from extensions; free-text Priority was our declared gap in Wave C |
| Triage source | Wave B bands (Ailem 2026 AutoCon; Koo 2026 ASCE JCEM) feed `Priorities` |

## Delivered (code + test + evidence)

- `bcf3_exporter.py`: emits root `extensions.xml` built **from the vocabularies
  actually used** by emitted topics (TopicTypes / TopicStatuses / Priorities /
  TopicLabels), sorted + de-duplicated → byte-identical archives for identical
  reports; omitted for empty reports.
- `samples/bcf-xsd/release_3_0/extensions.xsd` vendored (verbatim official).
- `bcf_consumers._validate_against_xsd`: validates `extensions.xml` when the
  schema and member are both present (2.1 dir has no extensions.xsd → gracefully
  out of scope; honesty statuses unchanged).
- Tests (6 new): vocabularies declared & used-subset agreement (every markup
  Priority/TopicType/Label ⊆ extensions lists), empty-report omission,
  determinism across clash input order, tampered extensions.xml → `failed`.
- T1 evidence regenerated (`bcf-structural-handoff-2026-07-25.json`):
  `xsd_status="passed"` now covers extensions.xml; handoff tool exit 0.

## Explicitly NOT claimed

- CDE import (RT-008 T2) — unchanged; extensions.xml improves import behavior
  but proof still requires an external-tool artifact.
- BCF 2.1 extension schemas (project.bcfp-referenced mechanism) — out of scope.
- Users/Stages/SnippetTypes vocabularies — not emitted (no data source yet).

## Gate evidence (2026-07-25 local)

`ruff format --check` 317 files PASS · `ruff check` PASS · `mypy src` 192 files
PASS · `pytest tests -q` **952 passed, 7 skipped** · handoff tool exit 0.
