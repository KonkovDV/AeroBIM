"""Four-role RASE demo for SP63-COVER-SLAB-001 — template, not customer_approved.

Hjelseth & Nisbet 2011 (CIB W78): https://itc.scix.net/paper/w78-2011-Paper-45
No fabricated DOI. Clause is 8.3 (template), not SP 63 table 8.1.
"""

from __future__ import annotations

from typing import Any

HJELSETH_NISBET_2011 = "Hjelseth & Nisbet 2011, CIB W78 Paper 45"
HJELSETH_NISBET_URL = "https://itc.scix.net/paper/w78-2011-Paper-45"
IDS_1_0_FINAL = "2024-06-01"
SP63_COVER_RULE_ID = "SP63-COVER-SLAB-001"
SP63_COVER_CLAUSE = "8.3 (template)"
REPORT_TRACE_FIELDS = (
    "norm_source",
    "norm_clause",
    "expected_value",
    "observed_value",
    "rase_elements",
)


def rase_four_roles_from_cover_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """Map one synthetic cover rule onto R/A/S/E. Never sets customer_approved."""

    if str(rule.get("rule_id") or "") != SP63_COVER_RULE_ID:
        raise ValueError("demo is bound to SP63-COVER-SLAB-001 only")
    clause = str(rule.get("norm_clause") or "")
    if clause != SP63_COVER_CLAUSE:
        raise ValueError("clause must stay 8.3 (template)")
    approval = str(rule.get("approval_status") or "")
    if approval == "customer_approved":
        raise ValueError("template must not carry customer_approved")
    prop = str(rule.get("property_name") or "")
    pset = str(rule.get("property_set") or "")
    operator = str(rule.get("operator") or "")
    expected = rule.get("expected_value")
    unit = str(rule.get("unit") or "")
    return {
        "rule_id": SP63_COVER_RULE_ID,
        "R": (
            f"{prop} {operator} {expected} {unit}".strip()
            + " — template threshold, not SP 63 table 8.1"
        ),
        "A": str(rule.get("ifc_entity") or ""),
        "S": f"{pset}.{prop}",
        "E": "not stated — template, not exposure class",
        "norm_source": str(rule.get("norm_source") or ""),
        "norm_clause": clause,
        "approval_status": approval,
        "customer_approved": False,
        "citation": HJELSETH_NISBET_2011,
        "citation_url": HJELSETH_NISBET_URL,
        "ids_1_0_final": IDS_1_0_FINAL,
        "report_fields": REPORT_TRACE_FIELDS,
    }


__all__ = [
    "HJELSETH_NISBET_2011",
    "HJELSETH_NISBET_URL",
    "IDS_1_0_FINAL",
    "REPORT_TRACE_FIELDS",
    "SP63_COVER_CLAUSE",
    "SP63_COVER_RULE_ID",
    "rase_four_roles_from_cover_rule",
]
