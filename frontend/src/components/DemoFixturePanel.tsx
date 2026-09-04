import { useState } from "react";
import { seedDemoFixture } from "../lib/api";
import { UI_COPY } from "../lib/ui-copy";

export type DemoFixturePanelProps = {
  onSeeded: (reportId: string) => void;
  /** When a report is already on the expert screen, hide the essay so the three-pane is the landing. */
  hideIntro?: boolean;
};

export default function DemoFixturePanel({ onSeeded, hideIntro = false }: DemoFixturePanelProps) {
  const [status, setStatus] = useState<"idle" | "loading" | "ok" | "failed">("idle");
  const [detail, setDetail] = useState<string | null>(null);

  async function seed(): Promise<void> {
    setStatus("loading");
    setDetail(null);
    try {
      const result = await seedDemoFixture();
      setStatus("ok");
      setDetail(UI_COPY.demoSeeded(result.issue_count, result.checkpoint));
      onSeeded(result.report_id);
    } catch (error: unknown) {
      setStatus("failed");
      setDetail(error instanceof Error ? error.message : UI_COPY.demoSeedFailed);
    }
  }

  const compact = hideIntro || status === "ok";

  return (
    <section
      className={`panel demo-fixture-panel${compact ? " demo-fixture-compact" : ""}`}
      data-testid="demo-fixture-panel"
      data-compact={compact ? "true" : "false"}
    >
      {compact ? null : (
        <>
          <div className="panel-header">
            <div>
              <p className="panel-kicker">{UI_COPY.demoKicker}</p>
              <h2>{UI_COPY.demoTitle}</h2>
            </div>
          </div>
          <p className="compact-copy">{UI_COPY.demoBody}</p>
        </>
      )}
      <button
        type="button"
        className="toolbar-button"
        aria-label={UI_COPY.demoSeed}
        onClick={() => void seed()}
        disabled={status === "loading"}
      >
        {status === "loading"
          ? UI_COPY.demoSeeding
          : status === "ok"
            ? UI_COPY.demoRepeat
            : compact
              ? UI_COPY.demoTitle
              : UI_COPY.demoSeed}
      </button>
      {detail ? (
        <p className="compact-copy" role="status">
          {detail}
        </p>
      ) : null}
    </section>
  );
}
