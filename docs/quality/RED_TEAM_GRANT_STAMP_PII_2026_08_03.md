---
title: "Red Team — Studio grant stamp/PII gate (2026-08-03)"
status: active
version: "1.3.0"
last_updated: "2026-08-03"
claim_boundary: "Self red-team. Checkpoint NO_GO. Not external audit. Not DPA."
---

# Red Team — Yandex Studio stamp/PII + claims (2026-08-03)

**Author relationship:** self  
**Scope:** region-restricted VLM PII gate · cropper CRS · absolute-CRS fail-closed · grant≠RT-001  
**Checkpoint:** **NO_GO**  
**HEAD wave:** allowlist+clip → CRS/bottom-band → left-strip + absolute-CRS harden (v1.3)

## Attack surface

| Threat | Path | Control |
|---|---|---|
| Signatory PII → Studio C0/C1 | region-crop Base64 VLM | Allowlist `content` only |
| Whole-sheet / bottom / left title | oversized content crop | Clip priors: bottom `(0,0.85)–(1,1)` + left `(0,0)–(0.10,1)` |
| `page-pixel` values ≤1 auto-normalized | `_is_normalized_bbox` alone | Absolute CRS requires page size (RT-STAMP-12) |
| Normalized plan + page-point cropper | DI/smoke | Cropper `normalized-0-1`; page-point refuses 0..1 |
| Non-normalized task under PII guard | pipeline `_read_one` | Refuse crop unless task CRS is `normalized-0-1` |
| Disable PII on ready pipeline | constructor | ValueError |
| Whole-sheet Kimi smoke | separate path | HybridRouteGate; not verdict; not DI default |
| Grant = Checkpoint progress | claims | Claims Lock forbids |

## Findings

| ID | Surface | Verdict |
|---|---|---|
| RT-STAMP-01..05, 07..11 | prior waves | **MITIGATED** |
| RT-STAMP-06 | Left/rotated vertical title in content | **MITIGATED** for ≤10% left strip prior; wider/atypical forms still need customer geometry validation |
| RT-STAMP-12 | Absolute CRS with coords ≤1 treated as normalized | **MITIGATED** — explicit absolute CRS never auto-promotes |
| RT-STAMP-13 | Task CRS ignored at crop time | **MITIGATED** — guard path requires `normalized-0-1` on task |
| RT-CLAIM-01..03 | overclaim | **MITIGATED** |

## Doctrine

Unknown role does not authorize egress. Absolute CRS does not silently become relative. Clip complements allowlist; it does not replace it.

## Still open (external)

RT-001 / RT-002 / RT-003 · atypical title geometry beyond 10% left / 15% bottom priors · D-7 batch · live Studio multimodal 5.3 · DPA for CONFIDENTIAL · whole-sheet smoke remains operator-gated only

## Verdict

PII eng-gate **allowlist + dual priors + absolute-CRS fail-closed** acceptable under Claims Lock for PUBLIC/INTERNAL fixtures. Checkpoint **NO_GO**.
