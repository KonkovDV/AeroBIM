# PD/RD consistency pilot (synthetic, 2026-09)

Narrow class: **IfcWall `Qto_WallBaseQuantities.Width` vs PDF text-layer `WALL-01 thickness/width`**.

This is a source contradiction, not a SP/regulatory finding and not a claim that the
whole PD/RD pack is checked. Inputs are synthetic. `customer_go` stays false.
CDE BCF import is **NOT_VERIFIED**. Geometry-derived IfcSpace area is **not_implemented**.

## Command

From `backend/`:

```text
python -m aerobim.tools.ensure_pd_rd_pilot_drawings
python -m aerobim.tools.run_pd_rd_consistency_pilot --variant defect --out var/pd-rd-defect
python -m aerobim.tools.run_pd_rd_consistency_pilot --variant clean --out var/pd-rd-clean
```

Optional local expert journal (not OIDC; LLM cannot sign):

```text
python -m aerobim.tools.run_pd_rd_consistency_pilot --variant defect --out var/pd-rd-defect --expert-verdict accepted --expert-subject lab-expert
```

Variants: `clean`, `defect`, `unit`, `missing`, `ambiguous`, `mixed-rev`, `parser-error`, `unsupported`, `ifc-missing-width`.

## Expected difference

| Variant | Expected machine result |
|---|---|
| clean / unit | no `AEROBIM-PD-RD-WALL-WIDTH` hard conflict |
| defect | hard conflict with both values, GUID, page, evidence refs |
| missing / ifc-missing-width / parser-error / unsupported / ambiguous | cannot-verify (not a project violation); no positive pass |
| mixed-rev | mixed revision detected; values not treated as same-revision evidence |

Default HTTP mode: `GET /v1/auth/bff` is 501; shared bearer and `anonymous-dev` cannot assign expert status.
