/** Имена cookie лабораторного BFF. Не промышленный SSO. */

export const BFF_SESSION_COOKIE_NAMES = ["aerobim_bff_session", "__Host-aerobim-session"] as const;

export const BFF_LAB_AUTHZ_COOKIE_NAME = "aerobim_bff_lab_authz";

function cookieHeaderToRaw(
  cookieHeader: string | readonly string[] | undefined,
): string {
  if (cookieHeader == null) {
    return "";
  }
  if (typeof cookieHeader === "string") {
    return cookieHeader;
  }
  return cookieHeader.join("; ");
}

function parseCookiePairs(
  cookieHeader: string | readonly string[] | undefined,
): Map<string, string> {
  const raw = cookieHeaderToRaw(cookieHeader);
  const pairs = new Map<string, string>();
  if (!raw) {
    return pairs;
  }
  for (const segment of raw.split(";")) {
    const trimmed = segment.trim();
    if (!trimmed) {
      continue;
    }
    const eq = trimmed.indexOf("=");
    if (eq <= 0) {
      continue;
    }
    const name = trimmed.slice(0, eq).trim();
    if (!name) {
      continue;
    }
    pairs.set(name, trimmed.slice(eq + 1).trim());
  }
  return pairs;
}

export function requestHasBffSessionCookie(
  cookieHeader: string | readonly string[] | undefined,
): boolean {
  const pairs = parseCookiePairs(cookieHeader);
  return BFF_SESSION_COOKIE_NAMES.some((name) => pairs.has(name));
}

/** Vite skips loopback Bearer only when the lab session is verified (HD3-BFF-01). */
export function requestShouldSkipViteBearer(
  cookieHeader: string | readonly string[] | undefined,
): boolean {
  const pairs = parseCookiePairs(cookieHeader);
  const hasSession = BFF_SESSION_COOKIE_NAMES.some((name) => pairs.has(name));
  return hasSession && pairs.get(BFF_LAB_AUTHZ_COOKIE_NAME) === "1";
}
