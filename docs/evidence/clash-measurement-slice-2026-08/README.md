<!-- claims-lint: allow-file reason="Measurement scaffold citing forbidden accuracy phrases only as non-claims / protocol boundary" -->
---
title: "Clash measurement slice — kickoff (KT#2 window)"
status: active
version: "0.1.0"
date: "2026-08-09"
claim_boundary: "Scaffold only. No product accuracy. Allowed wording after labeling: geometric intersection of extents, measured P/R at n with κ — never «коллизия по ТЗ >90%»."
---

# Clash measurement slice (12–14.08)

Applies existing WP-07 protocol — does not invent a new one.

| Item | Value |
| --- | --- |
| Finding class | `clash` only (`SPATIAL-HARD-CLASH` / IfcClash intersection) |
| Target n | **50** interim (planner prefers ~62 power / ~111 Wilson; report CI width) |
| Adjudicators | 2 (dual-blind); κ gate eng ≥0.60, pilot target ≥0.80 |
| Interim quality | TP/(TP+FP) ≥ 0.60 planning — **not** TZ >90% |
| Forbidden claims | verified collisions; MEP delivered; product >90% |

## Files in this folder

| File | Role |
| --- | --- |
| `adjudication-worksheet.csv` | Dual labels (from template) |
| `labels-protocol-draft.json` | Protocol labels shell — fill after export |
| `agreement-template.json` | κ/α artifact shell |
| `STATUS.json` | Machine-readable progress |

## Operator sequence

```text
python scripts/run_clash_adjudication_slice.py --check-tools
cd backend
pip install -e ".[clash]"
# analyze package with clash enabled → report JSON
aerobim-export-detections-from-report --report <report.json> --out ../docs/evidence/clash-measurement-slice-2026-08/detections.json
# fill adjudication-worksheet.csv (engineer-a / engineer-b)
aerobim-measure-adjudicator-agreement --csv ../docs/evidence/clash-measurement-slice-2026-08/adjudication-worksheet.csv
aerobim-build-detection-labels ...
aerobim-evaluate-detection-precision --labels <labels.json> --detections <detections.json>
```

## Corpus blocker (honest)

In-repo IFC fixtures are too small / incomplete for IfcClash geom iterator (`AssertionError` on initialize).  
**Need:** customer or pilot IFC with real solid geometry (Samolet pack / agreed corpus). Until that file is present, detections stay empty and P/R cannot be measured — matrix stays “not measured”, not `0% engine`.

## Matrix wording when done

Replace clash accuracy cell with:  
`precision=… recall=… n=50 κ=… (geometric intersection of extents, measured; not TZ >90%)`  
and run `python scripts/lint_claims.py --matrix-guard`.
