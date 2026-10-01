import { describe, expect, it } from "vitest";
import {
  applyDrawingPan,
  applyDrawingPinch,
  applyDrawingScaleStep,
  applyDrawingWheel,
  IDENTITY_DRAWING_VIEW,
} from "./drawing-zoom";

describe("drawing-zoom", () => {
  it("zooms in on wheel-up and resets to identity at scale 1", () => {
    const zoomed = applyDrawingWheel(IDENTITY_DRAWING_VIEW, -100, false);
    expect(zoomed.scale).toBeGreaterThan(1);
    const out = applyDrawingWheel(zoomed, 400, false);
    expect(out).toEqual(IDENTITY_DRAWING_VIEW);
  });

  it("uses a coarser step when reduced motion is requested", () => {
    const normal = applyDrawingWheel(IDENTITY_DRAWING_VIEW, -1, false);
    const reduced = applyDrawingWheel(IDENTITY_DRAWING_VIEW, -1, true);
    expect(reduced.scale).toBeGreaterThan(normal.scale);
  });

  it("pans only when zoomed", () => {
    expect(applyDrawingPan(IDENTITY_DRAWING_VIEW, 10, 10)).toEqual(IDENTITY_DRAWING_VIEW);
    const panned = applyDrawingPan({ scale: 2, x: 0, y: 0 }, 5, -3);
    expect(panned).toEqual({ scale: 2, x: 5, y: -3 });
  });

  it("zooms toward the pointer instead of the origin", () => {
    const pointer = { x: 100, y: 40 };
    const zoomed = applyDrawingWheel(IDENTITY_DRAWING_VIEW, -1, false, pointer);
    expect(zoomed.scale).toBe(1.2);
    expect(zoomed.x).toBeCloseTo(100 - 1.2 * 100);
    expect(zoomed.y).toBeCloseTo(40 - 1.2 * 40);
  });

  it("steps scale from the +/- buttons by 0.5", () => {
    const zoomed = applyDrawingScaleStep(IDENTITY_DRAWING_VIEW, 1);
    expect(zoomed.scale).toBe(1.5);
    expect(applyDrawingScaleStep(zoomed, -1).scale).toBe(1);
  });

  it("applies a pinch ratio about the midpoint", () => {
    const pinched = applyDrawingPinch({ scale: 2, x: 0, y: 0 }, 1.5, { x: 10, y: 10 });
    expect(pinched.scale).toBe(3);
  });
});
