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
    tz: "Загрузка Office / PDF / IFC; ТЗ перечисляет для моделей больше, чем IFC",
    fn: "Зона сброса + POST /v1/uploads",
    evidence: "PackUploadPanel; RVT/NWD/закрытый DWG — жёсткий отказ до POST",
    git: "partial",
  },
  {
    id: "TZ-RUN",
    tz: "Автоматический анализ; цель ТЗ 30:00 на комплект",
    fn: "POST-заявка + опрос jobs/{job_id}",
    evidence: "AnalyzeRunPanel: таймер ММ:СС; цель ТЗ 30:00; не SLA; SSE не поставлен",
    git: "partial",
  },
  {
    id: "TZ-OVERLAY",
    tz: "Разбор чертежей с наложением ошибок",
    fn: "DrawingEvidencePanel: наложение bbox",
    evidence: "Превью растра/PDF; не CAD-наложение; web-ifc — вьюер фикстуры",
    git: "partial",
  },
  {
    id: "TZ-REMARK",
    tz: "Замечание: суть + пункт нормы/СТО + локация",
    fn: "RemarkCardPanel + review-events",
    evidence: "Пустой пункт → обязательное поле ТЗ; этаж/ось или «нет в индексе»",
    git: "partial",
  },
  {
    id: "TZ-ROLES",
    tz: "Эксперт и Пользователь",
    fn: "Макет экрана + серверный HITL 403",
    evidence: "RoleHonestyBanner; GET /v1/auth/bff по умолчанию 501, LAB не SSO",
    git: "partial",
  },
  {
    id: "TZ-EXPORT",
    tz: "Отчёт + импорт/экспорт файлов",
    fn: "HTML JSON BCF 2.1/3.0; PDF — черновик покрытия",
    evidence: "XLSX вне MVP и не рендерится; коннектора 10D/Tangl нет",
    git: "partial",
  },
  {
    id: "TZ-DIFF",
    tz: "Сравнение версий документации",
    fn: "GET revision-diff",
    evidence: "новые / не воспроизведено / остались; «не воспроизведено» ≠ исправлено",
    git: "partial",
  },
  {
    id: "TZ-BLOCKERS",
    tz: "Честная рамка приёмки",
    fn: "GET /v1/system/capabilities: снимок приёмки",
    evidence: "RT-001/002/003 остаются ОТКРЫТЫ; UI гейты не переключает",
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
