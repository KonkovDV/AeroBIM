# Samolet Pilot — Environment & Runbook (2026-07)

**Checkpoint:** `NO_GO` until RT-001 / RT-002 / RT-003 customer evidence.  
**Profile:** `AEROBIM_SIGNOFF_PROFILE=samolet_pilot` — fail-closed clash / MEP / unit_scale / intake.

## Required environment matrix

| Variable | Pilot value | Purpose | Blocks pass if wrong |
|---|---|---|---|
| `AEROBIM_ENV` | `production` or explicit pilot host | Non-dev defaults | Anonymous access |
| `AEROBIM_SIGNOFF_PROFILE` | `samolet_pilot` | Fail-closed capabilities | Soft pass |
| `AEROBIM_CUSTOMER_INTAKE` | path to signed gate JSON | Phase B intake | `AEROBIM-CUSTOMER-INTAKE` ERROR |
| `AEROBIM_API_BEARER_TOKEN` and/or OIDC | configured | Auth | 401 / startup fail |
| `AEROBIM_MEP_FEDERATED_SCOPE_PATH` | `samples/mep/federated-scope-template.json` until customer VERIFIED scope | RT-003 wiring | `mep_system_clash=NOT_VERIFIED` |
| `AEROBIM_MEP_SCOPE_MEMO_REF` | customer memo id when MEP in scope | Scope honesty | MEP probe fail-closed |
| `AEROBIM_IFC_PARSE_CACHE_DIR` | e.g. `/var/aerobim/ifc-cache` | Perf observability only | — (not SLA claim) |
| `AEROBIM_REQUIRE_CLASH` | `true` when clash in scope | Capability gate | BLOCKED |
| `AEROBIM_REQUIRE_MEP_SYSTEM_CLASH` | `true` when MEP in scope | Capability gate | BLOCKED |

## Forbidden to set without evidence

| Variable / claim | Why |
|---|---|
| Customer SLA ≤30 min | Requires `measure_package_sla` on real pack |
| `AEROBIM_MEP_SYSTEM_CLASH_ENABLED=true` without VERIFIED federated scope | RT-003 |
| Invented `AEROBIM_MEP_SCOPE_MEMO_REF` | Customer sign-off only |

## Federated MEP scope template

Template (empty, `NOT_VERIFIED`): [`../../samples/mep/federated-scope-template.json`](../../samples/mep/federated-scope-template.json)

Engineering verified **fixture** (not customer RT-003): [`../../samples/mep/federated-scope-verified-fixture.json`](../../samples/mep/federated-scope-verified-fixture.json)  
→ status **`ENG_FIXTURE`** (never `VERIFIED` without expert_signoff); `samples/mep/hvac-sprinkler-systems.ifc` + template matrix. Capability **`NOT_VERIFIED`**. Findings are WARNING/`Comment` only (co-presence, not Clash).

Customer VERIFIED scope must include:

```json
{
  "schema_version": "1.0.0",
  "status": "VERIFIED",
  "scope_memo_ref": "<customer-memo-id>",
  "federated_ifc_paths": ["samples/customer/hvac.ifc", "samples/customer/sprinkler.ifc"],
  "clearance_matrix_ref": "samples/customer/mep-clearance-matrix.json",
  "expert_signoff": {
    "signed_by": "<expert>",
    "signed_at": "<ISO-8601>"
  }
}
```

Paths must be **repo-relative** (absolute / `..` rejected by path jail). Until customer geometry + signed matrix: no `AEROBIM-MEP-FORBIDDEN` ERROR, no BCF Clash from template, checkpoint **`NO_GO`**.

## Pilot run sequence

```bash
# 1. Validate intake gate (must not be all-false for pilot analyze)
cd backend
python -m aerobim.tools.validate_customer_intake_gate \
  --gate ../audit/evidence/customer-intake-gate.json

# 2. Profile contour timings (fixture baseline — not customer SLA)
python -m aerobim.tools.profile_package_trace \
  --pack ../samples/benchmarks/project-package-baseline.json \
  --output ../docs/evidence/package-profile-trace-latest.json

# 3. Evidence bundle under production policy evaluation
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/customer/<agreed-pack>.json \
  --output ../audit/evidence/pilot-run-<date>
```

## Evidence artifacts per run

| Artifact | Path |
|---|---|
| Runtime baseline | `docs/evidence/runtime-baseline-latest.json` |
| Profile trace | `docs/evidence/package-profile-trace-latest.json` |
| Run manifest | `run_manifest.json` inside evidence bundle |
| Intake gate | `audit/evidence/customer-intake-gate.json` |
| BCF T2 (customer) | empty template — `NOT_VERIFIED` |

## Related docs

- [`../pilot-protocol-samolet-2026.md`](../pilot-protocol-samolet-2026.md)
- [`../quality/CUSTOMER_PILOT_BACKLOG_2026_07_21.md`](../quality/CUSTOMER_PILOT_BACKLOG_2026_07_21.md)
- [`../security/PILOT_THREAT_MODEL_2026_07.md`](../security/PILOT_THREAT_MODEL_2026_07.md)
