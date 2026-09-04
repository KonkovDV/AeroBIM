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

/** Discovery BFF + сессия. 200 LAB не промышленный SSO. */
export function useAuthBff(uiRole: UiRoleAlias): AuthBffShellState {
  const [discovery, setDiscovery] = useState<AuthBffDiscovery>(DEFAULT_DISCOVERY);
  const [session, setSession] = useState<AuthBffSession | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const nextDiscovery = await fetchAuthBff();
      const nextSession = nextDiscovery.status === "LAB" ? await fetchAuthSession() : null;
      if (!cancelled) {
        setDiscovery(nextDiscovery);
        setSession(nextSession);
      }
    })();
    return () => {
      cancelled = true;
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
