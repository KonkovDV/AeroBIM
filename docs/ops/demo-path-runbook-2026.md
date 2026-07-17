---
title: "Demo path runbook — upload → analyze → review → BCF"
status: active
last_updated: "2026-07-11"
tags: [aerobim, ops, demo, bcf, openbim, track-a5]
---

# Runbook: TechLab / Task 07 demo path (Track A5)

Цель — за **один прогон** показать детерминированный контур Task 07 на
**fixture** (не на корпусе Самолёта): ingest → analyze → review exports →
**BCF 2.1 ZIP**.

## World practice (openBIM)

| Practice | AeroBIM demo posture |
|---|---|
| buildingSMART **IDS → IFC check → issue handoff** | Fixture pack includes IDS + IFC; findings → BCF topics |
| **BCF-XML file exchange** (default week-1) | `GET /v1/reports/{id}/export/bcf?version=2.1` |
| **BCF-API / OpenCDE** | Escalation only — see [`../pilot-cde-handoff-2026.md`](../pilot-cde-handoff-2026.md) Scenario B |
| Expert remains accountable | Claim boundary + HITL remarks; no autonomous sign-off |

References: [bSI BCF](https://technical.buildingsmart.org/standards/bcf/),
[BCF-XML](https://github.com/buildingSMART/BCF-XML),
[BCF-API](https://github.com/buildingSMART/BCF-API).

## Claim boundary (say this on stage)

**Proven by this runbook / CLI:** multipart upload, deterministic analyze on
fixture, report fetch, HTML export, BCF ZIP **structural smoke** (VersionId +
GUID-folder `markup.bcf` + Topic). Fixture wall-clock ≪ 30 min.

`loop_ok` / exit 0 means the **API chain** worked. `analyze_passed` is separate
and may be `false` when the fixture correctly finds issues.

**Do not claim:** customer accuracy >90%, full SP/GOST, Solibri replacement,
autonomous sign-off, `customer_confirmed` typical-errors, CDE import proof,
full buildingSMART BCF conformance certification.

## 0. Prerequisites

```powershell
cd AeroBIM\backend
python -m pip install -e ".[dev]"
```

Optional UI follow-up: frontend deps + `python -m aerobim.tools.run_live_review_smoke`.

## 1. One-command API demo (preferred gate)

```powershell
cd AeroBIM\backend
python -m aerobim.tools.run_demo_path `
  --output ..\docs\evidence\demo-path-pilot-moscow-2026-07-11.json
```

Console script alias: `aerobim-run-demo-path`.

Exit 0 + `"ok": true` means the loop passed. Inspect `steps` and
`claim_boundary` in the JSON.

Default pack: `samples/benchmarks/project-package-pilot-moscow-v1.json`.

## 2. Manual curl path (same semantics)

Start backend with an isolated storage dir, then:

1. `POST /v1/uploads` — IFC binary  
2. Stage IDS / TZ / calc / drawings into the storage jail  
3. `POST /v1/analyze/project-package` with storage-relative paths  
4. `GET /v1/reports/{report_id}`  
5. `GET /v1/reports/{report_id}/export/html`  
6. `GET /v1/reports/{report_id}/export/bcf?version=2.1` → save `.bcfzip`  
7. Open ZIP: must contain `bcf.version` (VersionId) + ≥1 `{uuid}/markup.bcf` with Topic

> Note: `run_demo_path` uses in-process ASGI (`TestClient`) with **development**
> auth. Do not point `--storage-dir` at a production jail.

## 3. Browser review (optional, visual)

```powershell
python -m aerobim.tools.run_live_review_smoke
```

Or seed + open frontend — see [`../../ops/smoke-path.md`](../../ops/smoke-path.md).

Demo script for humans:

1. Open report list → select demo report  
2. Show 3D IFC highlight + 2D problem zone (if present)  
3. Filter by severity / edit one remark (HITL)  
4. Download BCF 2.1 — state: «week-1 handoff = file import into CDE»

## 4. SLA rail (fixture only)

```powershell
python -m aerobim.tools.measure_package_sla `
  --pack ..\samples\benchmarks\project-package-pilot-moscow-v1.json `
  --max-minutes 30 `
  --output ..\docs\evidence\samolet-sla-demo-fixture.json
```

Customer SLA remains TBD until an agreed Samolet pack is measured.

## 5. After demo — what to ask Samolet

Use [`../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md):
approved pack, corpus, 2 adjudicators, CDE+BCF version, baseline hours.

## Related

- Evidence: [`../evidence/TRACK_A5_DEMO_PATH_2026_07_11.md`](../evidence/demo-path-pilot-moscow-2026-07-11.json)
- Intake precision (when corpus arrives): [`intake-precision-runbook-2026.md`](intake-precision-runbook-2026.md)
- Claim boundary: [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)
