---
title: "BCF XSD alignment + triage handoff"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Structural XSD alignment only. No CDE import claim — RT-008 T2 stays customer-gated. Checkpoint stays NO_GO."
---

# Wave C — BCF XSD alignment + triage handoff (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| BCF 2.1 schema | buildingSMART BCF-XML `release_2_1/Schemas/markup.xsd` — Topic sequence: ReferenceLink*, Title, Priority?, Index?, Labels*, CreationDate, CreationAuthor, …, Description?; `Viewpoints` is ViewPoint-typed with `Guid` attribute |
| BCF 3.0 schema | buildingSMART BCF-XML `release_3_0/Schemas/markup.xsd` — `Markup` contains only Header?+Topic; **Comments/Viewpoints moved inside Topic**; `ReferenceLinks`/`Labels` are wrappers; `Header/Files/File` |
| Consumer reality | BIMcollab accepts **BCF 3.0 import** since 2026-02-20 — structural fidelity is now consumer-visible |
| Triage | Wave B `domain/clash_triage.py` (Ailem 2026 AutoCon; Koo 2026 ASCE JCEM) |

## Defects found (against official XSD)

- 2.1 exporter emitted Topic children out of XSD order (Title→Description→…→ReferenceLink)
  and wrapped `Viewpoints > Viewpoint Guid=…` instead of `Viewpoints Guid=…`.
- 3.0 exporter emitted `Comments`/`Viewpoints` as **siblings** of Topic (2.1-style),
  bare `ReferenceLink` children, no `Labels` wrapper, and `Header/File` with a
  `Date` **attribute** instead of `Files/File/Date` element.

## Delivered (code + test)

- `bcf_report_exporter.py` (2.1): XSD-ordered Topic children; `Priority` (triage
  band, e.g. Critical), `Index` (triage rank), `triage:band=…` label; clash
  topics in deterministic triage order with symmetric duplicates merged; topic
  GUID seeded from pair key (stable across engine output reorderings, no index
  in seed); rationale + duplicates_merged in Description.
- `bcf3_exporter.py` (3.0): full structural rewrite per release_3_0 markup.xsd —
  Comments/Viewpoints inside Topic, ReferenceLinks/Labels wrappers,
  Header/Files/File, Priority/Index/Labels from triage; same stable GUID seeding.
- `tests/test_bcf_xsd_alignment.py` — 9 tests: XSD-relative child order (2.1 +
  3.0), Priority/Index from band/rank, wrapper structure, Header/Files/File,
  Markup children exactly [Header, Topic] (3.0), GUID stability across input
  order, symmetric-duplicate merge into one topic.
- Updated 2 stale asserts that pinned the pre-XSD (incorrect) structure.

## Explicitly NOT claimed

- CDE import (RT-008 T2) — requires saved independent import artifact from a
  customer/external tool run; structural PASS ≠ import PASS.
- extensions.xml Priority vocabulary — we emit free-text Priority (legal per
  XSD `NonEmptyOrBlankString`); predefined-list alignment is a consumer-side
  agreement for the pilot.
- No change to Shared-gate: exporters are read-side of the report.

## Gate evidence (2026-07-25 local)

`ruff check` PASS · `mypy src` 192 files PASS · `pytest tests -q`
**943 passed, 7 skipped** (incl. 77 across all BCF suites + triage).
