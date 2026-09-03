import { UI_COPY } from "../../lib/ui-copy";
import type { UiRoleAlias } from "../../lib/ui-role";
import RoleHonestyBanner from "../honesty/RoleHonestyBanner";

export type ShellHeaderProps = {
  apiBase: string;
  reportCount: number;
  uiRole: UiRoleAlias;
  onRoleChange: (role: UiRoleAlias) => void;
};

export default function ShellHeader({
  apiBase,
  reportCount,
  uiRole,
  onRoleChange,
}: ShellHeaderProps) {
  return (
    <header className="app-header">
      <div>
        <p className="eyebrow">{UI_COPY.headerEyebrow}</p>
        <h1>{UI_COPY.headerTitle}</h1>
        <p className="lede">
          {UI_COPY.headerLede.split("summary.passed").map((part, index, parts) =>
            index < parts.length - 1 ? (
              <span key={part}>
                {part}
                <code>summary.passed</code>
              </span>
            ) : (
              <span key={part}>{part}</span>
            ),
          )}
        </p>
        <RoleHonestyBanner />
      </div>
      <div className="header-card">
        <span>{UI_COPY.apiLabel}</span>
        <strong>{apiBase || UI_COPY.sameOriginApi}</strong>
        <span>{UI_COPY.reportsLoaded(reportCount)}</span>
        <label className="role-alias">
          {UI_COPY.roleSelectLabel}
          <select
            aria-label={UI_COPY.roleSelectLabel}
            value={uiRole}
            onChange={(event) => {
              onRoleChange(event.target.value === "user" ? "user" : "expert");
            }}
          >
            <option value="expert">{UI_COPY.roleExpert}</option>
            <option value="user">{UI_COPY.roleUser}</option>
          </select>
        </label>
      </div>
    </header>
  );
}
