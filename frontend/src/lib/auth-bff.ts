/** Разбор GET /v1/auth/bff и /v1/auth/session. 200 LAB ≠ промышленный SSO. */

export type AuthBffDiscoveryStatus = "NOT_IMPLEMENTED" | "LAB" | "UNKNOWN";

export type AuthBffDiscovery = {
  httpStatus: number;
  status: AuthBffDiscoveryStatus;
};

export type AuthBffSession = {
  authenticated: boolean;
  identityVerified: boolean;
  roles: string[];
  tenantId: string | null;
  subject: string | null;
};

function readStatusField(body: unknown): string {
  if (body === null || typeof body !== "object" || !("status" in body)) {
    return "";
  }
  const value = (body as { status?: unknown }).status;
  return typeof value === "string" ? value : "";
}

export function parseAuthBffResponse(httpStatus: number, body: unknown): AuthBffDiscovery {
  const statusField = readStatusField(body);
  if (httpStatus === 501 || statusField === "NOT_IMPLEMENTED") {
    return { httpStatus, status: "NOT_IMPLEMENTED" };
  }
  if (httpStatus === 200 && statusField === "LAB") {
    return { httpStatus, status: "LAB" };
  }
  return { httpStatus, status: "UNKNOWN" };
}

export function parseAuthBffSession(httpStatus: number, body: unknown): AuthBffSession | null {
  if (httpStatus === 501 || httpStatus === 401 || httpStatus !== 200) {
    return null;
  }
  if (body === null || typeof body !== "object") {
    return null;
  }
  const payload = body as {
    authenticated?: unknown;
    identity_verified?: unknown;
    roles?: unknown;
    tenant_id?: unknown;
    sub?: unknown;
  };
  const roles = Array.isArray(payload.roles)
    ? payload.roles.filter((role): role is string => typeof role === "string")
    : [];
  const tenant = typeof payload.tenant_id === "string" ? payload.tenant_id.trim() : "";
  return {
    authenticated: payload.authenticated === true,
    identityVerified: payload.identity_verified === true,
    roles,
    tenantId: tenant.length > 0 ? tenant : null,
    subject: typeof payload.sub === "string" ? payload.sub : null,
  };
}
