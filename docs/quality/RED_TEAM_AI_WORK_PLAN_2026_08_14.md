<!-- claims-lint: allow-file reason="Red Team of 14.08 work plan; forbidden phrases listed as non-claims; NO_GO explicit" -->
---
title: "Red Team — work plan 14.08.2026 (no code)"
status: active
version: "1.0.0"
last_updated: "2026-08-14"
claim_boundary: >
  Internal Red Team of the 14.08 work plan. Checkpoint remains NO_GO. Does not close
  RT-001/002/003. Not product accuracy. Not Tangl/10D integration. No code changes.
---

# Red Team — план работ 14.08 (код не трогаем)

**Author relationship:** Internal self-assessment  
**Scope:** `docs/pilot/AI_WORK_PLAN_2026_08_14.md` (detailed no-code plan)  
**Code / architecture:** **unchanged** (freeze: no new ports, adapters, DI)  
**Checkpoint:** **`NO_GO`**

## Verdict

| Lane | Result |
|---|---|
| Application security (Critical/High) | **0** — no runtime change |
| Integrity (Medium) | **0 open** — plan explicitly forbids code changes |
| Claims Lock | **PASS** — all forbidden phrases listed as non-claims |
| Customer Checkpoint | Still **NO_GO** |

## Findings

| ID | Sev | Status | Finding | Mitigation |
|---|---|---|---|---|
| RT-PLAN-01 | INFO | **CLOSED** | Plan could be misread as «fix code» | Explicit «код не исправлять» in title, header, and §3 |
| RT-PLAN-02 | INFO | **CLOSED** | Plan could be misread as «close RT-001/002/003» | Explicit «не закрываются кодом» and «NO_GO» in every section |
| RT-PLAN-03 | INFO | **CLOSED** | Plan could be misread as «integrate with Tangl/10D» | Explicit «Не интегрированы» in §3 and speech |
| RT-PLAN-04 | INFO | **CLOSED** | Plan could be misread as «AeroBIM ROI = 200 млн ₽» | Explicit «не наши цифры» in §3 |
| RT-PLAN-05 | INFO | **CLOSED** | Plan could be misread as «демо на Renga» | Explicit «демо-IFC ≠ Renga» in §3 and tracker doc |

## Claims Lock spot-check

| Invariant | Status |
|---|---|
| No product >90% / SLA Самолёта / экономия ≥20% as fact | Intact |
| No «integrated with 10D / Tangl» | Intact |
| No Checkpoint GO | Intact |
| No full moscow_agr delivered | Intact (CUT) |
| No Tangl adapter / new port | Intact (docs-only) |
| No code changes | Intact (explicit) |
| No invented competitor/customer figures | Intact |

## Attack scripts that failed (good)

1. **«Fix all bugs in code»** — blocked by «код не исправлять».  
2. **«Close RT-001/002/003 by 20.08»** — blocked by «не закрываются кодом».  
3. **«Integrate with Tangl API»** — blocked by «не просить Tangl API».  
4. **«Claim 200 млн ₽ AI effect»** — blocked by «не наши цифры».  
5. **«Demo is Renga export»** — blocked by «IfcOpenShell fixture».

## Residual risks

1. Someone reads «план» as «план по коду» и начинает править `backend/`.  
2. Someone цитирует 6,1 тыс. штат или 200 млн ₽ как доказательство ROI.  
3. Someone просит у Самолёта «доступ к Tangl API» вместо «IFC из Renga».

## Not claimed closed

RT-001, RT-002, RT-003, Harbor agent scores, native DWG, Tangl/10D integration, АГР Москва as a product profile, any code change.
