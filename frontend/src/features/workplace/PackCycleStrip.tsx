import type { WorkspaceView } from "../../components/WorkspaceNav";
import { packDraftHasAny, type PackDraft } from "../../lib/pack-draft";

export type PackCycleStepId = "upload" | "run" | "expert" | "export";

const STEPS: readonly {
  id: PackCycleStepId;
  label: string;
  ariaLabel: string;
  view: WorkspaceView;
  views: readonly WorkspaceView[];
}[] = [
  { id: "upload", label: "Загрузка", ariaLabel: "Цикл: приём файлов", view: "upload", views: ["upload"] },
  { id: "run", label: "Прогон", ariaLabel: "Цикл: запуск анализа", view: "run", views: ["run"] },
  { id: "expert", label: "Эксперт", ariaLabel: "Цикл: триаж находок", view: "review", views: ["review", "remark"] },
  { id: "export", label: "Экспорт", ariaLabel: "Цикл: выгрузка отчёта", view: "export", views: ["export"] },
];

export type PackCycleStripProps = {
  workspaceView: WorkspaceView;
  packDraft: PackDraft;
  hasReport: boolean;
  onChange: (view: WorkspaceView) => void;
};

function stepState(
  step: (typeof STEPS)[number],
  workspaceView: WorkspaceView,
  packDraft: PackDraft,
  hasReport: boolean,
): "current" | "ready" | "blocked" {
  if (step.views.includes(workspaceView)) {
    return "current";
  }
  if (step.id === "upload") {
    return "ready";
  }
  if (step.id === "run") {
    return packDraftHasAny(packDraft) ? "ready" : "blocked";
  }
  if (step.id === "expert" || step.id === "export") {
    return hasReport ? "ready" : "blocked";
  }
  return "blocked";
}

export default function PackCycleStrip({
  workspaceView,
  packDraft,
  hasReport,
  onChange,
}: PackCycleStripProps) {
  return (
    <nav className="pack-cycle-strip" aria-label="Цикл комплекта" data-testid="pack-cycle-strip">
      {STEPS.map((step, index) => {
        const state = stepState(step, workspaceView, packDraft, hasReport);
        return (
          <span key={step.id} className="pack-cycle-step-wrap">
            {index > 0 ? <span className="pack-cycle-arrow" aria-hidden="true">→</span> : null}
            <button
              type="button"
              className={`pack-cycle-step pack-cycle-step-${state}`}
              aria-label={step.ariaLabel}
              aria-current={state === "current" ? "step" : undefined}
              disabled={state === "blocked"}
              onClick={() => onChange(step.view)}
            >
              {step.label}
            </button>
          </span>
        );
      })}
      <p className="pack-cycle-caption">
        Загрузка → прогон → триаж → отчёт. Не измеренный SLA. UI не пишет{" "}
        <code>summary.passed</code>.
      </p>
    </nav>
  );
}
