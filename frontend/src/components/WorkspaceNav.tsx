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
  { id: "projects", label: "Проекты" },
  { id: "upload", label: "Загрузка" },
  { id: "run", label: "Прогон" },
  { id: "review", label: "Эксперт" },
  { id: "remark", label: "Замечание" },
  { id: "export", label: "Экспорт" },
  { id: "diff", label: "Версии" },
  { id: "user", label: "Эффект" },
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
};

export default function WorkspaceNav({ workspaceView, onChange }: WorkspaceNavProps) {
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
        </button>
      ))}
    </nav>
  );
}
