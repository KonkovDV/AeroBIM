import { UI_COPY } from "../../lib/ui-copy";
import type { AuthBffDiscoveryStatus } from "../../lib/auth-bff";

export type RoleHonestyBannerProps = {
  bffStatus?: AuthBffDiscoveryStatus;
};

/** Header pin: localStorage role is not RBAC. Checkpoint GO; customer_go false. */
function bannerCopy(status: AuthBffDiscoveryStatus): string {
  if (status === "LAB") {
    return UI_COPY.roleBannerLab;
  }
  if (status === "LOADING") {
    return UI_COPY.roleBannerLoading;
  }
  if (status === "UNKNOWN") {
    return UI_COPY.roleBannerUnknown;
  }
  return UI_COPY.roleBanner;
}

export default function RoleHonestyBanner({ bffStatus = "NOT_IMPLEMENTED" }: RoleHonestyBannerProps) {
  const text = bannerCopy(bffStatus);
  return (
    <p className="role-honesty-banner" role="status" data-testid="role-honesty-banner">
      {text}
    </p>
  );
}
