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
    note: "Сохранённый список отчётов; выбор комплекта открывает трёхпанель эксперта",
  },
  {
    id: "SCR-UPLOAD",
    title: "Загрузка комплекта",
    git: "partial",
    note: "POST /v1/uploads: зона сброса, прогресс, отмена; нативные форматы — жёсткий отказ",
  },
  {
    id: "SCR-RUN",
    title: "Прогон анализа",
    git: "partial",
    note: "Опрос jobs/{job_id}; группы движков из матрицы возможностей; SSE не поставлен",
  },
  {
    id: "SCR-EXPERT",
    title: "Рабочее место эксперта",
    git: "partial",
    note: "Три панели ТЗ: находки | 2D/3D | замечание; индекс отчётов — SCR-PROJECTS",
  },
  {
    id: "SCR-REMARK",
    title: "Карточка замечания",
    git: "partial",
    note: "HITL-замечание + история review-events; этаж/ось или «нет в индексе»",
  },
  {
    id: "SCR-EXPORT",
    title: "Отчёт и экспорт",
    git: "partial",
    note: "HTML JSON BCF 2.1/3.0; PDF = черновик покрытия; XLSX нет в API; фальшивый 200 не поставляем",
  },
  {
    id: "SCR-DIFF",
    title: "Сравнение версий",
    git: "partial",
    note: "HTTP-дельта находок; «не воспроизведено» ≠ исправлено; два отчёта, не CDE",
  },
  {
    id: "SCR-USER",
    title: "Дашборд «Пользователь»",
    git: "partial",
    note: "Карта ТЗ + снимок приёмки + показатели ревью; OIDC BFF остаётся 501",
  },
];
