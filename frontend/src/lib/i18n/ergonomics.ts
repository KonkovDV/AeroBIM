/** Эргономика оболочки: пропуск навигации и плотность списков. */
export const ERGONOMICS_COPY = {
  skipToWork: "Перейти к рабочей области",
  densityLabel: "Плотность",
  densityComfortable: "Обычная",
  densityCompact: "Плотная",
  densityHint: (target: string) => `Переключить плотность списков: ${target.toLowerCase()}`,
  densityAnnounce: (mode: string) => `Плотность списков: ${mode.toLowerCase()}`,
} as const;
