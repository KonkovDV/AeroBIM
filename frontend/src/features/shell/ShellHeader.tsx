import DensityToggle from "../../components/DensityToggle";
import { UI_COPY } from "../../lib/ui-copy";
import type { UiRoleAlias } from "../../lib/ui-role";
import type { AuthBffDiscoveryStatus } from "../../lib/auth-bff";
import RoleHonestyBanner from "../honesty/RoleHonestyBanner";

export type ShellHeaderProps = {
  /** Kept for caller compatibility; service addresses never appear in product UI. */
  apiBase: string;
  reportCount: number;
  uiRole: UiRoleAlias;
  onRoleChange: (role: UiRoleAlias) => void;
  bffStatus?: AuthBffDiscoveryStatus;
  roleLocked?: boolean;
};

export default function ShellHeader({
  reportCount,
  uiRole,
  onRoleChange,
  bffStatus = "NOT_IMPLEMENTED",
  roleLocked = false,
}: ShellHeaderProps) {
  return (
    <header className="app-header product-header">
      <a className="skip-to-work" href="#work-area" data-testid="skip-to-work">
        {UI_COPY.skipToWork}
      </a>
      <div className="product-identity">
        <span className="brand-mark" aria-hidden="true" />
        <div className="product-title">
          <p className="product-wordmark">{UI_COPY.headerEyebrow}</p>
          <h1>{UI_COPY.headerTitle}</h1>
        </div>
      </div>
      <div className="product-toolbar">
        <span className="product-report-count">{UI_COPY.reportsLoaded(reportCount)}</span>
        <DensityToggle />
        <label className="product-role">
          <span>{UI_COPY.roleSelectLabel}</span>
          <select
            aria-label={UI_COPY.roleSelectLabel}
            value={uiRole}
            disabled={roleLocked}
            onChange={(event) => onRoleChange(event.target.value === "user" ? "user" : "expert")}
          >
            <option value="expert">{UI_COPY.roleExpert}</option>
            <option value="user">{UI_COPY.roleUser}</option>
          </select>
        </label>
      </div>
      <div className="product-context">
        <RoleHonestyBanner bffStatus={bffStatus} />
        <details className="scope-disclosure product-scope">
            <summary>{UI_COPY.scopeDisclosure}</summary>
          <p className="lede">{UI_COPY.headerLede}</p>
        </details>
      </div>
    </header>
  );
}
