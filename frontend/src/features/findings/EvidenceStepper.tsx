import type { ValidationIssue } from "../../lib/types";
import { UI_COPY } from "../../lib/ui-copy";

export type EvidenceStepperProps = {
  issue: ValidationIssue | null;
};

export default function EvidenceStepper({ issue }: EvidenceStepperProps) {
  const steps = [
    { id: "essence", label: UI_COPY.essenceStep, ready: Boolean(issue) },
    { id: "sheet", label: UI_COPY.sheetStep, ready: Boolean(issue?.problem_zone?.sheet_id) },
    { id: "spatial", label: UI_COPY.spatialStep, ready: Boolean(issue?.element_guid) },
    {
      id: "raw",
      label: UI_COPY.rawStep,
      ready: Boolean((issue?.evidence_refs?.length ?? 0) > 0),
    },
  ];

  return (
    <ol className="evidence-stepper" data-testid="evidence-stepper" aria-label={UI_COPY.evidenceAria}>
      {steps.map((step) => (
        <li key={step.id} className={step.ready ? "evidence-step ready" : "evidence-step"}>
          {step.label}
          {step.ready ? ` · ${UI_COPY.evidencePresent}` : ` · ${UI_COPY.evidenceMissing}`}
        </li>
      ))}
    </ol>
  );
}
