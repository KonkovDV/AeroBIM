import { useEffect, useMemo, useState } from "react";
import { fetchAuthBff, fetchAuthSession } from "../lib/api";
import type { AuthBffDiscovery, AuthBffSession } from "../lib/auth-bff";
import { hitlEnabledForShell, roleAliasFromOidcRoles, type UiRoleAlias } from "../lib/ui-role";

export type AuthBffShellState = {
  discovery: AuthBffDiscovery;
  session: AuthBffSession | null;
  roleLocked: boolean;
  screenRole: UiRoleAlias;
  hitlEnabled: boolean;
};

const DEFAULT_DISCOVERY: AuthBffDiscovery = {
  httpStatus: 501,
  status: "NOT_IMPLEMENTED",
};

/**
 * REAL-05: Delay schedule for BFF fetch retries.
 *
 * The BFF may be transiently unavailable at startup (container not ready,
 * reverse-proxy warm-up, network blip). Without retry the app stays in
 * NOT_IMPLEMENTED state permanently and all auth-gated features appear
 * disabled to the jury / demo user.
 *
 * Schedule: attempt 0 = immediate, attempt 1 = 1 s, attempt 2 = 3 s.
 * After all attempts are exhausted the hook falls back to DEFAULT_DISCOVERY
 * (NOT_IMPLEMENTED / 501) so the shell degrades gracefully rather than
 * hanging indefinitely.
 */
const RETRY_DELAYS_MS = [0, 1_000, 3_000] as const;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Fetch BFF discovery + session with exponential-backoff retry.
 * Respects an AbortSignal so the effect cleanup (component unmount or
 * StrictMode double-invoke) stops in-flight retries without leaking state.
 */
async function fetchBffWithRetry(
  signal: AbortSignal,
): Promise<{ discovery: AuthBffDiscovery; session: AuthBffSession | null }> {
  let lastError: unknown;

  for (let attempt = 0; attempt < RETRY_DELAYS_MS.length; attempt++) {
    if (signal.aborted) {
      return { discovery: DEFAULT_DISCOVERY, session: null };
    }

    const delay = RETRY_DELAYS_MS[attempt];
    if (delay > 0) {
      await sleep(delay);
    }

    if (signal.aborted) {
      return { discovery: DEFAULT_DISCOVERY, session: null };
    }

    try {
      const discovery = await fetchAuthBff();
      const session =
        discovery.status === "LAB" ? await fetchAuthSession() : null;
      return { discovery, session };
    } catch (err) {
      lastError = err;
      // Loop continues to the next attempt (unless this was the last one).
    }
  }

  // All retries exhausted — degrade gracefully to NOT_IMPLEMENTED.
  // Log so operator logs show the root cause; never surface to end-user UI.
  console.warn(
    "[useAuthBff] BFF unreachable after",
    RETRY_DELAYS_MS.length,
    "attempts, using fallback.",
    lastError,
  );
  return { discovery: DEFAULT_DISCOVERY, session: null };
}

/** Discovery BFF + сессия. 200 LAB не промышленный SSO. */
export function useAuthBff(uiRole: UiRoleAlias): AuthBffShellState {
  const [discovery, setDiscovery] = useState<AuthBffDiscovery>(DEFAULT_DISCOVERY);
  const [session, setSession] = useState<AuthBffSession | null>(null);

  useEffect(() => {
    // AbortController replaces the boolean `cancelled` flag: it also
    // propagates into any signal-aware fetch helpers added in the future.
    const controller = new AbortController();

    void fetchBffWithRetry(controller.signal).then(({ discovery: d, session: s }) => {
      if (!controller.signal.aborted) {
        setDiscovery(d);
        setSession(s);
      }
    });

    return () => {
      controller.abort();
    };
  }, []);

  return useMemo(() => {
    const roleLocked = discovery.status === "LAB" && session?.identityVerified === true;
    return {
      discovery,
      session,
      roleLocked,
      screenRole: roleLocked && session ? roleAliasFromOidcRoles(session.roles) : uiRole,
      hitlEnabled: hitlEnabledForShell({
        bffStatus: discovery.status,
        session,
        uiRole,
      }),
    };
  }, [discovery, session, uiRole]);
}
