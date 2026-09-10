/** Eight-screen IA. Status SSOT remains the backend screen rows. */

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
    note: "Сохранённый список отчётов; выбор комплекта открывает рабочее место эксперта",
  },
  {
    id: "SCR-UPLOAD",
    title: "Загрузка комплекта",
    git: "partial",
    note: "Зона сброса и прогресс; нативные форматы отклоняются до отправки",
  },
  {
    id: "SCR-RUN",
    title: "Прогон анализа",
    git: "partial",
    note: "Ожидание результата и группы проверок; подробный поток событий не показан",
  },
  {
    id: "SCR-EXPERT",
    title: "Рабочее место эксперта",
    git: "partial",
    note: "Три панели: замечания, лист и модель, карточка",
  },
  {
    id: "SCR-REMARK",
    title: "Карточка замечания",
    git: "partial",
    note: "Текст замечания и история решений; этаж и ось или «нет в индексе»",
  },
  {
    id: "SCR-EXPORT",
    title: "Отчёт и экспорт",
    git: "partial",
    note: "HTML, JSON, BCF; PDF — черновик покрытия; таблица Excel не выгружается",
  },
  {
    id: "SCR-DIFF",
    title: "Сравнение версий",
    git: "partial",
    note: "Сравнение двух отчётов; «не воспроизведено» ≠ исправлено",
  },
  {
    id: "SCR-USER",
    title: "Экран «Эффект»",
    git: "partial",
    note: "Карта требований, рамка приёмки и показатели разбора",
  },
];
