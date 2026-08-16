<!-- claims-lint: allow-file reason="Red Team audit evidence; documents OPEN residuals without Checkpoint GO" -->
---
title: "Red Team audit — tracker sprint 15.08 evening"
claim_boundary: "Eng findings only. Checkpoint NO_GO unchanged. Not customer accuracy."
---

# Red Team audit (2026-08-15 evening)

**Scope:** uncommitted KT#2 hardening + tracker tasks 1–6 (IFC matrix refresh, dataset hunt/re-run, consult pack, GTM KPI, open-core options). Independent security-review of the dirty tree: **no Critical / High / Medium**.

**Honesty lock (unchanged):** Checkpoint **NO_GO**; RT-001 / RT-002 / RT-003 OPEN; `auth_bff` default `NOT_IMPLEMENTED`; BCF T2 `NOT_VERIFIED`; native DWG `NOT_IMPLEMENTED`; VLM advisory only.

## Security (code)

Independent review of OIDC BFF Phase 3, rate-limit, overlay renderer: nonce bind, HMAC cookie, redirect allowlist, `safe_urlopen` token exchange, GET `/v1/auth/login|callback|session` share a budget, BFF cookie does **not** satisfy `require_bearer_auth` on `/v1/*`. pypdfium2 swap is CLI/fixture-only.

| Sev | Finding | Disposition |
|---|---|---|
| INFO | Lab mock IdP without JWKS → session with `identity_verified=false` | Documented; not production SSO |
| INFO | In-memory session/state stores | Lab scale only |
| INFO | Token-exchange `response.read()` uncapped | URL is operator-configured and SSRF-gated |

## Honesty / tracker (docs + evidence)

| Sev | Finding | Disposition |
|---|---|---|
| MED | Schema-suite clash flipped `failed` → `skipped` after tiny-skip | **Closed:** live matrix + exporter note name `AEROBIM_CLASH_SKIP_TINY`; all-skipped still fail-closed. Not a silent pass |
| MED | Tracker asked to re-run PNST 909 22-scenario IDS | **Closed as honesty (15.08):** pack on disk; runtime snapshot stays 05.08; **no CLI in tree that night**. **16.08:** CLI is in tree; live pack is still a header sample → `SKIPPED_PACK_INCOMPLETE`; still do not invent 18/22 |
| LOW | IFC-Bench / AEC-Bench numbers can be misread as product accuracy | **Closed:** hunt log + smoke JSON `open_bench_only`, Harbor **NOT_RUN**, 27/1026 countable subset |
| LOW | Consult minutes could be invented | **Closed:** journal stays empty until owner notes; Burnaev 12.08 still unrecorded |
| LOW | Commercial KPI could be faked as 3–5 | **Closed:** GTM says live count is `.local/commercial-ops/` only; git does not invent scheduled demos |

## Still OPEN (by design)

- RT-001 / RT-002 / RT-003 → Checkpoint **NO_GO**
- Harbor 160 / AEC-Bench drawing-reading false-pass **NOT_MEASURED**
- BCF T2 CDE import `NOT_VERIFIED`
- STUB-ODA-CAD-001 / MEP-CLASH-001
- OIDC production IdP + FE bearer removal
- No PNST 22-scenario regenerator in tree

## 16.08 addendum

CLI `run_pnst909_22_scenario_runtime` is now in tree. Frozen pairing covers 22 scenarios. Live pack on the audit host is still a header sample, so the CLI returns `SKIPPED_PACK_INCOMPLETE` and does **not** overwrite the 05.08 18/22 snapshot. Ishigaki gold XML document-audit is processability, not generation F1.

## Do not say after this pass

Checkpoint GO; product accuracy >90%; SLA ≤30 min; DWG-ready; MEP delivered; CDE-ready; OIDC BFF / SSO ready; «AEC-Bench прогнан агентом»; «18/22 пересняли сегодня»; «3–5 демо уже назначены».

## Honesty

No flip of `summary.passed`, `auth_bff=implemented`, `mep_system_clash=OK`, `dwg_dxf=OK`, or BCF T2 `VERIFIED`.
