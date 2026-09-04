/** Макет экрана в localStorage. Не OIDC. По умолчанию GET /v1/auth/bff = 501. */

import type { AuthBffDiscoveryStatus, AuthBffSession } from "./auth-bff";

export type UiRoleAlias = "expert" | "user";

export const UI_ROLE_STORAGE_KEY = "aerobim-ui-role-alias-v1";

const HITL_EXPERT_ROLE_ALIASES = new Set([
  "reviewer",
  "hitl_reviewer",
  "aerobim:reviewer",
  "aerobim:hitl_reviewer",
  "expert",
  "aerobim:expert",
  "admin",
  "aerobim:admin",
]);

export function readUiRoleAlias(): UiRoleAlias {
  if (typeof window === "undefined") {
    return "expert";
  }
  return window.localStorage.getItem(UI_ROLE_STORAGE_KEY) === "user" ? "user" : "expert";
}

export function persistUiRoleAlias(role: UiRoleAlias): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(UI_ROLE_STORAGE_KEY, role);
}

export function roleAliasFromOidcRoles(roles: readonly string[]): UiRoleAlias {
  const normalized = new Set(roles.map((role) => role.trim().toLowerCase()));
  for (const alias of HITL_EXPERT_ROLE_ALIASES) {
    if (normalized.has(alias)) {
      return "expert";
    }
  }
  return "user";
}

export function hitlEnabledForShell(input: {
  bffStatus: AuthBffDiscoveryStatus;
  session: AuthBffSession | null;
  uiRole: UiRoleAlias;
}): boolean {
  if (input.bffStatus === "LAB") {
    return (
      input.session?.authenticated === true &&
      input.session.identityVerified &&
      roleAliasFromOidcRoles(input.session.roles) === "expert"
    );
  }
  return input.uiRole === "expert";
}
