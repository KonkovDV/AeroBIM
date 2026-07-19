# RED TEAM RESIDUAL SLICE — Defense depth — 2026-07-19

**After:** norm-pack ACL residual (`0990af1`)  
**Checkpoint:** `NO_GO` (RT-001 / RT-002 / RT-003 still OPEN)

---

## Mitigations

| ID | Theme | Status |
|---|---|---|
| RT-R12-001 | IFC/drawing object keys prefixed `tenants/{tid}/…` when tenant bound | **MITIGATED** |
| RT-R12-002 | Advisory ERROR agent cannot change `passed` / engine error_count | **MITIGATED** (matrix unit + DeterminismGate) |
| RT-R12-003 | ZIP member limits + path-jail double-dot adversarial cases | **MITIGATED** |

## Explicit confirmation

No claim inflation. External blockers unchanged. PR #10/#11 untouched.
