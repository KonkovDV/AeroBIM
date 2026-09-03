import { useEffect, useState } from "react";
import { fetchReviewKpi, type ReviewKpiPayload } from "../lib/api";
import { UI_COPY } from "../lib/ui-copy";

export type ReviewKpiPanelProps = {
  reportId: string | null;
};

function formatRate(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return UI_COPY.kpiNoDecisions;
  }
  return UI_COPY.kpiAcceptance(Math.round(value * 100));
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
          setError(err instanceof Error ? err.message : UI_COPY.kpiUnavailable);
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
          <p className="panel-kicker">{UI_COPY.kpiKicker}</p>
          <h2>{UI_COPY.kpiTitle}</h2>
        </div>
      </div>
      <p className="compact-copy">{UI_COPY.kpiBody}</p>
      {!reportId ? (
        <p className="panel-empty">{UI_COPY.kpiSelectReport}</p>
      ) : loading ? (
        <p className="compact-copy">{UI_COPY.kpiLoading}</p>
      ) : error ? (
        <p className="compact-copy">{error}</p>
      ) : payload ? (
        <ul className="kpi-list">
          <li>
            {UI_COPY.kpiEvents}: {payload.kpi.event_count}
          </li>
          <li>
            {UI_COPY.kpiOpened}: {payload.kpi.opened_count}
          </li>
          <li>
            {UI_COPY.kpiTriaged}: {payload.kpi.triaged_count}
          </li>
          <li>{formatRate(payload.kpi.acceptance_rate)}</li>
          <li>
            {UI_COPY.kpiAvgLatency}:{" "}
            {payload.kpi.avg_latency_ms === null
              ? UI_COPY.kpiNoTimings
              : `${Math.round(payload.kpi.avg_latency_ms)} мс`}
          </li>
        </ul>
      ) : null}
    </section>
  );
}
