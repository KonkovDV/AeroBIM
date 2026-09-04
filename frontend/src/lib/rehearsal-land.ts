/** Scroll the expert three-pane into view after a demo seed or a finished job. */

export function scrollExpertWorkplaceIntoView(): void {
  document.querySelector("[data-testid='expert-workplace']")?.scrollIntoView({ block: "start" });
}
