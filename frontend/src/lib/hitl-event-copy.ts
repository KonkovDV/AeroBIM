import { UI_COPY } from "./ui-copy";

/** Подписи типов HITL-событий. Не точность продукта, не журнал СОД. */
export function hitlEventTypeLabel(eventType: string): string {
  switch (eventType) {
    case "opened":
      return UI_COPY.kpiTypeOpened;
    case "accepted":
      return UI_COPY.kpiTypeAccepted;
    case "rejected":
      return UI_COPY.kpiTypeRejected;
    case "edited":
      return UI_COPY.kpiTypeEdited;
    case "edited_remark":
      return UI_COPY.kpiTypeEditedRemark;
    case "triaged":
      return UI_COPY.kpiTypeTriaged;
    case "waived":
      return UI_COPY.kpiTypeWaived;
    case "superseded":
      return UI_COPY.kpiTypeSuperseded;
    case "escalated":
      return UI_COPY.kpiTypeEscalated;
    default:
      return eventType;
  }
}
