/** Eight-screen IA. SSOT of status: aerobim.domain.ui_expert_workplace_triage.SCREEN_ROWS */

export type TzUiScreenGit = "partial" | "missing";

export type TzUiScreen = {
  id: string;
  titleRu: string;
  git: TzUiScreenGit;
  note: string;
};

export const TZ_UI_SCREENS: TzUiScreen[] = [
  {
    id: "SCR-PROJECTS",
    titleRu: "Проекты и комплекты",
    git: "partial",
    note: "Persisted report list, not a pack workspace with last-run verdict owner",
  },
  {
    id: "SCR-UPLOAD",
    titleRu: "Загрузка комплекта",
    git: "partial",
    note: "POST /v1/uploads dropzone + progress; natives fail-closed in copy",
  },
  {
    id: "SCR-RUN",
    titleRu: "Прогон анализа",
    git: "partial",
    note: "jobs/{job_id} poll; coarse stages; SSE not shipped; 30 min is TZ goal",
  },
  {
    id: "SCR-EXPERT",
    titleRu: "Рабочее место эксперта",
    git: "partial",
    note: "Resizable three panels; keyboard J/K/A/R/E; windowed list above 40 findings",
  },
  {
    id: "SCR-REMARK",
    titleRu: "Карточка замечания",
    git: "partial",
    note: "HITL remark + review-events history; storey/axis or «нет в индексе»",
  },
  {
    id: "SCR-EXPORT",
    titleRu: "Отчёт и экспорт",
    git: "partial",
    note: "HTML JSON BCF 2.1/3.0 PDF; XLSX not an API; do not ship a fake 200",
  },
  {
    id: "SCR-DIFF",
    titleRu: "Сравнение версий комплекта",
    git: "partial",
    note: "HTTP finding delta; no_longer_reported does not claim resolved",
  },
  {
    id: "SCR-USER",
    titleRu: "Дашборд роли «Пользователь»",
    git: "partial",
    note: "review-kpi API exists; TZ-coverage screen this pass; OIDC BFF stays 501",
  },
];
