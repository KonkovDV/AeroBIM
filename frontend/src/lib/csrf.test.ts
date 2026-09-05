import { describe, expect, it } from "vitest";
import { AEROBIM_CSRF_HEADER, AEROBIM_CSRF_VALUE, aerobimCsrfHeaders } from "./csrf";

describe("aerobim CSRF custom header", () => {
  it("exports the review-shell requested-with pair", () => {
    expect(AEROBIM_CSRF_HEADER).toBe("X-AeroBIM-Requested-With");
    expect(AEROBIM_CSRF_VALUE).toBe("AeroBIMReviewShell");
    expect(aerobimCsrfHeaders()[AEROBIM_CSRF_HEADER]).toBe(AEROBIM_CSRF_VALUE);
  });
});
