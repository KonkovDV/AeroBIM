import type { CapabilityState, ReportCapabilities } from "./types";

export const CAPABILITY_ORDER: Array<keyof ReportCapabilities> = [
  "ifc_schema",
  "ifc_validation",
  "ids",
  "unit_scale",
  "clash",
  "norm_rule_packs",
  "section_pairing",
  "raster",
  "dwg_dxf",
  "cv_human_level",
  "mep_system_clash",
  "calculation_match",
  "calculation_correctness",
  "package_completeness",
  "llm_advisory",
  "extraction_integrity",
  "qualified_signature",
];

export const BLOCKING_STATES: ReadonlySet<CapabilityState> = new Set(["failed", "missing"]);

const LABEL_RU: Record<string, string> = {
  ifc_schema: "схема IFC",
  ifc_validation: "валидация IFC",
  ids: "IDS",
  unit_scale: "единицы",
  clash: "коллизии",
  norm_rule_packs: "нормативные пакеты",
  section_pairing: "пары ПД/РД",
  raster: "растр чертежей",
  dwg_dxf: "DWG",
  cv_human_level: "CV human-level",
  mep_system_clash: "MEP-коллизии",
  calculation_match: "сравнение расчётов",
  calculation_correctness: "пересчёт расчётов",
  package_completeness: "комплектность",
  llm_advisory: "советующий ИИ",
  extraction_integrity: "целостность извлечения",
  qualified_signature: "квалифицированная подпись",
};

export type CapabilityRow = {
  key: string;
  status: CapabilityState;
  reason?: string | null;
};

export function capabilityRows(capabilities: ReportCapabilities): CapabilityRow[] {
  return CAPABILITY_ORDER.flatMap((key) => {
    const entry = capabilities[key];
    if (!entry) return [];
    return [{ key, ...entry }];
  });
}

export function formatCapabilityLabel(key: string): string {
  return LABEL_RU[key] ?? key.replaceAll("_", " ");
}

export function humanCapabilityLine(row: CapabilityRow): string {
  const label = formatCapabilityLabel(row.key);
  if (row.status === "skipped" || row.status === "not_verified" || row.status === "not_implemented") {
    return `Проверка «${label}» пропущена (${row.status}) → тишина ≠ успех`;
  }
  if (BLOCKING_STATES.has(row.status)) {
    return `Проверка «${label}» = ${row.status} → summary.passed на сервере не зелёный из-за тишины`;
  }
  return `Проверка «${label}» = ${row.status}`;
}
