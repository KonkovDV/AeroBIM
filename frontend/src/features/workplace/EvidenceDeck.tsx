import { useId, useState, type KeyboardEvent, type ReactNode } from "react";
import { UI_COPY } from "../../lib/ui-copy";

type EvidenceTab = "model" | "drawing" | "clash";

const TABS: readonly { id: EvidenceTab; label: string }[] = [
  { id: "model", label: UI_COPY.evidenceTabModel },
  { id: "drawing", label: UI_COPY.evidenceTabDrawing },
  { id: "clash", label: UI_COPY.evidenceTabClash },
];

export type EvidenceDeckProps = {
  model: ReactNode;
  drawing: ReactNode;
  clash: ReactNode;
  expanded?: boolean;
  onToggleExpanded?: () => void;
};

/**
 * Center inspector from the reference console: one evidence surface at a time.
 * The panels stay the application's own viewer, drawing overlay and clash list.
 */
export default function EvidenceDeck({
  model,
  drawing,
  clash,
  expanded = false,
  onToggleExpanded,
}: EvidenceDeckProps) {
  const [tab, setTab] = useState<EvidenceTab>("model");
  const base = useId().replace(/:/g, "");
  const panels: Record<EvidenceTab, ReactNode> = { model, drawing, clash };

  function onTabKey(event: KeyboardEvent<HTMLDivElement>): void {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const index = TABS.findIndex((item) => item.id === tab);
    const next =
      event.key === "ArrowRight" ? TABS[(index + 1) % TABS.length]
      : event.key === "ArrowLeft" ? TABS[(index - 1 + TABS.length) % TABS.length]
      : event.key === "Home" ? TABS[0]
      : event.key === "End" ? TABS[TABS.length - 1]
      : null;
    if (!next) return;
    event.preventDefault();
    event.stopPropagation();
    setTab(next.id);
    document.getElementById(`${base}-tab-${next.id}`)?.focus();
  }

  return (
    <div className="evidence-deck" data-testid="evidence-deck">
      <div className="evidence-deck-bar">
      <div
        className="evidence-deck-tabs"
        role="tablist"
        aria-label={UI_COPY.evidenceDeckAria}
        aria-orientation="horizontal"
        onKeyDown={onTabKey}
      >
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            id={`${base}-tab-${item.id}`}
            aria-selected={tab === item.id}
            aria-controls={`${base}-panel-${item.id}`}
            tabIndex={tab === item.id ? 0 : -1}
            className={tab === item.id ? "active" : ""}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
        {onToggleExpanded ? (
          <button
            type="button"
            className="evidence-deck-expand"
            aria-pressed={expanded}
            onClick={onToggleExpanded}
          >
            {expanded ? UI_COPY.restorePanes : UI_COPY.expandCenter}
          </button>
        ) : null}
      </div>
      {TABS.map((item) => (
        <div
          key={item.id}
          role="tabpanel"
          id={`${base}-panel-${item.id}`}
          aria-labelledby={`${base}-tab-${item.id}`}
          hidden={tab !== item.id}
          tabIndex={tab === item.id ? 0 : undefined}
          className="evidence-deck-panel"
        >
          {panels[item.id]}
        </div>
      ))}
    </div>
  );
}
