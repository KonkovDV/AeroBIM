import { describe, expect, it, vi } from "vitest";
import { releaseWebIfcHandle } from "./web-ifc-release";

describe("releaseWebIfcHandle", () => {
  it("calls delete when the handle exposes it", () => {
    const del = vi.fn();
    releaseWebIfcHandle({ delete: del });
    expect(del).toHaveBeenCalledTimes(1);
  });

  it("skips handles without a callable delete (web-ifc FlatMesh gap)", () => {
    expect(() => releaseWebIfcHandle({})).not.toThrow();
    expect(() => releaseWebIfcHandle({ delete: undefined })).not.toThrow();
    expect(() => releaseWebIfcHandle(null)).not.toThrow();
  });
});
