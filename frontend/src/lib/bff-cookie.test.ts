import { describe, expect, it } from "vitest";
import { requestHasBffSessionCookie, requestShouldSkipViteBearer } from "./bff-cookie";

describe("requestHasBffSessionCookie", () => {
  it("detects lab and Host-prefixed session cookies", () => {
    expect(requestHasBffSessionCookie("aerobim_bff_session=abc.def")).toBe(true);
    expect(requestHasBffSessionCookie("__Host-aerobim-session=abc.def")).toBe(true);
    expect(requestHasBffSessionCookie("other=1")).toBe(false);
    expect(requestHasBffSessionCookie(undefined)).toBe(false);
  });

  it("rejects prefix and suffix tossing of the session name", () => {
    expect(requestHasBffSessionCookie("not_aerobim_bff_session=abc.def")).toBe(false);
    expect(requestHasBffSessionCookie("fooaerobim_bff_session=abc.def")).toBe(false);
    expect(requestHasBffSessionCookie("aerobim_bff_session_extra=abc.def")).toBe(false);
    expect(requestHasBffSessionCookie("aerobim_bff_session=abc.def")).toBe(true);
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

  it("does not skip Bearer on prefix tossing plus a lab authz flag", () => {
    expect(
      requestShouldSkipViteBearer("not_aerobim_bff_session=1; aerobim_bff_lab_authz=1"),
    ).toBe(false);
    expect(
      requestShouldSkipViteBearer("fooaerobim_bff_session=1; aerobim_bff_lab_authz=1"),
    ).toBe(false);
  });

  it("requires the lab authz value to be exactly 1", () => {
    expect(
      requestShouldSkipViteBearer("aerobim_bff_session=abc.def; aerobim_bff_lab_authz=10"),
    ).toBe(false);
    expect(
      requestShouldSkipViteBearer("aerobim_bff_session=abc.def; aerobim_bff_lab_authz=1x"),
    ).toBe(false);
  });
});
