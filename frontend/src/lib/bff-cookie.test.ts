import { describe, expect, it } from "vitest";
import { requestHasBffSessionCookie, requestShouldSkipViteBearer } from "./bff-cookie";

describe("requestHasBffSessionCookie", () => {
  it("detects lab and Host-prefixed session cookies", () => {
    expect(requestHasBffSessionCookie("aerobim_bff_session=abc.def")).toBe(true);
    expect(requestHasBffSessionCookie("__Host-aerobim-session=abc.def")).toBe(true);
    expect(requestHasBffSessionCookie("other=1")).toBe(false);
    expect(requestHasBffSessionCookie(undefined)).toBe(false);
  });
});

describe("requestShouldSkipViteBearer", () => {
  it("keeps Bearer inject for unverified lab cookies", () => {
    expect(requestShouldSkipViteBearer("aerobim_bff_session=abc.def")).toBe(false);
  });

  it("skips Bearer only when session and lab authz flag are both present", () => {
    expect(
      requestShouldSkipViteBearer("aerobim_bff_session=abc.def; aerobim_bff_lab_authz=1"),
    ).toBe(true);
    expect(requestShouldSkipViteBearer("aerobim_bff_lab_authz=1")).toBe(false);
  });
});
