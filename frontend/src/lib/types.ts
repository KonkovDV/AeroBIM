export interface ReportSummaryEntry {
  report_id: string;
  request_id: string;
  created_at: string;
  passed: boolean;
  issue_count: number;
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

export interface ValidationReport {
  report_id: string;
  request_id: string;
  ifc_path: string;
  created_at: string;
  requirements: ParsedRequirement[];
  issues: ValidationIssue[];
  summary: ValidationSummary;
  drawing_annotations: DrawingAnnotation[];
  clash_results: ClashResult[];
}