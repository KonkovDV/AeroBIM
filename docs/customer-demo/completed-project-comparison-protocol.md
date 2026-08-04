# Completed-project comparison protocol (customer demo)

**Status:** Sprint 2 active draft  
**Meeting date:** `DATE_TO_BE_CONFIRMED`  
**Claim level:** demo protocol only — not product accuracy evidence  
**Checkpoint:** NO_GO until customer adjudication corpus exists

## Purpose

Compare AeroBIM findings against an expert / examination issue register on a **completed** project package (NDA), on two axes required by the tracker:

1. **Finding counts** — ours vs register vs intersection  
2. **Criticality** — agreement on the intersection after severity mapping

## Required customer inputs

- IFC / PDF / ТЗ / calculations as released  
- Final examination conclusion **or** internal issue register  
- Revision identifiers  

Hashes recorded before analysis.

## Finding identity

| Term | Definition |
|---|---|
| finding identity | (rule_family, primary_evidence_ref, object_guid_or_doc_locus, normalized_title) |
| matched | In register **and** AeroBIM (after identity + severity mapping) |
| customer-only | Register only (FN vs expert register) |
| AI-only | AeroBIM only — **see three categories below** |

## Three categories for AI-only (mandatory)

AI-only is **not** automatically a system error. Customer expert assigns one of:

| Category | Meaning |
|---|---|
| `false_positive` | Not a real issue |
| `non_essential` | Real but correctly omitted from the formal conclusion |
| `expert_miss` | Real issue missed by the register — strongest pilot argument |

**Without this adjudication, comparison numbers are not published.**

## Severity scale (propose, then agree)

AeroBIM default: CRITICAL / WARNING / INFO — see [`severity-taxonomy-draft.md`](severity-taxonomy-draft.md).  
Map customer labels via an agreed table before scoring criticality agreement. Scale mismatch is a common false “poor compare”.

## Comparison table (fill after adjudication only)

| Category | Customer | AeroBIM | Matched | AI-only (adj.) | Customer-only | Agreement |
|---|---:|---:|---:|---:|---:|---:|
| Total | | | | | | |
| Critical | | | | | | |
| Warning | | | | | | |
| Info | | | | | | |

AI-only column may be split into FP / non_essential / expert_miss in the annex.

## Demo flow

1. Package composition + hashes  
2. Show customer register / conclusion  
3. Intake completeness + deterministic run  
4. Coverage map + evidence-linked findings  
5. Match  
6. **Adjudicate AI-only into three categories** (customer expert)  
7. Severity mapping agreement  
8. Wall-clock / p95 (no fixture SLA claims)  
9. Export HTML/JSON/BCF  

## Hard rules

- No synthetic findings as project defects  
- No «точность >90%» / product % from open benches  
- LLM must not flip `summary.passed`  
- PII-гейт / closed contour unchanged  
- RT-001/002/003 stay open until customer evidence closes them  

## Evidence class

`CUSTOMER_ONLY` for published agreement metrics. Until adjudication, this file is process design only (`AUTHOR_CLAIM`).
