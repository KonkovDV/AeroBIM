import { useEffect, useState } from "react";
import { fetchReviewKpi, type ReviewKpiPayload } from "../lib/api";

export type ReviewKpiPanelProps = {
  reportId: string | null;
};

function formatRate(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "no decisions";
  }
  return `${Math.round(value * 100)} % confirmed among accepted/rejected`;
}

export default function ReviewKpiPanel({ reportId }: ReviewKpiPanelProps) {
  const [payload, setPayload] = useState<ReviewKpiPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!reportId) {
      setPayload(null);
      setError(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    void fetchReviewKpi(reportId, { signal: controller.signal })
      .then((next) => {
        setPayload(next);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setPayload(null);
          setError(err instanceof Error ? err.message : "KPI unavailable");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [reportId]);

  return (
    <section className="panel kpi-panel" data-testid="review-kpi-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">Effect dashboard</p>
          <h2>review-kpi</h2>
        </div>
      </div>
      <p className="compact-copy">
        HITL journal, not product accuracy and not A1–A8 hours. UI-event latency is not an SLA for
        “time to first valid remark”. An empty journal is an empty screen, not “0 % errors”.
        Checkpoint NO_GO.
      </p>
      {!reportId ? (
        <p className="panel-empty">Select a report in the list, then open this screen.</p>
      ) : loading ? (
        <p className="compact-copy">Loading KPI…</p>
      ) : error ? (
        <p className="compact-copy">{error}</p>
      ) : payload ? (
        <ul className="kpi-list">
          <li>Events: {payload.kpi.event_count}</li>
          <li>Opened: {payload.kpi.opened_count}</li>
          <li>Triage: {payload.kpi.triaged_count}</li>
          <li>{formatRate(payload.kpi.acceptance_rate)}</li>
          <li>
            Average latency:{" "}
            {payload.kpi.avg_latency_ms === null
              ? "no UI-event timings (TR-65: third metric missing)"
              : `${Math.round(payload.kpi.avg_latency_ms)} ms`}
          </li>
        </ul>
      ) : null}
    </section>
  );
}
