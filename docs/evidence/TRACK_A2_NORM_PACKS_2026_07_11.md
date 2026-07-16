---
title: "Track A2 — Norm / rule packs hardening"
status: complete-engineering
delivered_at: "2026-07-11"
tags: [aerobim, p1, norm-rule-packs, track-a]
---

# Track A2 — Norm / rule packs hardening (2026-07-11)

Strengthens the norm/rule-pack path for a future Samolet corpus **without** faking
"full GOST". Scope: CI schema gate, non-hardcoded customer path (manifest/env),
fail-closed capability, honesty in reason.

## Было / стало

| Item | До A2 | После A2 |
|---|---|---|
| Schema validation | только рантайм loader | **CI-gate**: `samples/rule-packs/*.json` × `norm-rule-pack.schema.json` (jsonschema Draft 2020-12) + loader round-trip |
| Customer path | только явный `norm_rule_pack_paths` в запросе | **manifest OR env** `AEROBIM_NORM_RULE_PACK` (storage-jail-resolved fallback), приоритет у manifest |
| Missing configured pack | n/a (или silent skip) | `capabilities.norm_rule_packs=failed` (fail-closed, не silent) |
| No pack | `skipped` | `skipped` (без изменений) |
| Non-approved pack | `[synthetic-template]` в reason | + явная пометка `advisory: non-approved pack(s) — not for deterministic sign-off` |
| Env misconfig (`../`, absolute, symlink) | n/a | `PathJailError` на резолве (fail-closed config) |
| Docs | contract only | + property→pack/IDS how-to table + manifest/env how-to |

## Atomic delivery (Clean Architecture preserved)

- **Core** (`core/config/settings.py`): `Settings.norm_rule_pack_path` (env
  `AEROBIM_NORM_RULE_PACK`).
- **Application** (`analyze_project_package.py`): use case gains
  `default_norm_rule_pack_path`; `_collect_norm_pack_requirements` → precedence
  (request manifest → env default → skipped) + new `_load_norm_packs` helper with
  tolerant (env, fail-closed capability) vs strict (request, raises) modes and
  non-approved advisory.
- **Infrastructure** (`di/bootstrap.py`): `_resolve_default_norm_pack_path`
  resolves the env default inside the storage jail (existence-tolerant) and wires
  it into the use case. No new DI token needed (loader token already existed).
- **Docs**: `docs/rule-packs/README.md` (how-to + table), `.env.example`
  (`AEROBIM_NORM_RULE_PACK`), TZ matrix "vs norms / design rules".

Layer direction unchanged: core → (none), application → core+domain,
infrastructure → core+domain+application.

## Verification

- New: `test_norm_rule_pack_schema.py` (4 tests: schema conformance, loader
  round-trip, approved-requires-approval), `test_norm_pack_env_capability.py`
  (9 tests: skipped/ok-via-env/failed-missing/request-precedence + Settings env +
  jail resolver incl. traversal rejection).
- Full backend: **377 passed, 2 skipped** (post-A1 364/2; +13 tests, 0 regressions).
- `test_wave0_soundness.py`, `test_layer_boundaries.py`,
  `test_p1_norm_section_integration.py` green (A1 section pairing untouched).

## Claim boundary (unchanged)

Delivered: loader + CI schema gate + manifest/env plumbing + capability honesty.
NOT delivered / NOT claimed: full SP/GOST, IDS 1.0 replacement, customer-approved
pack. `synthetic-template` remains sign-off-forbidden and is now explicitly marked
advisory in the capability reason.

## Customer blockers still open

1. Customer-**approved** residential pack (not `synthetic-template`) with each
   `rule_id` bound to EIR/ТЗ/company criterion.
2. Adjudicated corpus before any published precision (see Track A3).
3. Signed scope memo to flip pack `status` → `approved`.
