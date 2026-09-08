export type Cols = { left: number; mid: number; right: number };
export type Side = "left" | "right";
export const MIN_PCT = 16;
export const DEFAULT_COLS: Cols = { left: 28, mid: 36, right: 36 };

const round = (value: number): number => Math.round(value * 10) / 10;
const bound = (value: number, maximum: number): number =>
  round(Math.min(maximum, Math.max(MIN_PCT, value)));

/** Stored preferences are untrusted; every pane keeps its minimum share. */
export function normalizeCols(value: unknown): Cols {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return { ...DEFAULT_COLS };
  }
  const input = value as Partial<Cols>;
  const finite = (candidate: unknown, fallback: number): number =>
    typeof candidate === "number" && Number.isFinite(candidate) ? candidate : fallback;
  const left = bound(finite(input.left, DEFAULT_COLS.left), 100 - 2 * MIN_PCT);
  const right = bound(finite(input.right, DEFAULT_COLS.right), 100 - MIN_PCT - left);
  return { left, mid: round(100 - left - right), right };
}

/** Resize adjacent panes only: the opposite outer pane must not drift. */
export function resizeCols(current: Cols, side: Side, value: number): Cols {
  if (!Number.isFinite(value)) {
    return current;
  }
  const opposite = side === "left" ? "right" : "left";
  const size = bound(value, 100 - MIN_PCT - current[opposite]);
  return { ...current, [side]: size, mid: round(100 - size - current[opposite]) };
}
