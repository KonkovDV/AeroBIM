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
  ifc_validation: "проверка IFC",
  ids: "IDS",
  unit_scale: "единицы",
  clash: "коллизии",
  norm_rule_packs: "нормативные пакеты",
  section_pairing: "сшивка ПД/РД",
  raster: "растр чертежа",
  dwg_dxf: "DWG",
  cv_human_level: "CV на уровне человека",
  mep_system_clash: "коллизии MEP",
  calculation_match: "сверка расчёта",
  calculation_correctness: "пересчёт расчёта",
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

const STATUS_RU: Record<CapabilityState, string> = {
  ok: "выполнена",
  skipped: "пропущена",
  failed: "не выполнена",
  missing: "отсутствует",
  not_verified: "не проверена",
  not_implemented: "не реализована",
};

export function formatCapabilityState(status: CapabilityState): string {
  return STATUS_RU[status];
}

export function capabilityStatusPhrase(row: CapabilityRow): string {
  return `${formatCapabilityLabel(row.key)}: ${formatCapabilityState(row.status)}`;
}

export function humanCapabilityLine(row: CapabilityRow): string {
  if (row.key === "mep_system_clash" && row.status !== "ok") {
    return "Проверка коллизий инженерных сетей не выполнена (сети в IFC не переданы) → тишина ≠ успех";
  }
  const label = formatCapabilityLabel(row.key);
  if (row.status === "ok") {
    return `Проверка «${label}» выполнена`;
  }
  if (BLOCKING_STATES.has(row.status)) {
    return `Проверка «${label}» не выполнена → вердикт отрицательный; UI не пишет summary.passed`;
  }
  return `Проверка «${label}» не выполнена → тишина ≠ успех`;
}

export const RUN_ENGINE_GROUPS: Array<{
  id: string;
  title: string;
  keys: Array<keyof ReportCapabilities>;
}> = [
  { id: "model", title: "модель", keys: ["ifc_schema", "ifc_validation", "unit_scale"] },
  { id: "rules", title: "правила", keys: ["ids", "norm_rule_packs", "clash"] },
  { id: "docs", title: "документы", keys: ["raster", "section_pairing", "calculation_match"] },
  { id: "report", title: "отчёт", keys: ["package_completeness", "extraction_integrity"] },
];

const ENGINE_RANK: Record<CapabilityState, number> = {
  failed: 50,
  missing: 40,
  not_implemented: 30,
  not_verified: 25,
  skipped: 20,
  ok: 10,
};

export type EngineGroupStatus = CapabilityState | "pending";

export function formatEngineGroupStatus(status: EngineGroupStatus): string {
  if (status === "pending") {
    return "ожидание";
  }
  return formatCapabilityState(status);
}

export function engineGroupStatus(
  capabilities: ReportCapabilities | null | undefined,
  keys: ReadonlyArray<keyof ReportCapabilities>,
): EngineGroupStatus {
  if (!capabilities) {
    return "pending";
  }
  let worst: CapabilityState | null = null;
  let worstRank = -1;
  for (const key of keys) {
    const entry = capabilities[key];
    if (!entry) {
      continue;
    }
    const rank = ENGINE_RANK[entry.status] ?? 0;
    if (rank > worstRank) {
      worst = entry.status;
      worstRank = rank;
    }
  }
  return worst ?? "pending";
}
