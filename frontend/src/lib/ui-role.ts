/** Local UI screen mock. Not OIDC. GET /v1/auth/bff stays 501. Does not grant HITL. */

export type UiRoleAlias = "expert" | "user";

export const UI_ROLE_STORAGE_KEY = "aerobim-ui-role-alias-v1";

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
