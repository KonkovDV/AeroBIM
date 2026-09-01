import { useEffect, useState } from "react";
import { fetchReviewKpi, type ReviewKpiPayload } from "../lib/api";

export type ReviewKpiPanelProps = {
  reportId: string | null;
};

function formatRate(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "нет решений";
  }
  return `${Math.round(value * 100)} % подтверждённых среди принятых/отклонённых`;
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
          <p className="panel-kicker">Дашборд эффекта</p>
          <h2>review-kpi</h2>
        </div>
      </div>
      <p className="compact-copy">
        Журнал HITL, не точность продукта и не часы A1–A8. Пустой журнал — пустой экран, не «0 %
        ошибок». Checkpoint NO_GO.
      </p>
      {!reportId ? (
        <p className="panel-empty">Выберите отчёт в списке, затем откройте этот экран.</p>
      ) : loading ? (
        <p className="compact-copy">Загрузка KPI…</p>
      ) : error ? (
        <p className="compact-copy">{error}</p>
      ) : payload ? (
        <ul className="kpi-list">
          <li>Событий: {payload.kpi.event_count}</li>
          <li>Открыто: {payload.kpi.opened_count}</li>
          <li>Триаж: {payload.kpi.triaged_count}</li>
          <li>{formatRate(payload.kpi.acceptance_rate)}</li>
          <li>
            Средняя latency:{" "}
            {payload.kpi.avg_latency_ms === null
              ? "нет замеров UI-событий (ТР-65: третья метрика missing)"
              : `${Math.round(payload.kpi.avg_latency_ms)} мс`}
          </li>
        </ul>
      ) : null}
    </section>
  );
}
