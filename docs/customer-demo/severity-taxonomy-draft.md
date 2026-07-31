# Severity taxonomy draft (customer demo)

**Status:** `PROPOSED_NOT_CUSTOMER_APPROVED`  
**Sprint:** 2.1  
**Rule:** Never compare customer severity and AeroBIM severity without a mapping table.

## Process

1. Ask the customer for their severity / criticality criteria first.
2. If provided, build a mapping table (customer label → AeroBIM bucket).
3. If not provided, use the draft below **only as a proposal**.

## Draft taxonomy (proposal)

### CRITICAL

Affects safety, structural capacity, fire safety, unresolvable hard clash, material rework risk, or stop-work risk.

### WARNING

Requires correction but does not create immediate critical risk under the stated project context.

### INFO

Incompleteness, data quality, format defect, or recommendation without proven safety / cost / schedule impact.

## Mapping table template

| Customer label | Customer definition (quote) | AeroBIM bucket | Notes | Approved by |
|---|---|---|---|---|
| | | CRITICAL / WARNING / INFO / OUT_OF_SCOPE | | |

## Claim boundary

- This draft is **not** customer-approved.
- Severity suggestion from LLM is advisory only.
- Deterministic engine + policy remain owners of reported severity on findings.
