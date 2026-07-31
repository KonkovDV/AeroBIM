# Completed-project comparison protocol (customer demo)

**Status:** draft for Sprint 2.1  
**Meeting date:** `DATE_TO_BE_CONFIRMED`  
**Claim level:** demo protocol only — not product accuracy evidence

## Purpose

Compare AeroBIM findings against an expert / examination issue register on a **completed** project package provided by the customer under NDA, using two mandatory axes:

1. total finding count (after duplicate consolidation)
2. severity / criticality agreement (via **mapping table**, never raw label equality)

## Required customer inputs (when available)

- IFC models (disciplines as released)
- PDF drawings
- technical requirements / ТЗ
- calculation materials
- final examination conclusion (if shareable)
- internal review report / issue register
- revision history

Hashes and revisions are recorded before analysis.

## Finding identity definitions

| Term | Definition |
|---|---|
| finding identity | Stable key over (rule_family, primary_evidence_ref, object_guid_or_doc_locus, normalized_title) |
| duplicate finding | Same identity within one AeroBIM run (or near-duplicate after template normalize) |
| same issue across revisions | Shared identity across revision A/B; status may change |
| severity mapping | Customer severity → AeroBIM CRITICAL/WARNING/INFO via agreed table |
| expert-confirmed finding | Present in customer register **and** matched in AeroBIM |
| AI-only finding | AeroBIM only; not in customer register |
| customer-only finding | Customer register only; not reported by AeroBIM |
| not-verifiable finding | Evidence insufficient for deterministic match |
| out-of-scope finding | Outside declared check coverage / intake completeness |

## Comparison table (fill per demo)

| Category | Customer findings | AeroBIM findings | Matched | AI-only | Customer-only | Agreement |
|---|---:|---:|---:|---:|---:|---:|
| Total | | | | | | |
| Critical | | | | | | |
| Warning | | | | | | |
| Info | | | | | | |

Agreement = matched / (matched + AI-only + customer-only) after mapping. Report separately for raw counts vs mapped severity.

## Demo flow

1. Show completed project composition.
2. Record hashes and revisions.
3. Show examination / issue register (customer).
4. Load package into AeroBIM.
5. Check intake completeness.
6. Run deterministic checks.
7. Show coverage map.
8. Show findings with evidence.
9. Match against customer register.
10. Show disagreements.
11. Show severity mapping.
12. Show time-to-first-finding.
13. Show total wall time.
14. Export HTML/JSON/BCF.
15. Hand disputed cases to expert.

## Hard demo rules

- Do not present synthetic findings as project defects.
- Do not claim customer SLA ≤30 minutes from fixtures.
- Do not claim CDE integration from BCF ZIP alone.
- Do not let LLM advisory change `summary.passed`.
- RT-001/002/003 remain open until customer evidence closes them.

## Evidence class

`CUSTOMER_ONLY` for agreement metrics on real projects. Until then, this protocol is `AUTHOR_CLAIM` process design only.
