<!-- claims-lint: allow-file reason="KT#2 fixture handoff index; forbidden phrases only as non-claims" -->
---
title: "KT#2 handoff pack — 2026-08-11"
date: "2026-08-11"
claim_boundary: "Fixture GO / methodology handoff. Checkpoint NO_GO until RT-001/002/003."
---

# KT#2 handoff pack (2026-08-11)

**Verdict for jury:** methodology + fixture contour is ready to show.  
**Product checkpoint:** **NO_GO** (RT-001 corpus · RT-002 norm pack · RT-003 MEP).

Machine status: [`STATUS.json`](./STATUS.json)

**17.08 sell-path (wedge freeze):** `python -m aerobim.tools.run_demo_ifc_acceptance_gate` → `artifacts/ifc-acceptance-gate-demo/`. Overlay `run_demo_vertical_slice` is P1 of the same evidence chain. Video 2–3 min is **not recorded and not attached**.

**Superseded 11.08 HTML is not in the public tree.** Live overlay (P1): `python -m aerobim.tools.run_demo_vertical_slice` and pin [`../vertical-slice-demo-live-2026-08-14.md`](../vertical-slice-demo-live-2026-08-14.md). Do not open snapshot HTML as overlay.

## What to open in the meeting (30–40 min)

| # | Artifact | Path |
| --- | --- | --- |
| 1 | **Live Acceptance Gate (sell-path)** | `python -m aerobim.tools.run_demo_ifc_acceptance_gate` → `artifacts/ifc-acceptance-gate-demo/` |
| 1b | **Live overlay (P1)** | `python -m aerobim.tools.run_demo_vertical_slice` → `artifacts/vertical-slice-demo/report.html` (`#kt2-overlay`) |
| 2 | This STATUS | `docs/evidence/kt2-handoff-2026-08-11/STATUS.json` |
| 3 | Wall-guid **GUID-mismatch bundle** (not overlay) | `wall-guid/` — `summary.passed=false`. **Do not** open `wall-guid/report.html` as the KT#2 slice |
| 4 | Vertical slice **11.08 snapshot** (JSON only) | `vertical-slice/slice-summary.json` + `LIMITATIONS.json` |
| 5 | Harness dry-run (synthetic, not publishable) | `harness-dryrun/pilot-harness-report.json` |
| 6 | Clash fixture measure (AABB n=6) | [`../clash-measurement-slice-2026-08/`](../clash-measurement-slice-2026-08/) |
| 7 | Drawing overlay smoke PNG | [`../drawing-overlay-smoke-2026-08/`](../drawing-overlay-smoke-2026-08/) |
| 8 | Video | Not recorded. Notice: [`../../demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](../../TIER0_INDEX.md) |

**Do not open** `wall-guid/report.html` as the overlay demo (no `#kt2-overlay` on the 11.08 HTML).

## Regenerate (fixture only)

```powershell
cd backend
python -m aerobim.tools.export_evidence_bundle --pack ../samples/benchmarks/project-package-wall-guid-demo.json --output ../docs/evidence/kt2-handoff-2026-08-11/wall-guid
python -m aerobim.tools.verify_evidence_bundle --bundle ../docs/evidence/kt2-handoff-2026-08-11/wall-guid
python -m aerobim.tools.run_vertical_slice --manifest ../samples/demo/vertical-slice-2026-08-11/manifest.json --output ../docs/evidence/kt2-handoff-2026-08-11/vertical-slice
python -m aerobim.tools.run_pilot_harness --labels ../samples/benchmarks/detection-precision/labels-synthetic.json --detections ../samples/benchmarks/detection-precision/detections-synthetic.json --output ../docs/evidence/kt2-handoff-2026-08-11/harness-dryrun
python -m aerobim.tools.run_pilot_harness --labels ../samples/benchmarks/detection-precision/labels-synthetic.json --detections ../samples/benchmarks/detection-precision/detections-synthetic.json --require-publishable
# expect exit 1
python -m aerobim.tools.measure_extent_clash_fixture
python -m aerobim.tools.render_drawing_overlay_evidence
```

## Forbidden speech

Do **not** say: customer accuracy >90%, SLA ≤30 min on customer pack, native DWG ready, MEP delivered, OIDC BFF production-ready, CV understands drawings.

**Do** say: fixture GO, harness ready, measured AABB extents on synthetic IFC (n=6, not duplex inventory 654), deterministic overlay illustration, waiting on Samolet corpus/pack/experts.
