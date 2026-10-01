"""Canonical intake-gate key names. Domain-owned so KT#3 packing does not import application."""

from __future__ import annotations

INTAKE_GATE_KEYS = (
    "nda_signed",
    "scope_memo_signed",
    "customer_package_in_samples_customer",
    "customer_approved_norm_pack_with_approval_ref",
    "ids_or_property_table_present",
    "dual_human_adjudicators_named",
    "cohens_kappa_or_krippendorff_alpha_reported",
    "confusion_matrix_reported",
    "zero_unresolved_labels",
    "precision_claim_publishable",
    "cde_bcf_import_evidence",
    "customer_sla_pack_measured",
    "mep_federated_scope",
)

__all__ = ["INTAKE_GATE_KEYS"]
