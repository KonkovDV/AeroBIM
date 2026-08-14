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

**Superseded demo HTML:** `vertical-slice/report.html` is the **11.08 snapshot** and does not contain `#kt2-overlay`. For the live CLI demo run `python -m aerobim.tools.run_demo_vertical_slice` and use pin [`../vertical-slice-demo-live-2026-08-14.md`](../vertical-slice-demo-live-2026-08-14.md). Do not open the 11.08 HTML on the tracker call.

## What to open in the meeting (30–40 min)

| # | Artifact | Path |
| --- | --- | --- |
| 1 | This STATUS | `docs/evidence/kt2-handoff-2026-08-11/STATUS.json` |
| 2 | Wall-guid evidence bundle (verified) | `wall-guid/` — `summary.passed=false`, outcome BLOCKED |
| 3 | Vertical slice (PDF text-layer honesty) | `vertical-slice/slice-summary.json` + `LIMITATIONS.json` |
| 4 | Harness dry-run (synthetic, not publishable) | `harness-dryrun/pilot-harness-report.json` |
| 5 | Clash fixture measure (AABB n=5) | [`../clash-measurement-slice-2026-08/`](../clash-measurement-slice-2026-08/) |
| 6 | Drawing overlay smoke PNG | [`../drawing-overlay-smoke-2026-08/`](../drawing-overlay-smoke-2026-08/) |
| 7 | Mentor pack | [`../../demo/mentor-mikhail-2026-08-11/`](../../demo/mentor-mikhail-2026-08-11/) |
| 8 | Demo format | [`../../demo-format-2026-08.md`](../../demo-format-2026-08.md) |
| 9 | Workplan DoD | [`../../pilot/PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md`](../../pilot/PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md) |
| 10 | Customer blockers eng pack | [`../../audit/RT_CUSTOMER_BLOCKERS_ENG_PACK_2026_08_11.md`](../../audit/RT_CUSTOMER_BLOCKERS_ENG_PACK_2026_08_11.md) |

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

**Do** say: fixture GO, harness ready, measured AABB extents on synthetic IFC (n=5), deterministic overlay illustration, waiting on Samolet corpus/pack/experts.
