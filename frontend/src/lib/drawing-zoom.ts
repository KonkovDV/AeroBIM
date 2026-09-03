/** Зум/пан превью листа: CSS transform, без пересчёта bbox. Не CV. */

export const DRAWING_SCALE_MIN = 1;
export const DRAWING_SCALE_MAX = 6;
export const DRAWING_SCALE_STEP = 0.2;
export const DRAWING_SCALE_STEP_REDUCED = 0.5;

export type DrawingViewTransform = {
  scale: number;
  x: number;
  y: number;
};

export const IDENTITY_DRAWING_VIEW: DrawingViewTransform = { scale: 1, x: 0, y: 0 };

export function clampDrawingScale(scale: number): number {
  return Math.min(DRAWING_SCALE_MAX, Math.max(DRAWING_SCALE_MIN, Number.isFinite(scale) ? scale : 1));
}

export function applyDrawingWheel(
  view: DrawingViewTransform,
  deltaY: number,
  reducedMotion: boolean,
): DrawingViewTransform {
  const step = reducedMotion ? DRAWING_SCALE_STEP_REDUCED : DRAWING_SCALE_STEP;
  const direction = deltaY > 0 ? -1 : 1;
  const scale = clampDrawingScale(view.scale + direction * step);
  if (scale <= 1) {
    return IDENTITY_DRAWING_VIEW;
  }
  return { ...view, scale };
}

export function applyDrawingPan(
  view: DrawingViewTransform,
  dx: number,
  dy: number,
): DrawingViewTransform {
  if (view.scale <= 1) {
    return IDENTITY_DRAWING_VIEW;
  }
  return { ...view, x: view.x + dx, y: view.y + dy };
}

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
