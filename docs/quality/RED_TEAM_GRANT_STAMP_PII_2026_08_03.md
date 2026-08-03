---
title: "Red Team — Studio grant stamp/PII gate (2026-08-03)"
status: active
version: "1.4.0"
last_updated: "2026-08-03"
claim_boundary: "Self red-team. Checkpoint NO_GO. Not external audit. Not DPA. Priors=hypothesis until customer sheets."
---

# Red Team — Yandex Studio stamp/PII + claims (2026-08-03)

**Author relationship:** self  
**Scope:** region-restricted VLM PII gate · `/Rotate` · overflow clamp · coverage counters  
**Checkpoint:** **NO_GO**  
**Claim boundary:** «PII guard active» OK · «ПДн не уходят в облако» **not** claimable until Samolet sheet validation

## Attack surface

| Threat | Path | Control |
|---|---|---|
| Signatory PII → Studio | region-crop VLM | Allowlist `content` + visual priors clipped in page space |
| `/Rotate 90` landscape CAD | priors in visual space vs raw page | Map priors by rotate; unknown rotate → fail-closed |
| CropBox < MediaBox overflow | norm > 1 escapes priors | Overflow >2% → exclude (no >1 residuals) |
| Future roles silent drop | allowlist | `excluded_unknown_role` + coverage alarm in reason |
| Kill-switch | ready + guard off | ValueError |
| Grant = Checkpoint | claims | Forbidden |

## Findings

| ID | Verdict |
|---|---|
| RT-STAMP-01..13 | **MITIGATED** (prior waves) |
| RT-STAMP-14 `/Rotate` | **MITIGATED** — `priors_in_page_space` + `read_page_rotate_degrees`; None → skip VLM |
| RT-STAMP-15 overflow | **MITIGATED** — `_finalize_normalized` reject / clamp |
| RT-STAMP-16 counters / coverage | **MITIGATED** — `excluded_by_role` / `excluded_by_geometry` / `excluded_unknown_role` |
| Customer prior validation | **OPEN** — fixtures ≠ Samolet sheets |
| RT-001/002/003 | **OPEN** — external |

## Verdict

Eng PII gate hardened through RT-STAMP-14..16. Checkpoint **NO_GO**. Do not claim RESTRICTED-safe cloud VLM without customer geometry + DPA/C2.
