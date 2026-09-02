/** Keys must stay aligned with aerobim.domain.intake_gate_keys.INTAKE_GATE_KEYS */

export const INTAKE_GATE_KEYS = [
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
] as const;

export type IntakeGateKey = (typeof INTAKE_GATE_KEYS)[number];

const LABEL_EN: Record<IntakeGateKey, string> = {
  nda_signed: "NDA signed",
  scope_memo_signed: "scope memo signed",
  customer_package_in_samples_customer: "customer pack in samples/customer (git)",
  customer_approved_norm_pack_with_approval_ref: "acceptance profile with approval_ref (RT-002)",
  ids_or_property_table_present: "IDS or property table present",
  dual_human_adjudicators_named: "two human adjudicators (RT-001)",
  cohens_kappa_or_krippendorff_alpha_reported: "κ/α on labels",
  confusion_matrix_reported: "confusion matrix reported",
  zero_unresolved_labels: "no unresolved labels",
  precision_claim_publishable: "PrecisionClaim.publishable",
  cde_bcf_import_evidence: "BCF import into the CDE evidenced",
  customer_sla_pack_measured: "SLA measured on a customer pack",
  mep_federated_scope: "federated MEP in scope (RT-003)",
};

export function intakeGateLabel(key: string): string {
  return LABEL_EN[key as IntakeGateKey] ?? key;
}

export function isIntakeGateTrue(trueGates: readonly string[], key: string): boolean {
  return trueGates.includes(key);
}
