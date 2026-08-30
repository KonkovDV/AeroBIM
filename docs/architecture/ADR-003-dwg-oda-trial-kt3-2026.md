<!-- claims-lint: allow-file reason="ADR: native DWG remains FAILED; ODA trial is KT#3 measurement not a product claim" -->
---
title: "ADR-003 — Native DWG stays FAILED; ODA 60-day trial is KT#3 fact-finding"
status: accepted
date: 2026-08-13
last_updated: "2026-08-30"
claim_boundary: "Native DWG remains FAILED. This ADR does not authorize a DWG-ready claim. ODA trial ≠ commercial license ≠ SaaS."
---

# ADR-003: Native DWG and ODA trial

## Context

Tracker asks how we handle DWG. Runtime today: `EzdxfCadModelIngestor` returns `supported=False` for `.dwg`; capability `dwg_dxf` is FAILED when DWG is requested; FAILED CAD capability blocks `summary.passed` (ADR-001). Options A/B/C: [`docs/tz/DWG_DECISION_OPTIONS_ABC_2026_08.md`](../tz/DWG_DECISION_OPTIONS_ABC_2026_08.md). Cost/legal: `docs/dwg-blocker-memo-2026-08.md`.

Russian intake for expertise is PDF/A + IFC + XML (MinStroy 783/пр, PP RF 614). DWG is a contractor working format, not the regulator's required exchange.

ODA [pricing](https://www.opendesign.com/pricing): Commercial membership is **not** licensed for SaaS/web; Sustaining is the SaaS floor. A 60-day evaluation is fact-finding, not a product feature.

## Decision

1. **Native DWG stays FAILED** through KT#2 (20.08.2026). No green DWG path. No «DWG-ready».
2. **KT#3 (03–21.09)** may run an **ODA Drawings 60-day trial** solely to measure:
   - nanoCAD / SPDS / GraphiCS **proxy objects** (`ACAD_PROXY_OBJECT` and vendor equivalents);
   - layers, SHX, CP1251, xrefs, attributed blocks;
   - what survives vs what is cached graphics only.
3. **Buy** a commercial ODA (or CADSoftTools) license **only if both** hold:
   - ≥30% of customer packages in the pilot corpus are DWG-only (no IFC/PDF equivalent for the same sheet/model);
   - DWG is written into the **signed Samolet acceptance profile**.
4. Commercial license ≠ SaaS. Hosted Shared-gate cannot use ODA Commercial (≤100 copies, no web). If we ever host, Sustaining (or equivalent server license) is the floor — still a later owner decision.
5. Native **RVT/NWD** is a *different* SKU: ODA BimRv / BimNv extensions (public 2026 list 6 250 USD each on top of Sustaining). Do not quote Sustaining 7 500 USD as the RVT price. OSINT: [`../quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md`](../quality/NATIVE_CAD_LICENSE_FORK_OSINT_2026_08.md).
6. DXF via optional `ezdxf` remains **not** native DWG.

## Consequences

- Keep fail-closed honesty on `capabilities.dwg_dxf`.
- Do not start ODA integration adapters before the trial protocol exists (new adapter under the existing CAD ingest port is allowed later; **no new domain port** in KT#2).
- Trial numbers go to `artifacts/` with hashes; they do not flip this ADR to «DWG-ready».
