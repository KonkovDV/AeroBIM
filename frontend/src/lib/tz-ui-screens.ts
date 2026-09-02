/** Eight-screen IA. SSOT of status: aerobim.domain.ui_expert_workplace_triage.SCREEN_ROWS */

export type TzUiScreenGit = "partial" | "missing";

export type TzUiScreen = {
  id: string;
  title: string;
  git: TzUiScreenGit;
  note: string;
};

export const TZ_UI_SCREENS: TzUiScreen[] = [
  {
    id: "SCR-PROJECTS",
    title: "Проекты и комплекты",
    git: "partial",
    note: "Persisted report list; picking a pack opens the expert three-pane",
  },
  {
    id: "SCR-UPLOAD",
    title: "Загрузка комплекта",
    git: "partial",
    note: "POST /v1/uploads dropzone + progress + cancel; natives fail-closed in copy",
  },
  {
    id: "SCR-RUN",
    title: "Прогон анализа",
    git: "partial",
    note: "jobs/{job_id} poll; engine groups from capabilities; SSE not shipped",
  },
  {
    id: "SCR-EXPERT",
    title: "Рабочее место эксперта",
    git: "partial",
    note: "TZ three-pane: findings | 2D/3D | remark; report index is SCR-PROJECTS",
  },
  {
    id: "SCR-REMARK",
    title: "Карточка замечания",
    git: "partial",
    note: "HITL remark + review-events history; storey/axis or «нет в индексе»",
  },
  {
    id: "SCR-EXPORT",
    title: "Отчёт и экспорт",
    git: "partial",
    note: "HTML JSON BCF 2.1/3.0; PDF = coverage draft; XLSX not an API; do not ship a fake 200",
  },
  {
    id: "SCR-DIFF",
    title: "Сравнение версий",
    git: "partial",
    note: "HTTP finding delta; no_longer_reported ≠ исправлено; two reports, not CDE",
  },
  {
    id: "SCR-USER",
    title: "Дашборд «Пользователь»",
    git: "partial",
    note: "TZ map + intake snapshot + review-kpi; OIDC BFF stays 501",
  },
];
