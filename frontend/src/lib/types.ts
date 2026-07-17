export interface ReportSummaryEntry {
  report_id: string;
  request_id: string;
  created_at: string;
  passed: boolean;
  issue_count: number;
  project_name?: string | null;
  discipline?: string | null;
}

export interface ReportListResponse {
  reports: ReportSummaryEntry[];
  count: number;
}

export interface ProblemZone {
  sheet_id: string | null;
  page_number: number | null;
  x: number | null;
  y: number | null;
  width: number | null;
  height: number | null;
  element_guid: string | null;
}

export interface ParsedRequirement {
  rule_id: string;
  ifc_entity: string | null;
  rule_scope: string;
  target_ref: string | null;
  property_set: string | null;
  property_name: string | null;
  operator: string;
  expected_value: string | null;
  unit: string | null;
  source: string;
  source_kind: string;
  evidence_text: string | null;
  instructions: string | null;
  evidence_modality: string | null;
}

export interface ValidationIssue {
  rule_id: string;
  severity: "info" | "warning" | "error";
  message: string;
  ifc_entity: string | null;
  category: string;
  target_ref: string | null;
  property_set: string | null;
  property_name: string | null;
  operator: string | null;
  expected_value: string | null;
  observed_value: string | null;
  unit: string | null;
  element_guid: string | null;
  problem_zone: ProblemZone | null;
  remark: {
    title: string;
    body: string;
  } | null;
  conflict_kind?: string | null;
  priority?: number;
  rase_elements?: string[];
  rase_summary?: string | null;
}

export interface DrawingAnnotation {
  annotation_id: string;
  sheet_id: string;
  target_ref: string;
  measure_name: string;
  observed_value: string;
  unit: string | null;
  problem_zone: ProblemZone | null;
  source: string;
}

export interface DrawingAsset {
  asset_id: string;
  sheet_id: string;
  page_number: number | null;
  media_type: string;
  coordinate_width: number | null;
  coordinate_height: number | null;
  stored_filename: string | null;
}

export interface ClashResult {
  element_a_guid: string;
  element_b_guid: string;
  clash_type: string;
  distance: number;
  description: string;
}

export interface ValidationSummary {
  requirement_count: number;
  issue_count: number;
  error_count: number;
  warning_count: number;
  passed: boolean;
  drawing_annotation_count: number;
  generated_remark_count: number;
}

export type DocStatus = "WIP" | "Shared" | "Published" | "Archived";

export type CapabilityState =
  | "ok"
  | "skipped"
  | "failed"
  | "missing"
  | "not_verified"
  | "not_implemented";

export interface CapabilityStatus {
  status: CapabilityState;
  reason?: string | null;
}

export interface ReportCapabilities {
  clash: CapabilityStatus;
  ids: CapabilityStatus;
  ifc_validation: CapabilityStatus;
  unit_scale: CapabilityStatus;
  raster: CapabilityStatus;
  ifc_schema: CapabilityStatus;
  norm_rule_packs?: CapabilityStatus;
  section_pairing?: CapabilityStatus;
  dwg_dxf?: CapabilityStatus;
  cv_human_level?: CapabilityStatus;
  mep_system_clash?: CapabilityStatus;
  calculation_match?: CapabilityStatus;
  calculation_correctness?: CapabilityStatus;
}

export interface DivergenceRecord {
  finding_key: string;
  engine_verdict: string;
  advisory_verdict: string;
  resolution?: "engine_wins";
}

export interface DrawingRegionRef {
  sheet_id: string;
  bbox_xyxy: [number, number, number, number];
  confidence: number;
  modality: string;
  hitl_required?: boolean;
  hitl_reason?: string | null;
}

export interface IdsCompileDraft {
  suggested_ids_xml: string;
  rationale: string;
  source_requirement_count: number;
  advisory_only?: boolean;
  confidence?: number;
  rase_elements?: string[];
  rase_summary?: string | null;
}

export interface ValidationReport {
  report_id: string;
  request_id: string;
  created_at: string;
  project_name?: string | null;
  discipline?: string | null;
  stage?: string | null;
  information_container_id?: string | null;
  revision?: string | null;
  doc_status?: DocStatus | null;
  requirements: ParsedRequirement[];
  issues: ValidationIssue[];
  summary: ValidationSummary;
  drawing_annotations: DrawingAnnotation[];
  drawing_assets: DrawingAsset[];
  clash_results: ClashResult[];
  capabilities?: ReportCapabilities | null;
  divergences?: DivergenceRecord[];
  drawing_regions?: DrawingRegionRef[];
  advisory_ids_draft?: IdsCompileDraft | null;
}
