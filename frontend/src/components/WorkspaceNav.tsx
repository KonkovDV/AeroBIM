import { useEffect, useId } from "react";
import { UI_COPY } from "../lib/ui-copy";
import { isTextEntryTarget } from "../lib/triage-hotkeys";
import WorkspaceIcon from "./WorkspaceIcon";

export type WorkspaceView = "projects" | "upload" | "run" | "review" | "remark" | "export" | "diff" | "user";
export const WORKSPACE_NAV: readonly { id: WorkspaceView; label: string }[] = [
  { id: "projects", label: UI_COPY.navProjects },
  { id: "upload", label: UI_COPY.navUpload },
  { id: "run", label: UI_COPY.navRun },
  { id: "review", label: UI_COPY.navReview },
  { id: "remark", label: UI_COPY.navRemark },
  { id: "export", label: UI_COPY.navExport },
  { id: "diff", label: UI_COPY.navDiff },
  { id: "user", label: UI_COPY.navUser },
];
export const EXPERT_SHELL_VIEWS: ReadonlySet<WorkspaceView> = new Set(["review", "remark", "export"]);
export const TRIAGE_KEYBOARD_VIEWS: ReadonlySet<WorkspaceView> = new Set(["review", "remark", "export"]);
export function formatNavBadgeCount(count: number): string {
  return count > 99 ? "99+" : String(count);
}
export type WorkspaceNavProps = {
  workspaceView: WorkspaceView;
  onChange: (view: WorkspaceView) => void;
  reviewFindingsCount?: number | null;
};

export default function WorkspaceNav({ workspaceView, onChange, reviewFindingsCount = null }: WorkspaceNavProps) {
  const countId = useId();
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent): void {
      if (!event.altKey || event.ctrlKey || event.metaKey || event.repeat || event.isComposing || event.defaultPrevented) return;
      if (isTextEntryTarget(event.target)) return;
      const next = WORKSPACE_NAV[Number(event.key) - 1];
      if (!next) return;
      event.preventDefault();
      onChange(next.id);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onChange]);

  return (
    <nav className="workspace-nav product-nav" aria-label={UI_COPY.navAria} data-testid="workspace-nav">
      <label className="product-mobile-nav">
        <span>{UI_COPY.mobileNavLabel}</span>
        <select value={workspaceView} onChange={(event) => {
          const next = WORKSPACE_NAV.find(({ id }) => id === event.target.value);
          if (next) onChange(next.id);
        }}>
          {WORKSPACE_NAV.map(({ id, label }) => <option key={id} value={id}>{label}</option>)}
        </select>
      </label>
      <div className="product-nav-links">
        {WORKSPACE_NAV.map(({ id, label }, index) => (
          <button key={id} type="button"
            className={`toolbar-button ${workspaceView === id ? "active" : ""}`}
            aria-current={workspaceView === id ? "page" : undefined}
            aria-keyshortcuts={`Alt+${index + 1}`}
            aria-describedby={id === "review" && reviewFindingsCount !== null ? countId : undefined}
            onClick={() => onChange(id)}>
            <WorkspaceIcon name={id} />
            {label}
            {id === "review" && reviewFindingsCount !== null ? (
              <span className="nav-badge" data-testid="nav-review-badge"
                title={UI_COPY.navReviewCount(reviewFindingsCount)} aria-hidden="true">
                {formatNavBadgeCount(reviewFindingsCount)}
              </span>
            ) : null}
          </button>
        ))}
      </div>
      {reviewFindingsCount !== null ? <span id={countId} className="product-sr-only">{UI_COPY.navReviewCount(reviewFindingsCount)}</span> : null}
    </nav>
  );
}
