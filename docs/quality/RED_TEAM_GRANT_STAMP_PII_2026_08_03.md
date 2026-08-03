---
title: "Red Team — Studio grant stamp/PII gate (2026-08-03)"
status: active
version: "1.2.0"
last_updated: "2026-08-03"
claim_boundary: "Self red-team. Checkpoint NO_GO. Not external audit. Not DPA."
---

# Red Team — Yandex Studio stamp/PII + claims (2026-08-03)

**Author relationship:** self  
**Scope:** region-restricted VLM PII gate · cropper CRS · grant≠RT-001 Claims Lock  
**Checkpoint:** **NO_GO**  
**HEAD wave:** allowlist+clip (`1b433ad`) → CRS / bottom-band / ready-guard harden (this revision)

## Attack surface

| Threat | Path | Control |
|---|---|---|
| Signatory PII → Studio C0/C1 | region-crop Base64 VLM | Allowlist `content` only; stamp/title/unknown → exclude |
| Whole-sheet / bottom-band smuggle | overlap-ratio denylist | Clip full bottom band `(0,0.85)–(1,1)` from allowlisted crops |
| Middle-bottom inscription residual | split stamp+title priors | **MITIGATED** — single full bottom prior |
| Pixel/unknown CRS fail-open | unnormalized bbox | Exclude without page size; invalid bbox exclude |
| Normalized plan + page-point cropper | DI/smoke default CRS | **MITIGATED** — cropper wired `normalized-0-1`; page-point refuses ambiguous 0..1 boxes |
| Operator disables PII on ready pipeline | constructor | **MITIGATED** — `ready=True` requires guard on |
| Whole-sheet Kimi smoke | separate pipeline | fail-closed on pilot/production; not verdict path |
| Grant = Checkpoint progress | claims | Claims Lock forbids |

## Findings

| ID | Surface | Verdict |
|---|---|---|
| RT-STAMP-01..05, 07, 08 | prior wave | **MITIGATED** (allowlist+clip) |
| RT-STAMP-06 | Left/rotated vertical title tagged `content` | **OPEN** — allowlist primary; prior does not cover vertical strip; need customer geometry |
| RT-STAMP-09 | Plan emits normalized-0-1; DI cropper was page-point → silent ~1pt crops / CRS mismatch | **MITIGATED** — bootstrap+smoke `normalized-0-1`; croppers raise on ambiguous page-point+0..1 |
| RT-STAMP-10 | Middle-bottom FIO between split priors | **MITIGATED** — full bottom band prior |
| RT-STAMP-11 | `ready=True` + `exclude_stamp_regions=False` | **MITIGATED** — constructor ValueError |
| RT-CLAIM-01..03 | overclaim | **MITIGATED** |

## Doctrine

Unknown role does not authorize egress (same spirit as `data_classification` unknown → CONFIDENTIAL). Clip is not a denylist substitute for allowlist.

## Still open (external)

RT-001 / RT-002 / RT-003 · RT-STAMP-06 customer geometry · D-7 batch · live Studio multimodal 5.3 · DPA for CONFIDENTIAL

## Verdict

PII eng-gate **allowlist + bottom-band clip + CRS fail-closed** acceptable under Claims Lock for PUBLIC/INTERNAL fixtures. Checkpoint **NO_GO**.
