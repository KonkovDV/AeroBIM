import { UI_COPY } from "../../lib/ui-copy";

/** Header pin: localStorage role is not RBAC. Checkpoint NO_GO. */
export default function RoleHonestyBanner() {
  return (
    <p className="role-honesty-banner" role="status" data-testid="role-honesty-banner">
      {UI_COPY.roleBanner}
    </p>
  );
}
