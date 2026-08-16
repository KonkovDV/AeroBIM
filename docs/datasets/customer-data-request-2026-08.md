<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Customer data request — RT-001 expertise corpus"
date: 2026-08-07
status: formal_request
claim_boundary: >-
  Intake specification only. Checkpoint NO_GO. No product accuracy >90%.
  No invented orgs/contacts. Fixture-only public artifacts until GT exists.
---

# Customer data request — RT-001 (August 2026)

**Purpose:** Formal specification for pilot organizations willing to contribute **document ↔ expertise-remark pairs** under NDA. This document closes the gap identified in the [expertise corpus scan](expertise-corpus-scan-2026-08.md): no open corpus can substitute for dual-adjudicated customer ground truth.

**Audience:** Pilot org legal / BIM lead / chief engineer.  
**Related SSOT:** [`OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](../quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md), [`CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md), [`CUSTOMER_DATA_REQUIREMENTS_2026_07_31.md`](../../audit/reports/CUSTOMER_DATA_REQUIREMENTS_2026_07_31.md).

**Checkpoint:** **NO_GO** until this intake is executed with adjudicated labels. Open bench and in-repo fixtures do **not** close RT-001.

---

## 1. What we need (documents)

| Category | Minimum (pilot floor) | Preferred | Purpose |
|---|---|---|---|
| **Completed PD/RD package** | One discipline slice (e.g. AR or KR) | Federated slice + calcs + 2D sheets | Source documents for remark pairing |
| **Prior expertise conclusion or internal QC record** | PDF or structured export with remark list | Machine-readable remark IDs + sheet/element refs | Pairs remark ↔ document element |
| **Reference IFC** | 1 model matching the section | 2 revision snapshots for diff rehearsal | Analyze path today requires IFC |
| **Agreed rule subset** | Property table or IDS draft | Customer-approved norm pack (RT-002 separate) | Not «all GOST» — scoped subset only |
| **Calculation extract** | 1 table cross-checkable to model/drawing | Full calc book for load rows | Consistency check only — not independent correctness |

### Formats (acceptance order)

| Format | Status | Notes |
|---|---|---|
| **IFC** (2x3 / 4 / 4x3 per [`ISO 16739`](https://www.iso.org/standard/70303.html) / buildingSMART) | **Required** on analyze path | Primary model interchange |
| **PDF/A** | **Required** for normative sheet evidence | Per ПП РФ 614; raster/OCR is degrade path |
| **DXF** | **Optional** (customer export) | Parsed via optional `[cad]`; not native DWG |
| **DWG** | **Only if unavoidable** | Native DWG **not supported** today; triggers fail-closed capability; prefer IFC + PDF/A + customer-exported DXF |
| **XML / doc** | Optional | TZ language, acceptance criteria |

**Do not claim:** «DWG-ready», «анализируем DWG», or green pass on mixed DWG+unparsed packages.

---

## 2. Sections and scope

Pilot scope must be **written and signed** before transfer:

| Field | Example values | Gate |
|---|---|---|
| Discipline slice | AR, KR, VK, EO | One slice minimum |
| Building / object ID | Internal project code (de-identified) | No public repo commit |
| Revision baseline | Rev A (expertise input) | Required |
| Optional revision B | Post-fix snapshot | Diff rehearsal only |
| Excluded scopes | MEP federated clash, full-compound SLA | RT-003 / SLA not in scope |

MEP federated IFC + clearance matrix is a **separate RT-003 track** — not delivered in Sprint 3.

---

## 3. Expertise conclusions (what counts as GT)

**Required pair:** each adjudicated finding must link:

1. **Remark text** (from expertise conclusion or internal QC)
2. **Document anchor** (sheet ref, IFC GUID, property path, or calc row)
3. **Severity / category** (customer-defined taxonomy)
4. **TP / FP / FN label** after dual adjudication

**Not acceptable as RT-001 GT:**

| Source | Why |
|---|---|
| `samples/benchmarks/russian-aec-ground-truth.json` | Requirements extraction GT — **≠** expertise conclusions |
| IFC-Bench / buildingSMART IDS | Open bench / IDS regression only |
| Sprint-2 synthetic packs | `claim_level=synthetic_only` |
| Public «типовые замечания» catalogs | Coverage taxonomy only — no document-level TP/FP |

---

## 4. Minimum volume (pilot measurability)

| Metric | Floor | Target | Gate |
|---|---|---|---|
| Adjudicated finding labels (TP/FP/FN) | ≥50 | ≥200 | Wilson CI publishable only above agreed *n* |
| Typical-error patterns with examples | ≥10 | ≥20 | Remark calibration |
| Adjudicating engineers | **2** (independent) | 2 + tie-breaker | Cohen's κ / Krippendorff's α before accuracy claim |
| Manual baseline hours (same package) | 1 measured run | 3 runs median | Time-saved KPI denominator |

Below floor: metrics may be recorded internally but **must not** be published as product precision.

---

## 5. De-identification

| Requirement | Detail |
|---|---|
| **Scope memo** | List what is removed vs masked vs retained |
| **Masking ≠ anonymization** | Hybrid contour not wired to verdict; document honestly |
| **No public redistribution** | Customer IFC/PDF/conclusions stay out of public git |
| **Fixture extraction** | Only synthetic or heavily redacted snippets with written permission |
| **Project identifiers** | Replace with `PILOT_ORG_n` / internal codes in shared artifacts |
| **Personal data** | Strip names, phones, addresses from sheets unless required for anchor |

Re-identification risk must be assessed before any cloud LLM on customer files (written permission required).

---

## 6. Labeling format (dual adjudication)

**Protocol:**

1. Two qualified engineers label each finding independently.
2. Use repo templates:
   - [`samples/benchmarks/annotation/iaa-worksheet-template.json`](../../samples/benchmarks/annotation/iaa-worksheet-template.json)
   - [`samples/benchmarks/detection-precision/labels-template.json`](../../samples/benchmarks/detection-precision/labels-template.json)
3. Record `adjudication.method`, annotator IDs (pseudonymized), and timestamp in sidecar JSON.
4. **Forbidden:** single-annotator labels presented as product accuracy.

**Sidecar fields (minimum):**

```json
{
  "finding_id": "F-001",
  "remark_text": "...",
  "document_anchor": {"sheet": "AR-01", "ifc_guid": "..."},
  "a1_label": "TP",
  "a2_label": "TP",
  "consensus_label": "TP",
  "adjudication_method": "dual_independent",
  "disagreement_resolved_by": "tie_breaker_id_or_consensus_meeting"
}
```

---

## 7. Disagreement resolution

| Step | Action |
|---|---|
| 1 | Flag pairs where `a1_label ≠ a2_label` |
| 2 | Third qualified engineer (tie-breaker) or consensus meeting |
| 3 | Record resolution rationale (1–3 sentences) |
| 4 | Compute κ / α on pre-consensus labels for protocol quality |
| 5 | Publish metrics only on **consensus** labels |

Unresolved disagreements are excluded from precision denominator and counted separately.

---

## 8. Storage, transfer, and NDA

| Requirement | Rationale |
|---|---|
| Signed NDA before file transfer off customer premises | Claims Lock + pilot threat model |
| On-prem option for expertise orgs | Files need not leave customer network for first demo |
| No redistribution of customer IFC/PDF in public repo | Fixture-only public artifacts |
| Written permission before cloud LLM | PII / residency — not assumed |
| Retention / deletion schedule | Document in scope memo |
| Access log | Who copied what, when |

CDE/BCF test tenant answers are tracked separately ([`cde-integration-questionnaire-2026.md`](../cde-integration-questionnaire-2026.md)) — **BCF ZIP structural OK ≠ CDE-ready**.

---

## 9. Corpus fitness criteria (accept / reject)

| Criterion | Accept | Reject |
|---|---|---|
| Remark ↔ document pairs | ≥ floor with anchors | Remark list only, no anchors |
| Dual adjudication | 2 independent labelers | Single labeler |
| Format mix | IFC + PDF/A present | DWG-only package without export path |
| Scope | Signed discipline slice | «Whole compound» without boundary |
| Norm pack | Draft subset identified | «All GOST» unspecified |
| License to use | NDA + purpose-limited | Verbal OK only |
| Re-identification risk | Assessed | Unknown PII on sheets |

Rejected packs may still inform discovery — not RT-001 closure.

---

## 10. What NOT to claim until GT exists

| Forbidden until customer GT + adjudication | Allowed meanwhile |
|---|---|
| Product accuracy / «точность >90%» | Open-bench scores with `claim_level=open_bench_only` |
| «Подтверждено на реальных проектах заказчика» | «Fixture regression n=7» / «BSI n=290» |
| Customer SLA (комплект ≤30 мин) | Fixture SLA schema with `claim_level=fixture_only` |
| Expertise-conclusion automation rate | Exp B coverage % with AUTHOR_CLAIM caveat |
| RT-001 / Checkpoint GO | Checkpoint **NO_GO** |
| Closing RT-002 from draft/template packs | Draft norm advisory only |
| RT-003 MEP federated clash as delivered | ENG_PARTIAL scaffold, `geometry_verified=False` |
| «LLM beats regex on customer packs» | Fixture regex baseline only ([`kimi-vs-qwen-2026-08.md`](../evidence/kimi-vs-qwen-2026-08.md)) |
| «CDE-ready BCF» | BCF ZIP structurally OK; CDE import **NOT PROVEN** |

---

## 11. Intake workflow

1. **Discovery call** — qualify DWG/IFC/PDF mix, expertise conclusion availability ([`../gtm/COMMERCIAL_AND_OPEN_CORE_2026_08_14.md`](../gtm/COMMERCIAL_AND_OPEN_CORE_2026_08_14.md)).
2. **NDA** — signed before transfer.
3. **Scope memo** — discipline, formats, de-ID rules, excluded claims.
4. **Transfer** — on-prem preferred; encrypted channel if remote.
5. **Dual labeling** — templates + disagreement resolution.
6. **Metrics gate** — κ / α + Wilson CI before any publishable precision.
7. **Checkpoint review** — RT-001 remains **NO_GO** until steps 5–6 pass.

---

## References

- [Expertise corpus scan — August 2026](expertise-corpus-scan-2026-08.md) — source checklist expanded here
- [`adjudication-corpus-plan-latest.json`](../evidence/adjudication-corpus-plan-latest.json)
- [`pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)
- [`dwg-blocker-memo-2026-08.md`](../dwg-blocker-memo-2026-08.md)
