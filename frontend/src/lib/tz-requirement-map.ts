/** TZ item → shell function → evidence. Not a delivery claim. */

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
    fn: "Зона сброса файлов",
    evidence: "Нативные RVT, NWD и закрытый DWG отклоняются до отправки",
    git: "partial",
  },
  {
    id: "TZ-RUN",
    tz: "Автоматический анализ; цель ТЗ 30:00 на комплект",
    fn: "Запуск проверки и ожидание результата",
    evidence: "Таймер наблюдения; цель ТЗ 30:00; SLA не заявляем",
    git: "partial",
  },
  {
    id: "TZ-OVERLAY",
    tz: "Разбор чертежей с наложением ошибок",
    fn: "Наложение зоны на лист",
    evidence: "Превью листа из отчёта, не наложение CAD",
    git: "partial",
  },
  {
    id: "TZ-REMARK",
    tz: "Замечание: суть + пункт нормы/СТО + локация",
    fn: "Карточка замечания и история решений",
    evidence: "Пустой пункт остаётся обязательным; этаж и ось или «нет в индексе»",
    git: "partial",
  },
  {
    id: "TZ-ROLES",
    tz: "Эксперт и Пользователь",
    fn: "Режим просмотра и серверный отказ без прав эксперта",
    evidence: "Переключатель шапки не выдаёт права; промышленный вход ещё не подключён",
    git: "partial",
  },
  {
    id: "TZ-EXPORT",
    tz: "Отчёт + импорт/экспорт файлов",
    fn: "HTML, JSON, BCF; PDF — черновик покрытия",
    evidence: "Таблица Excel в этом выпуске не выгружается; коннектора 10D нет",
    git: "partial",
  },
  {
    id: "TZ-DIFF",
    tz: "Сравнение версий документации",
    fn: "Сравнение двух сохранённых отчётов",
    evidence: "новые / не воспроизведено / остались; «не воспроизведено» ≠ исправлено",
    git: "partial",
  },
  {
    id: "TZ-BLOCKERS",
    tz: "Честная рамка приёмки",
    fn: "Снимок условий приёмки",
    evidence: "RT-001, RT-002 и RT-003 остаются открытыми; оболочка гейты не переключает",
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
