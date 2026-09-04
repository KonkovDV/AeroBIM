import { UI_COPY } from "../../lib/ui-copy";
import type { AuthBffDiscoveryStatus } from "../../lib/auth-bff";

export type RoleHonestyBannerProps = {
  bffStatus?: AuthBffDiscoveryStatus;
};

/** Header pin: localStorage role is not RBAC. Checkpoint GO; customer_go false. */
export default function RoleHonestyBanner({ bffStatus = "NOT_IMPLEMENTED" }: RoleHonestyBannerProps) {
  const text = bffStatus === "LAB" ? UI_COPY.roleBannerLab : UI_COPY.roleBanner;
  return (
    <p className="role-honesty-banner" role="status" data-testid="role-honesty-banner">
      {text}
    </p>
  );
}
