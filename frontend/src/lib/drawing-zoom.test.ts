import { describe, expect, it } from "vitest";
import {
  applyDrawingPan,
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
});
