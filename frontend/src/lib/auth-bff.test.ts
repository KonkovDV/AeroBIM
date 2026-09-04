import { describe, expect, it } from "vitest";
import { parseAuthBffResponse, parseAuthBffSession } from "./auth-bff";

describe("parseAuthBffResponse", () => {
  it("treats 501 as NOT_IMPLEMENTED", () => {
    expect(parseAuthBffResponse(501, { status: "NOT_IMPLEMENTED" })).toEqual({
      httpStatus: 501,
      status: "NOT_IMPLEMENTED",
    });
  });

  it("treats 200 + LAB as lab, not SSO", () => {
    expect(parseAuthBffResponse(200, { status: "LAB", phase: 3 })).toEqual({
      httpStatus: 200,
      status: "LAB",
    });
  });

  it("does not treat a random 200 as LAB", () => {
    expect(parseAuthBffResponse(200, { status: "ok" }).status).toBe("UNKNOWN");
    expect(parseAuthBffResponse(200, { status: "IMPLEMENTED" }).status).toBe("UNKNOWN");
  });
});

describe("parseAuthBffSession", () => {
  it("returns null on 501 and 401", () => {
    expect(parseAuthBffSession(501, { authenticated: false })).toBeNull();
    expect(parseAuthBffSession(401, { authenticated: false })).toBeNull();
  });

  it("parses a verified lab session without claiming SSO", () => {
    const session = parseAuthBffSession(200, {
      authenticated: true,
      identity_verified: true,
      roles: ["reviewer"],
      tenant_id: "tenant-a",
      sub: "expert-1",
      production_sso: false,
    });
    expect(session).toEqual({
      authenticated: true,
      identityVerified: true,
      roles: ["reviewer"],
      tenantId: "tenant-a",
      subject: "expert-1",
    });
  });
});
