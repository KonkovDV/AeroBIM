/** Имена cookie лабораторного BFF. Не промышленный SSO. */

export const BFF_SESSION_COOKIE_NAMES = ["aerobim_bff_session", "__Host-aerobim-session"] as const;

export const BFF_LAB_AUTHZ_COOKIE_NAME = "aerobim_bff_lab_authz";

export function requestHasBffSessionCookie(
  cookieHeader: string | readonly string[] | undefined,
): boolean {
  const raw = Array.isArray(cookieHeader) ? cookieHeader.join("; ") : (cookieHeader ?? "");
  return BFF_SESSION_COOKIE_NAMES.some((name) => raw.includes(`${name}=`));
}

/** Vite skips loopback Bearer only when the lab session is verified (HD3-BFF-01). */
export function requestShouldSkipViteBearer(
  cookieHeader: string | readonly string[] | undefined,
): boolean {
  const raw = Array.isArray(cookieHeader) ? cookieHeader.join("; ") : (cookieHeader ?? "");
  return (
    requestHasBffSessionCookie(raw) && raw.includes(`${BFF_LAB_AUTHZ_COOKIE_NAME}=1`)
  );
}
