# BatchPlan feasibility probe

**Date:** 2026-08-04  
**Status:** tool pin — **not wired** into AeroBIM runtime  
**Claim level:** inventory / engineering note

## Verified

| Item | Value |
|---|---|
| Repo | https://github.com/byildiz/BatchPlan |
| License | **MIT** |
| Role | IFC → floor-plan PNG / WKT for planting drawing↔model defects |
| Example data in upstream | Schependomlaan IFC (tool repo examples) |

## Blockers (this environment)

1. **`pythonocc-core`** — BatchPlan requires conda `pythonocc-core` (not in AeroBIM locked pip wheel set).  
2. GUI dependency for `mark_floors` (headless CI friction).  
3. Do **not** pull KAAN project data via BatchPlan paper association (see [`KAAN_LICENSE_HONESTY_2026_08_04.md`](KAAN_LICENSE_HONESTY_2026_08_04.md)).

## Recommended next path

1. Keep BatchPlan as **external optional** pipeline (conda env), not a new AeroBIM pip dependency.  
2. Plant defects on **license-cleared** IFC (IFC-Bench duplex/dental non-GPL, OSArch after read).  
3. Emit GT JSON compatible with Sprint-2 detection metrics method.

Does not close RT-001. Does not change Checkpoint **GO**; customer_go false.
