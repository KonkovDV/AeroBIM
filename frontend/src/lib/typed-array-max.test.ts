import { describe, expect, it } from "vitest";
import { maxIndexValue } from "./typed-array-max";

describe("maxIndexValue", () => {
  it("returns -1 for an empty buffer", () => {
    expect(maxIndexValue(new Uint32Array())).toBe(-1);
  });

  it("finds the max without spreading into Math.max", () => {
    const indices = new Uint32Array(8);
    indices[0] = 3;
    indices[7] = 41;
    expect(maxIndexValue(indices)).toBe(41);
  });

  it("handles a large index buffer that would overflow Math.max spread", () => {
    const length = 200_000;
    const indices = new Uint32Array(length);
    indices[length - 1] = 99_999;
    expect(maxIndexValue(indices)).toBe(99_999);
  });
});
