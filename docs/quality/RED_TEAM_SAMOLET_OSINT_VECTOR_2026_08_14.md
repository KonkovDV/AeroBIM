<!-- claims-lint: allow-file reason="Red Team citing forbidden phrases as non-claims; OSINT secondary figures labeled non-product" -->
---
title: "Red Team — Samolet OSINT + vector pack (2026-08-14)"
status: active
version: "1.0.0"
last_updated: "2026-08-14"
claim_boundary: >
  Internal Red Team of the OSINT/GTM docs pack. Checkpoint remains NO_GO.
  Does not close RT-001/002/003. Not product accuracy. Not 10D/Tangl integration.
---

# Red Team — OSINT + вектор Самолёта

**Author relationship:** Internal self-assessment  
**Scope:** docs/GTM pack of 14.08.2026 (OSINT SSOT, competitive matrix RU rows, intake, jury/tracker speech, regulatory AGR rows, fixture IFC honesty, README speech bounds)  
**Code / architecture:** **unchanged** (freeze: no new ports, adapters, DI)  
**Checkpoint:** **`NO_GO`**

## Verdict

| Lane | Result |
|---|---|
| Application security (Critical/High) | **0** — no runtime change |
| Integrity (Medium) | **0 open** — three honesty gaps found in draft and **closed in the same pack** |
| Claims Lock | **PASS with notes** |
| Customer Checkpoint | Still **NO_GO** |

## Findings

| ID | Sev | Status | Finding | Mitigation |
|---|---|---|---|---|
| RT-OSINT-01 | MED | **MITIGATED** | Tracker/jury said «демо-IFC = Renga», while `samples/ifc/walls-multi-entity.ifc` is IfcOpenShell IFC4 named Samolet Multi Fixture | Explicit non-claim in tracker, FAQ, samples/ifc README, OSINT §3, README |
| RT-OSINT-02 | MED | **MITIGATED** | Temptation to invent а «сейчас в X» or « ушёл из группы» | OSINT people table: next employer **not asserted**; FAQ forbids naming post-exit titles |
| RT-OSINT-03 | MED | **MITIGATED** | Secondary synthesis assigned Tangl Control / Pilot-BIM to ГАЛС without primary page | Matrix + OSINT: ГАЛС = Sarex + Tangl **Value** (tangl.cloud). Control/Pilot-BIM = do not claim |
| RT-OSINT-04 | INFO | OPEN | Headcount 7.6k→6.1k and ~200 млн ₽ AI-effect are **secondary** press on the 2025 annual report / CNews — not for pitch slides without issuer PDF | Labeled `[П]` secondary; OSINT §2 says re-verify before external memo |
| RT-OSINT-05 | INFO | OPEN | ЦИМ АГР / СтроимПросто dates taken from industry write-ups + portal URL, not the DGP PDF in-repo | Regulatory baseline: not legal advice; `moscow_agr` remains CUT |
| RT-OSINT-06 | INFO | OPEN | Champion «Панькин» is from public webinar attribution already in tracker — not a signed sponsor letter | Do not mail-blast; wait for tracker/customer intro |

## Claims Lock spot-check

| Invariant | Status |
|---|---|
| No product >90% / SLA Самолёта / экономия ≥20% as fact | Intact |
| No «integrated with 10D / Tangl» | Intact (explicit non-claim) |
| No Checkpoint GO | Intact |
| No full moscow_agr delivered | Intact (CUT) |
| No Tangl adapter / new port | Intact (docs-only) |
| IFC-Bench 25/1026 not recycled as 514 | Not in this pack |
| Competitor card numbers not adopted as ours | Intact |

## Attack scripts that failed (good)

1. **«Replace Tangl»** — blocked by vector sentence + matrix rule of speech.  
2. **«Sell to Semenov as the 10D successor»** — blocked: champion = IM directorate; IT block = veto.  
3. **«A101 next week»** — blocked: they filter early-stage; second logo after measurable Samolet pilot.  
4. **«StroimProsto is our product»** — blocked: do not replace the city service.  
5. **«Demo is a Samolet Renga model»** — blocked by RT-OSINT-01.

## Residual risks

1. Someone quotes 6.1k headcount or 200 млн ₽ as AeroBIM ROI.  
2. Someone asks Renga for a public IFC and treats PNST 909 Experiment A (18/22) as customer precision.  
3. Tracker repeats «демо на Renga» from the old one-pager sentence without the honesty paragraph.

## Not claimed closed

RT-001, RT-002, RT-003, Harbor agent scores, native DWG, Tangl/10D integration, АГР Москва as a product profile.
