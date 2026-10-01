import { describe, expect, it } from "vitest";
import {
  indexContainedInStorey,
  iterateIdVector,
  unwrapExpressId,
  unwrapString,
} from "./ifc-element-props";

describe("ifc-element-props", () => {
  it("unwraps web-ifc { value } wrappers without inventing names", () => {
    expect(unwrapString({ value: "Wall-1" })).toBe("Wall-1");
    expect(unwrapString({ value: "  " })).toBeNull();
    expect(unwrapExpressId({ value: 42 })).toBe(42);
    expect(unwrapExpressId({ expressID: 7 })).toBe(7);
  });

  it("iterates size/get vectors and arrays", () => {
    expect(iterateIdVector([1, { value: 2 }])).toEqual([1, 2]);
    const vector = {
      size: () => 2,
      get: (index: number) => (index === 0 ? 10 : 11),
    };
    expect(iterateIdVector(vector)).toEqual([10, 11]);
  });

  it("indexes RelContainedInSpatialStructure only for known storeys", () => {
    const map = indexContainedInStorey(
      [
        { RelatingStructure: { value: 100 }, RelatedElements: [{ value: 1 }, { value: 2 }] },
        { RelatingStructure: { value: 999 }, RelatedElements: [{ value: 3 }] },
      ],
      new Set([100]),
    );
    expect(map.get(1)).toBe(100);
    expect(map.get(2)).toBe(100);
    expect(map.has(3)).toBe(false);
  });
});
