import { describe, expect, it } from "vitest";
import { ApiHttpError } from "./api";
import { classifyRequestFailure } from "./request-failure";

describe("classifyRequestFailure", () => {
  it("separates forbidden from network without reading exception prose", () => {
    expect(classifyRequestFailure(new ApiHttpError(403, "http://secret-host/v1"))).toBe("forbidden");
    expect(classifyRequestFailure(new TypeError("Failed to fetch"))).toBe("network");
    expect(classifyRequestFailure(new ApiHttpError(404, "missing"))).toBe("not_found");
    expect(classifyRequestFailure(new ApiHttpError(500, "trace"))).toBe("server");
  });

  it("does not invent a category from arbitrary Error text", () => {
    expect(classifyRequestFailure(new Error("API down: http://private-host"))).toBe("unknown");
  });
});
