/** Зум/пан превью листа: CSS transform, без пересчёта bbox. Не CV. */

export const DRAWING_SCALE_MIN = 1;
export const DRAWING_SCALE_MAX = 6;
export const DRAWING_SCALE_STEP = 0.2;
export const DRAWING_SCALE_STEP_REDUCED = 0.5;
export const DRAWING_SCALE_STEP_BUTTON = 0.5;

export type DrawingPointer = { x: number; y: number };

export type DrawingViewTransform = {
  scale: number;
  x: number;
  y: number;
};

export const IDENTITY_DRAWING_VIEW: DrawingViewTransform = { scale: 1, x: 0, y: 0 };

export function clampDrawingScale(scale: number): number {
  return Math.min(DRAWING_SCALE_MAX, Math.max(DRAWING_SCALE_MIN, Number.isFinite(scale) ? scale : 1));
}

function scaleTowardPointer(
  view: DrawingViewTransform,
  scale: number,
  pointer?: DrawingPointer,
): DrawingViewTransform {
  if (scale <= 1) {
    return IDENTITY_DRAWING_VIEW;
  }
  if (!pointer || view.scale <= 0) {
    return { ...view, scale };
  }
  const ratio = scale / view.scale;
  return {
    scale,
    x: pointer.x - ratio * (pointer.x - view.x),
    y: pointer.y - ratio * (pointer.y - view.y),
  };
}

export function applyDrawingWheel(
  view: DrawingViewTransform,
  deltaY: number,
  reducedMotion: boolean,
  pointer?: DrawingPointer,
): DrawingViewTransform {
  const step = reducedMotion ? DRAWING_SCALE_STEP_REDUCED : DRAWING_SCALE_STEP;
  const direction = deltaY > 0 ? -1 : 1;
  const scale = clampDrawingScale(view.scale + direction * step);
  return scaleTowardPointer(view, scale, pointer);
}

export function applyDrawingScaleStep(
  view: DrawingViewTransform,
  direction: 1 | -1,
  pointer?: DrawingPointer,
): DrawingViewTransform {
  const scale = clampDrawingScale(view.scale + direction * DRAWING_SCALE_STEP_BUTTON);
  return scaleTowardPointer(view, scale, pointer);
}

export function applyDrawingPinch(
  view: DrawingViewTransform,
  scaleRatio: number,
  midpoint: DrawingPointer,
): DrawingViewTransform {
  const ratio = Number.isFinite(scaleRatio) && scaleRatio > 0 ? scaleRatio : 1;
  const scale = clampDrawingScale(view.scale * ratio);
  return scaleTowardPointer(view, scale, midpoint);
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
