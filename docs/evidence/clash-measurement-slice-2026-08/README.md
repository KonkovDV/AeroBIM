<!-- claims-lint: allow-file reason="Measurement evidence citing forbidden accuracy phrases only as non-claims / protocol boundary" -->
---
title: "Clash measurement slice — fixture measured (2026-08-11)"
status: active
version: "0.2.0"
date: "2026-08-11"
claim_boundary: "Fixture AABB P/R only. Allowed: geometric intersection of extents, measured P/R at n=5 — never «коллизия по ТЗ >90%», never customer corpus, never IfcClash mesh product claim."
---

# Clash measurement slice (updated 2026-08-11)

Applies existing WP-07 protocol — does not invent a new one.

| Item | Value |
| --- | --- |
| Finding class | `clash` (`SPATIAL-EXTENT-CLASH` AABB extents on fixture) |
| Fixture n | **6** confirmed overlaps / 16 walls (`samples/ifc/clash-extent-overlap-fixture.ifc`) |
| Micro (fixture) | precision=1.0 recall=1.0 f1=1.0 (support=6) — **fixture_only** |
| Target customer n | **50** interim (still awaiting pilot IFC solids) |
| Forbidden claims | verified collisions; MEP delivered; product >90%; IfcClash mesh measured here |

## Fixture measurement (done)

```text
cd backend
python -m aerobim.tools.measure_extent_clash_fixture --write-fixture
```

Artifacts in this folder: `detections.json`, `labels.json`, `precision-recall.json`, `STATUS.json` (`status=fixture_measured`).

IfcClash on tiny in-repo IFCs can still return 0 clashes — this path measures **AABB extent intersection**, matching the matrix honesty wording (geometric intersection of extents), not mesh clash product.

## Files in this folder

| File | Role |
| --- | --- |
| `detections.json` / `labels.json` / `precision-recall.json` | Fixture measure run |
| `STATUS.json` | Machine-readable progress (`fixture_measured`) |
| `adjudication-worksheet.csv` | Dual labels template (customer corpus) |
| `labels-protocol-draft.json` | Protocol labels shell |
| `agreement-template.json` | κ/α artifact shell |

## Operator sequence (customer corpus — still open)

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

Customer / pilot IFC with real solids for n≈50 dual-blind labels is still required for publishable product metrics. Fixture P/R does **not** close TZ clash accuracy >90%.

## Matrix wording

`precision=1.0 recall=1.0 n=5 (AABB extents, fixture_only; not customer; not TZ >90%)`  
and run `python scripts/lint_claims.py --matrix-guard`.
