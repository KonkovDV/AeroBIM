/** Scroll the expert three-pane into view after a demo seed or a finished job. */

/**
 * Уважаем prefers-reduced-motion. matchMedia нет в jsdom и в старых движках, поэтому
 * отсутствие функции трактуем как «анимация разрешена».
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

export function scrollExpertWorkplaceIntoView(): void {
  document
    .querySelector("[data-testid='expert-workplace']")
    ?.scrollIntoView?.({ block: "start" });
}

/**
 * Прокрутка к списку находок. Цель — #finding-list: тот же узел, что и .issue-list,
 * но id устойчив к правкам классов и уже используется в aria-controls.
 */
export function scrollFindingListIntoView(): void {
  document.getElementById("finding-list")?.scrollIntoView?.({
    block: "nearest",
    behavior: prefersReducedMotion() ? "auto" : "smooth",
  });
}
