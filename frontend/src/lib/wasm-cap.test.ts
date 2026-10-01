import { describe, expect, it } from "vitest";
import {
  WASM_IFC_VIEWER_CAP_BYTES,
  assertFitsIfcViewerCap,
  ifcExceedsViewerCap,
  IfcViewerCapError,
} from "./wasm-cap";

describe("WASM IFC viewer cap", () => {
  it("is 256 MiB, not the 1.5 GB disk ingest figure", () => {
    expect(WASM_IFC_VIEWER_CAP_BYTES).toBe(256 * 1024 * 1024);
    expect(ifcExceedsViewerCap(WASM_IFC_VIEWER_CAP_BYTES)).toBe(false);
    expect(ifcExceedsViewerCap(WASM_IFC_VIEWER_CAP_BYTES + 1)).toBe(true);
  });

  it("throws before OpenModel on oversized payloads", () => {
    expect(() => assertFitsIfcViewerCap(WASM_IFC_VIEWER_CAP_BYTES + 1)).toThrow(IfcViewerCapError);
    expect(() => assertFitsIfcViewerCap(1)).not.toThrow();
  });
});
