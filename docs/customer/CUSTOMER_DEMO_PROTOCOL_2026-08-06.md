<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# Customer demo protocol — 2026-08-06

**Status:** Sprint 2 dated canonical  
**claim_level:** demo protocol only — not product accuracy evidence  
**Checkpoint:** NO_GO until customer adjudication corpus exists  
**Adapted from:** [`DEMO_PROTOCOL_COMPLETED_PROJECT.md`](DEMO_PROTOCOL_COMPLETED_PROJECT.md)

## Purpose

Compare AeroBIM findings against an expert / examination issue register on a **completed** project package (NDA), on the brief comparison axes:

1. **Finding counts** — ours vs register vs intersection  
2. **Criticality agreement** — on the intersection after severity mapping  
3. **AI-only adjudication** — false_positive / non_essential / expert_miss  
4. **Speed** — wall-clock / p95 on the customer pack (no fixture SLA claims)  
5. **Export handoff** — HTML / JSON / BCF structural (not CDE-ready claim)

## Required customer inputs

- IFC / PDF / ТЗ / calculations as released  
- Final examination conclusion **or** internal issue register  
- Revision identifiers  

Hashes recorded before analysis. **Customer approval required** before any external publication of comparison numbers.

## Finding identity

| Term | Definition |
|---|---|
| finding identity | (rule_family, primary_evidence_ref, object_guid_or_doc_locus, normalized_title) |
| matched | In register **and** AeroBIM (after identity + severity mapping) |
| customer-only | Register only (FN vs expert register) |
| AI-only | AeroBIM only — adjudicate into three categories below |

## Three categories for AI-only (mandatory)

| Category | Meaning |
|---|---|
| `false_positive` | Not a real issue |
| `non_essential` | Real but correctly omitted from the formal conclusion |
| `expert_miss` | Real issue missed by the register — strongest pilot argument |

**Without this adjudication, comparison numbers are not published.**

## Severity scale (proposed — Customer approval required)

| Proposed label | Intent | Map hint (AeroBIM) |
|---|---|---|
| **Critical** | Safety, structural/fire, stop-work, hard unresolvable clash | CRITICAL |
| **Major** | Must correct before release; material rework / schedule risk | WARNING (blocking under profile) |
| **Minor** | Correct before archive; limited impact under stated context | WARNING / INFO |
| **Info** | Data quality, incompleteness, recommendation | INFO |

This taxonomy is **PROPOSED_NOT_CUSTOMER_APPROVED**. Pending customer approval before any pilot narrative uses these labels as authoritative.

| Customer label | Customer definition (quote) | AeroBIM bucket | Notes | Approved by |
|---|---|---|---|---|
| | | Critical / Major / Minor / Info / OUT_OF_SCOPE | | |

## Comparison table (fill after adjudication + approval only)

| Category | Customer | AeroBIM | Matched | AI-only (adj.) | Customer-only | Agreement |
|---|---:|---:|---:|---:|---:|---:|
| Total | | | | | | |
| Critical | | | | | | |
| Major | | | | | | |
| Minor | | | | | | |
| Info | | | | | | |

## Demo flow

1. Package composition + hashes  
2. Show customer register / conclusion  
3. Intake completeness + deterministic run  
4. Coverage map + evidence-linked findings  
5. Match  
6. **Adjudicate AI-only** (customer expert)  
7. Severity mapping agreement (**Customer approval required**)  
8. Wall-clock / p95 (no fixture SLA claims)  
9. Export HTML/JSON/BCF  

## Hard rules

- No synthetic findings as project defects  
- No «точность >90%» / product % from open benches or fixtures  
- LLM must not flip `summary.passed`  
- PII gate / closed contour unchanged  
- RT-001/002/003 stay open until customer evidence closes them  
- **Customer approval required** before publishing any pilot accuracy narrative  
- `customer_precision_claim_publishable=false` until intake gates pass
