<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# Demo protocol — completed project comparison

**Status:** Sprint 2 canonical template  
**claim_level:** demo protocol only — not product accuracy evidence  
**Checkpoint:** NO_GO until customer adjudication corpus exists  
**Adapted from:** [`docs/customer-demo/completed-project-comparison-protocol.md`](../customer-demo/completed-project-comparison-protocol.md)

RU materials: [`DEMO_SCENARIO_TRACKER_RU_2026_08.md`](../customer-demo/DEMO_SCENARIO_TRACKER_RU_2026_08.md), discovery pack under [`docs/customer-discovery/`](../customer-discovery/).

## Purpose

Compare AeroBIM findings against an expert / examination issue register on a **completed** project package (NDA), on:

1. **Finding counts** — ours vs register vs intersection  
2. **Criticality** — agreement on the intersection after severity mapping

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

Propose four buckets for customer discussion (map to AeroBIM CRITICAL / WARNING / INFO):

| Proposed label | Intent |
|---|---|
| **Critical** | Safety, structural/fire, stop-work, hard unresolvable clash |
| **Major** | Must correct before release; material rework / schedule risk |
| **Minor** | Correct before archive; limited impact under stated context |
| **Info** | Data quality, incompleteness, recommendation |

This taxonomy is **PROPOSED_NOT_CUSTOMER_APPROVED**. See also [`severity-taxonomy-draft.md`](../customer-demo/severity-taxonomy-draft.md).

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
