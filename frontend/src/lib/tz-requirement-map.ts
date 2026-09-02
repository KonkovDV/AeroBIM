/** TZ item → shell function → git evidence. Not a delivery claim. */

import type { WorkspaceView } from "../components/WorkspaceNav";

export type TzRequirementRow = {
  id: string;
  tz: string;
  fn: string;
  evidence: string;
  git: "partial" | "missing";
};

export const TZ_REQUIREMENT_ROWS: TzRequirementRow[] = [
  {
    id: "TZ-UPLOAD",
    tz: "Upload Office / PDF / IFC; TZ lists more than IFC for models",
    fn: "Dropzone + POST /v1/uploads",
    evidence: "PackUploadPanel; RVT/NWD/closed DWG fail-closed before POST",
    git: "partial",
  },
  {
    id: "TZ-RUN",
    tz: "Automatic analysis; TZ 30:00 goal per pack",
    fn: "POST submit + poll jobs/{job_id}",
    evidence: "AnalyzeRunPanel elapsed MM:SS; TZ goal 30:00; not SLA; SSE not shipped",
    git: "partial",
  },
  {
    id: "TZ-OVERLAY",
    tz: "Drawing review with error overlay",
    fn: "DrawingEvidencePanel bbox overlay",
    evidence: "Raster/PDF preview; not CAD overlay; web-ifc is fixture viewer",
    git: "partial",
  },
  {
    id: "TZ-REMARK",
    tz: "Remark: essence + code/STO clause + location",
    fn: "RemarkCardPanel + review-events",
    evidence: "Empty clause → обязательное поле ТЗ; storey/axis or «нет в индексе»",
    git: "partial",
  },
  {
    id: "TZ-ROLES",
    tz: "Expert and User",
    fn: "Макет экрана + серверный HITL 403",
    evidence: "RoleHonestyBanner; GET /v1/auth/bff stays 501; not OIDC",
    git: "partial",
  },
  {
    id: "TZ-EXPORT",
    tz: "Report + file import/export",
    fn: "HTML JSON BCF 2.1/3.0; PDF черновик покрытия",
    evidence: "XLSX button disabled; no 10D/Tangl connector",
    git: "partial",
  },
  {
    id: "TZ-DIFF",
    tz: "Compare documentation versions",
    fn: "GET revision-diff",
    evidence: "newly / no_longer / still; no_longer_reported ≠ исправлено",
    git: "partial",
  },
  {
    id: "TZ-BLOCKERS",
    tz: "Honest acceptance frame",
    fn: "GET /v1/system/capabilities intake snapshot",
    evidence: "RT-001/002/003 stay OPEN; UI does not flip gates",
    git: "partial",
  },
];

export function tzRequirementView(id: string): WorkspaceView | null {
  switch (id) {
    case "TZ-UPLOAD":
      return "upload";
    case "TZ-RUN":
      return "run";
    case "TZ-OVERLAY":
      return "review";
    case "TZ-REMARK":
      return "remark";
    case "TZ-ROLES":
      return "user";
    case "TZ-EXPORT":
      return "export";
    case "TZ-DIFF":
      return "diff";
    case "TZ-BLOCKERS":
      return "user";
    default:
      return null;
  }
}
