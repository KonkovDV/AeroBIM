<!-- claims-lint: allow-file reason="Stale-norm citation scan; not product accuracy" -->
---
title: "Stale norm citations (GOST R 21.101-2020 superseded)"
date: 2026-08-13
claim_level: stale_norm_citation_scan
claim_boundary: >-
  Citation hygiene only. Not statutory interpretation of the replacement standard. Not Moscow AGR completeness. Not customer accuracy.
---

# Stale norm citations

A cited document that has been replaced raises `AEROBIM-NORM-SUPERSEDED` 
(warning). Demo: Moscow CIM AGR requirements cite GOST R 21.101-2020 after 
GOST R 21.101-2026 entered force on 2026-04-01 
(Rosstandart 129-st, 12.02.2026).

## Measured

- catalog documents: **2**
- citing sources: **1**
- superseded-citation warnings: **1**
- content_sha256: `d2ddd0b2b8a68c3fd8bb5a81895d47d3d5302e47d56ac5f5286c24c45d96ec4a`

## Issues

- `moscow_agr_cim_requirements`: ГОСТ Р 21.101-2020 → GOST_R_21.101-2026

```bash
cd backend
python -m aerobim.tools.export_stale_norm_scan
```
