import { describe, expect, it } from "vitest";
import { hitlEnabledForShell, roleAliasFromOidcRoles } from "./ui-role";
import type { AuthBffSession } from "./auth-bff";

function session(overrides: Partial<AuthBffSession>): AuthBffSession {
  return {
    authenticated: true,
    identityVerified: true,
    roles: ["user"],
    tenantId: "tenant-a",
    subject: "sub-1",
    ...overrides,
  };
}

describe("roleAliasFromOidcRoles", () => {
  it("maps reviewer/admin/expert to the expert screen", () => {
    expect(roleAliasFromOidcRoles(["reviewer"])).toBe("expert");
    expect(roleAliasFromOidcRoles(["aerobim:admin"])).toBe("expert");
    expect(roleAliasFromOidcRoles(["user"])).toBe("user");
    expect(roleAliasFromOidcRoles([])).toBe("user");
  });
});

describe("hitlEnabledForShell", () => {
  it("keeps the localStorage mock when BFF is 501", () => {
    expect(
      hitlEnabledForShell({ bffStatus: "NOT_IMPLEMENTED", session: null, uiRole: "expert" }),
    ).toBe(true);
    expect(
      hitlEnabledForShell({ bffStatus: "NOT_IMPLEMENTED", session: null, uiRole: "user" }),
    ).toBe(false);
  });

  it("requires a verified expert lab session when status is LAB", () => {
    expect(
      hitlEnabledForShell({
        bffStatus: "LAB",
        session: session({ roles: ["user"] }),
        uiRole: "expert",
      }),
    ).toBe(false);
    expect(
      hitlEnabledForShell({
        bffStatus: "LAB",
        session: session({ roles: ["reviewer"], identityVerified: false }),
        uiRole: "expert",
      }),
    ).toBe(false);
    expect(
      hitlEnabledForShell({
        bffStatus: "LAB",
        session: session({ roles: ["reviewer"] }),
        uiRole: "user",
      }),
    ).toBe(true);
  });
});
