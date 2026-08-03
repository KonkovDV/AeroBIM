---
title: "Red Team — Studio grant stamp/PII gate (2026-08-03)"
status: active
version: "1.1.0"
last_updated: "2026-08-03"
claim_boundary: "Self red-team. Checkpoint NO_GO. Not external audit. Not DPA."
---

# Red Team — Yandex Studio stamp/PII + claims (2026-08-03)

**Author relationship:** self  
**Scope:** region-restricted VLM stamp exclude · grant≠RT-001 Claims Lock · report reproducibility wording  
**Checkpoint:** **NO_GO**  
**HEAD note:** allowlist + PII-prior clip landed after external review of `ab7f3fb` (RT-STAMP-07/08)

## Attack surface

| Threat | Path | Control |
|---|---|---|
| Signatory PII reaches Studio C0/C1 | region-crop → Base64 VLM | **Allowlist** `layout_role=content` only; stamp / title_block / unknown → exclude |
| Whole-sheet / large crop smuggles stamp | overlap-ratio denylist inverted | **Clip** PII priors out of allowlisted bbox (`subtract_aabb` / `clip_pii_priors`) |
| Detector omits `layout_role` | unlabeled region | Allowlist deny (unknown ≠ safe) |
| Page-pixel bbox without CRS | `_is_normalized` false → old fail-open | Fail-closed unless `page_width`/`page_height` enable normalize+clip |
| Operator flips guard via env | settings | **no env knob**; constructor only |
| Vendor log as sole audit | Studio history N/A | adapter prompt/response hashes + `x-client-request-id` |
| Overclaim Checkpoint via grant | tracker / pitch | Claims Lock forbids «quota increase = RT-001 progress» |

## Findings

| ID | Surface | Verdict |
|---|---|---|
| RT-STAMP-01 | Role-only exclude bypassed if `layout_role` missing | **MITIGATED** — allowlist deny |
| RT-STAMP-02 | Content band false-positive | **MITIGATED** — clip, not 50% ratio discard |
| RT-STAMP-03 | Page-pixel prior mis-use | **SUPERSEDED** by RT-STAMP-08 |
| RT-STAMP-04 | Exclude count invisible | **MITIGATED** — `SheetReadResult.stamp_regions_excluded` |
| RT-STAMP-05 | Title-block FIO (ГОСТ 2.104) | **MITIGATED** — `title_block` not on allowlist; title prior also clipped from content |
| RT-STAMP-06 | Prior incomplete (e.g. left vertical inscription) | **OPEN** — allowlist is primary; prior is clip-only aid; customer geometry validation still required before CONFIDENTIAL |
| RT-STAMP-07 | Full sheet / bottom band bypass via low overlap ratio | **MITIGATED** — clip priors; tests assert no residual overlaps stamp |
| RT-STAMP-08 | Pixel bbox + unknown role fail-open | **MITIGATED** — exclude; content+pixels need page size |
| RT-CLAIM-01 | Grant tokens = RT-001 progress | **MITIGATED** |
| RT-CLAIM-02 | Model non-determinism blocks FAIR report | **MITIGATED** |
| RT-CLAIM-03 | Scenario 5.3 ⇒ Checkpoint GO | **MITIGATED** |

## Doctrine note

Gate matches project fail-closed: unknown role does **not** authorize egress (same spirit as `data_classification` unknown → CONFIDENTIAL / trust unknown → BLOCKED). Denylist-of-stamp was the inverted form and is retired.

## Still open (external)

RT-001 / RT-002 / RT-003 · customer geometry validation for left/rotated title blocks tagged as `content` · D-7 batch · live Studio multimodal 5.3 · DPA for CONFIDENTIAL

## Verdict

Stamp/PII eng-gate **allowlist+clip** acceptable under Claims Lock for PUBLIC/INTERNAL fixture crops. Checkpoint **NO_GO**. Do not claim RESTRICTED-safe Studio VLM without C2 or validated sheet geometry.
