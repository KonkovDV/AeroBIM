<!-- claims-lint: allow-file reason="Honest refusal of native RVT/NWD; IFC-first ingest; NO_GO" -->
---
title: "Native RVT/NWD ingest boundary — IFC-first"
date: "2026-08-27"
last_updated: "2026-08-30"
status: active
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Fail-closed refusal of closed Autodesk formats. Not a DWG/RVT/NWD reader.
  Not customer SLA. Checkpoint NO_GO.
---

# Native RVT / NWD — honest refusal (same class as DWG)

**What the 25.08 customer answers asked.** Native `.rvt` / `.nwd` among dataset classes. AeroBIM does not parse them.

**Why this is the same class as DWG.** Autodesk Revit (`rvt`/`rte`) and Navisworks (`nwd`/`nwc`) are closed formats. There is no free reader in this MIT tree. The DWG row already said that in the TZ coverage matrix; RVT/NWD did not. Silence on a closed format looks like an unmet TZ item.

**What the clone does now.**

Local unpack census 30.08 (gitignored trees, counts only): wrapper **27** `.rvt` / **21** NWD+NWC; unpack tree **75** `.rvt` / **8** Navis. Presence is not a reader. [`../evidence/unpack-census-2026-08.md`](../evidence/unpack-census-2026-08.md).

| Path | Behaviour |
|---|---|
| HTTP upload `.rvt`/`.rte`/`.nwd`/`.nwc` | `UploadContentError` with `native RVT/NWD parser is not implemented; closed Autodesk format without a free reader` |
| HTTP upload `.zip` whose members are Autodesk natives or a Revit container (`BasicFileInfo`) | Same `UploadContentError` — renaming the file to `.zip` is not a silent skip |
| Analyze `drawing_sources` with those suffixes **or** a `.zip` that names those members | `capabilities.dwg_dxf=FAILED`; `summary.passed=false`; DXF sibling success does not clear it |
| Declared package inventory `format=rvt`/`nwd` | `AEROBIM-PACKAGE-UNSUPPORTED-FORMAT` (ERROR), same as DWG |
| Probe | `python -m aerobim.tools.validate_native_autodesk_toolchain` → `claim_allowed=false` |

**Residual (not silent success).** A Navisworks binary renamed to `.zip` without ZIP magic is rejected as a content mismatch on HTTP upload. An unreadable ZIP drawing source that does not name Autodesk members still follows the existing CAD `MISSING` path — that is not a native-RVT claim.

**Ingest route we ask the customer to use.**

1. Authoring tool (including Renga, which Samolet has shown publicly on the Pushkino IZHS case) exports **IFC 2x3 / IFC4 / IFC4x3**.
2. Sheets and letters go as **PDF/A** (ПП 614 and MinStroy order 783/пр are built on PDF/A + IFC for the machine-checkable contour, not on native Revit).
3. Optional DXF sidecar for CAD annotation extract; DWG ingest stays `NOT_IMPLEMENTED` (`validate_dwg_toolchain`).

This is **their** exchange contour, not a concession: public Renga + Tangl cases already talk IFC/RVT on the customer side; AeroBIM's gate is IFC + IDS + sheets.

**What this does not do.** It does not close RT-001/002b/003. It does not raise `AEROBIM_MAX_IFC_BYTES` (analyze stays 256 MiB on the CI pin). It does not claim native Autodesk support.

**License fork (OSINT 2026-08-30).** ODA Sustaining (7 500 / 4 500 USD) is the SaaS *Drawings* floor, not Revit/Navisworks. BimRv and BimNv are listed at 6 250 USD each. LibreDWG is GPL-3+ and cannot join this MIT core. Public CADSoftTools CAD .NET starts at 765 USD (DWG/DXF, not RVT). Sources and Red Team: [`NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md`](../quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md).
