import { UI_COPY } from "../lib/ui-copy";

export type WorkspaceView =
  | "projects"
  | "upload"
  | "run"
  | "review"
  | "remark"
  | "export"
  | "diff"
  | "user";

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

export const EXPERT_SHELL_VIEWS: ReadonlySet<WorkspaceView> = new Set([
  "review",
  "remark",
  "export",
]);

export const TRIAGE_KEYBOARD_VIEWS: ReadonlySet<WorkspaceView> = new Set([
  "review",
  "remark",
  "export",
]);

export type WorkspaceNavProps = {
  workspaceView: WorkspaceView;
  onChange: (view: WorkspaceView) => void;
  /** Число находок выбранного отчёта на кнопке «Эксперт». Не точность продукта. */
  reviewFindingsCount?: number | null;
};

export default function WorkspaceNav({
  workspaceView,
  onChange,
  reviewFindingsCount = null,
}: WorkspaceNavProps) {
  return (
    <nav className="workspace-nav" aria-label={UI_COPY.navAria} data-testid="workspace-nav">
      {WORKSPACE_NAV.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          className={`toolbar-button ${workspaceView === id ? "active" : ""}`}
          aria-current={workspaceView === id ? "page" : undefined}
          onClick={() => onChange(id)}
        >
          {label}
          {id === "review" && reviewFindingsCount !== null ? (
            <span
              className="nav-badge"
              data-testid="nav-review-badge"
              title={UI_COPY.navReviewCount(reviewFindingsCount)}
              aria-hidden="true"
            >
              {reviewFindingsCount}
            </span>
          ) : null}
        </button>
      ))}
    </nav>
  );
}
