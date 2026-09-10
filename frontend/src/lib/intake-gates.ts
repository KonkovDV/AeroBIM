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

const LABEL_RU: Record<IntakeGateKey, string> = {
  nda_signed: "NDA подписан",
  scope_memo_signed: "меморандум о скоупе подписан",
  customer_package_in_samples_customer: "пакет заказчика в рабочей выборке",
  customer_approved_norm_pack_with_approval_ref: "профиль приёмки с ссылкой на согласование (RT-002)",
  ids_or_property_table_present: "IDS или таблица свойств присутствует",
  dual_human_adjudicators_named: "два независимых эксперта названы (RT-001)",
  cohens_kappa_or_krippendorff_alpha_reported: "согласованность меток посчитана",
  confusion_matrix_reported: "матрица ошибок опубликована",
  zero_unresolved_labels: "нет нерешённых меток",
  precision_claim_publishable: "заявка на точность публикуема",
  cde_bcf_import_evidence: "импорт замечаний в среду заказчика доказан",
  customer_sla_pack_measured: "срок обработки измерен на пакете заказчика",
  mep_federated_scope: "федеративные инженерные сети в скоупе (RT-003)",
};

export function intakeGateLabel(key: string): string {
  return LABEL_RU[key as IntakeGateKey] ?? key;
}

export function isIntakeGateTrue(trueGates: readonly string[], key: string): boolean {
  return trueGates.includes(key);
}
