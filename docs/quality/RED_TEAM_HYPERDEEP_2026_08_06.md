---
title: "Red Team Hyperdeep Audit — 2026-08-06"
status: active
version: "1.0.0"
last_updated: "2026-08-06"
claim_boundary: "Engineering remediations only. Checkpoint NO_GO until RT-001/002/003. Fixes do not close customer blockers."
---

# Red Team Hyperdeep Audit — 2026-08-06

**Method:** parallel architecture + security exploration → confirmed defects → code+tests → focused pytest.  
**Checkpoint:** still **`NO_GO`** (RT-001 / RT-002 / RT-003 unchanged).

## Findings fixed

| ID | Severity | Defect | Fix |
|---|---|---|---|
| RT-HD-01 | **BLOCKER** | `_advisory_object_kind` substring `"fixture" in path` → customer `office_fixture_v2.ifc` classified `public_fixture` → cloud overlay egress | Trusted prefixes only: `/samples/`, `/fixtures/` |
| RT-HD-02 | **CRITICAL** | `build_remark_llm_request` forced `allow_synthetic_public=True`, so `allow_customer_data=False` never blocked | Default `allow_synthetic_public=False`; analyze overlay sets True only for `public_fixture` |
| RT-HD-03 | **HIGH** | Cross-tenant path jail returned **403** + prefix oracle | **404** `"Object not found"` |
| RT-HD-04 | **HIGH** | `safe_storage_token("..")` → `".."` escaped upload/quota paths | Reject `.`/`..`; encode `.` as `!2e` |
| RT-HD-05 | **HIGH** | Double-encoded tenant prefix (`safe_storage_token` then `tenant_storage_prefix`) → collision `a/b` vs `a!2fb` | Encode once via `tenant_storage_prefix(tenant_key)` + jail resolve before write |
| RT-HD-06 | **HIGH** | Application → Infrastructure (`ifc_space_inventory`) | Port `IfcSpaceInventoryExtractor` + DI token `IFC_SPACE_INVENTORY` + adapter class |
| RT-HD-07 | **HIGH** | Application → Tools (`validate_customer_intake_gate`) | Logic moved to `application/services/customer_intake_gate.py`; tools = thin CLI wrapper |
| RT-HD-08 | **MEDIUM** | Absolute FS paths in analyze API errors / reinforcement digest | Generic `"file not found"`; storage-relative path only |
| RT-HD-09 | **MEDIUM** | Zip extract without post-join containment | `target.resolve().is_relative_to(extract_root)` |
| RT-HD-10 | **MEDIUM** | Quota store naive path join | `safe_storage_token` + relative_to quotas root |

## Held (no additional HARD defect)

DeterminismGate / `summary.passed` cannot be flipped by LLM; pilot/production clash-MEP fail-closed; report ACL 404; BCF ZIP member paths UUID-only; OIDC BFF stubs honest 501; outbound SSRF via `safe_urlopen`; `@sota-stub` entries tracked in `KNOWN_BUGS.md`.

## Inventory delta

| Metric | Before | After |
|---|---:|---:|
| Public domain Protocol ports | 46 | **47** |
| Adapter modules | 71 | 71 |
| DI tokens | 59 | **60** |

## Evidence

- New tests: `backend/tests/test_rt_hyperdeep_2026_08_06.py`
- Regression: RT-030 overlay, path jail, mutation ACL, qwen/advisory, pilot intake, runtime baseline
- Runtime baseline regenerated with architecture_inventory 47/71/60

## Not claimed

Product accuracy, customer SLA, DWG-ready, MEP delivered, CDE-ready BCF, Checkpoint GO.
