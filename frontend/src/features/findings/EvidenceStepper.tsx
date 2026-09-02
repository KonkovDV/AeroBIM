import type { ValidationIssue } from "../../lib/types";

export type EvidenceStepperProps = {
  issue: ValidationIssue | null;
};

export default function EvidenceStepper({ issue }: EvidenceStepperProps) {
  const steps = [
    { id: "essence", label: "1 essence", ready: Boolean(issue) },
    { id: "sheet", label: "2 sheet", ready: Boolean(issue?.problem_zone?.sheet_id) },
    { id: "spatial", label: "3 3D", ready: Boolean(issue?.element_guid) },
    {
      id: "raw",
      label: "4 raw",
      ready: Boolean((issue?.evidence_refs?.length ?? 0) > 0),
    },
  ];

  return (
    <ol className="evidence-stepper" data-testid="evidence-stepper" aria-label="Evidence levels">
      {steps.map((step) => (
        <li key={step.id} className={step.ready ? "evidence-step ready" : "evidence-step"}>
          {step.label}
          {step.ready ? " · present" : " · missing"}
        </li>
      ))}
    </ol>
  );
}
